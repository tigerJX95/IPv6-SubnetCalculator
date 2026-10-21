# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
#
# This file is part of IPv6SubnetCalculator.
# IPv6SubnetCalculator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IPv6SubnetCalculator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with IPv6SubnetCalculator. If not, see <https://www.gnu.org/licenses/>.

"""文件版本快照、原子无覆盖新建及现有文件的乐观冲突检查。"""
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import errno
import hashlib
import os
import stat
import uuid
from core.ipv6_core import InputError
from core.localized_text import text as tx


@dataclass(frozen=True)
class FileSnapshot:
    path: Path
    version: tuple | None

    @property
    def exists(self):
        return self.version is not None


def _version(info):
    return (info.st_dev,info.st_ino,info.st_mode,info.st_size,info.st_mtime_ns,info.st_ctime_ns)


def capture_file(path):
    path=Path(path)
    path=path.parent.resolve(strict=True)/path.name
    try:
        info=path.lstat()
    except FileNotFoundError:
        return FileSnapshot(path,None)
    if not stat.S_ISREG(info.st_mode):
        raise InputError(tx('保存目标不是普通文件，请选择其他文件名。'))
    return FileSnapshot(path,_version(info))


class SaveConflict(InputError):
    def __init__(self,destination,recovery=None):
        self.destination=Path(destination)
        self.recovery=Path(recovery) if recovery is not None else None
        message=tx('目标文件已变化或正在由其他保存任务使用，已停止覆盖：{0}',self.destination)
        if recovery is not None:
            message+=tx('\n本次完整内容已保留在：{0}\n请检查目标文件，再选择其他文件名保存。',self.recovery)
        super().__init__(message)


@contextmanager
def _existing_lock(path):
    # Cooperating processes serialize commits. Unrelated applications are not
    # required to honor this lock; the final version check is optimistic.
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes
        api=ctypes.WinDLL('kernel32',use_last_error=True)
        api.CreateMutexW.argtypes=(ctypes.c_void_p,wintypes.BOOL,wintypes.LPCWSTR)
        api.CreateMutexW.restype=wintypes.HANDLE
        api.WaitForSingleObject.argtypes=(wintypes.HANDLE,wintypes.DWORD)
        api.WaitForSingleObject.restype=wintypes.DWORD
        api.ReleaseMutex.argtypes=(wintypes.HANDLE,)
        api.ReleaseMutex.restype=wintypes.BOOL
        api.CloseHandle.argtypes=(wintypes.HANDLE,)
        api.CloseHandle.restype=wintypes.BOOL
        identity=hashlib.sha256(os.path.normcase(str(path)).encode('utf-8')).hexdigest()
        handle=api.CreateMutexW(None,False,'Local\\IPv6Save_'+identity)
        if not handle:raise ctypes.WinError(ctypes.get_last_error())
        acquired=False
        try:
            status=api.WaitForSingleObject(handle,0)
            if status not in (0,0x80):
                if status==0xFFFFFFFF:raise ctypes.WinError(ctypes.get_last_error())
                raise SaveConflict(path)
            acquired=True
            yield
        finally:
            if acquired:api.ReleaseMutex(handle)
            api.CloseHandle(handle)
    else:
        import fcntl
        try:
            fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0))
        except (FileNotFoundError,IsADirectoryError):
            raise SaveConflict(path) from None
        except OSError as exc:
            if exc.errno==errno.ELOOP:raise SaveConflict(path) from None
            raise
        try:
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise SaveConflict(path) from None
            yield
        finally:
            os.close(fd)


def _publish_new(temporary,destination):
    if os.name=='nt':
        # Windows rename refuses an existing destination, atomically.
        os.rename(temporary,destination)
    else:
        # Hard-link publication is atomic and refuses an existing destination.
        # Filesystems without this operation fail safely; never fall back to replace.
        os.link(temporary,destination)
        os.unlink(temporary)


def _recover(temporary,destination):
    recovery=destination.parent/('IPv6-Recovered-'+uuid.uuid4().hex+destination.suffix)
    try:_publish_new(temporary,recovery)
    except OSError:return Path(temporary)
    return recovery


def commit_file(temporary,destination,expected):
    destination=Path(destination)
    if destination.parent.resolve(strict=True)/destination.name!=expected.path:
        raise InputError(tx('保存目标与确认的文件不一致，请重新选择。'))
    destination=expected.path
    try:
        if not expected.exists:
            try:_publish_new(temporary,destination)
            except OSError as exc:
                if exc.errno==errno.EEXIST or destination.exists() or destination.is_symlink():
                    raise SaveConflict(destination) from None
                raise
        else:
            with _existing_lock(destination):
                try:current=capture_file(destination)
                except InputError:raise SaveConflict(destination) from None
                if current!=expected:raise SaveConflict(destination)
                os.replace(temporary,destination)
    except SaveConflict:
        raise SaveConflict(destination,_recover(temporary,destination)) from None
