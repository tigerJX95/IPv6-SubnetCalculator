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

"""将文件系统异常转换为中文；保留错误码和路径便于排查。"""
from core.localized_text import text as tx, exception_text
import errno


def describe_error(exc):
    if not isinstance(exc,OSError):
        return exception_text(exc)
    descriptions={errno.ENOENT:tx('找不到文件或目录，请检查路径。'),errno.EACCES:tx('没有访问权限，或文件正被其他程序占用。'),
        errno.EPERM:tx('当前操作不被允许，请检查访问权限。'),errno.ENOSPC:tx('磁盘空间不足，请清理空间后重试。'),
        errno.EROFS:tx('目标位置为只读，请选择可写目录。'),errno.EISDIR:tx('所选路径是文件夹，请选择文件。'),
        errno.ENOTDIR:tx('路径中的目录无效，请重新选择。'),errno.EEXIST:tx('文件或目录已存在。'),
        errno.EINVAL:tx('路径或文件名无效，请检查后重试。'),errno.ENAMETOOLONG:tx('路径或文件名过长。')}
    message=descriptions.get(exc.errno,tx('系统无法完成文件访问，请检查路径、权限或文件占用。'))
    if getattr(exc,'winerror',None) in (32,33):
        message=tx('文件正被其他程序占用，请关闭相关程序后重试。')
    if exc.filename:
        message+=tx('\n文件：')+str(exc.filename)
    code=getattr(exc,'winerror',None) or exc.errno
    if code is not None:
        message+=tx('（系统错误码：{0}）', code)
    return message
