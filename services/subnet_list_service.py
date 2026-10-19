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

"""有界 UTF-8 文件读取与可取消的后台清单检查。"""
from threading import Event
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from core.subnet_planning import free_space, aggregate_cidrs
from core.ipv6_core import InputError
from core.subnet_list import MAX_LIST_BYTES, validate_list_text, analyze_subnet_list, ListCheckCancelled


def load_subnet_list(path):
    with open(path, 'rb') as stream:
        data = stream.read(MAX_LIST_BYTES+1)
    if len(data)>MAX_LIST_BYTES:
        raise InputError('清单文件不能超过 1 MiB，请拆分后导入。')
    try:
        text = data.decode('utf-8-sig')
    except UnicodeError as exc:
        raise InputError('清单须为 UTF-8 文本（允许 BOM），请转换编码后重试。') from exc
    validate_list_text(text)
    return text


class _ListThread(QThread):
    def __init__(self, text, parent=None, *, task='relations', parent_network=''):
        super().__init__(parent)
        self.text = text
        self.task, self.parent_network = task, parent_network
        self.stop_event = Event()
        self.outcome = None

    def run(self):
        try:
            if self.task=='relations':
                result=analyze_subnet_list(self.text, stop=self.stop_event)
            elif self.task=='free':
                result=free_space(self.text,self.parent_network,stop=self.stop_event)
            elif self.task=='aggregate':
                result=aggregate_cidrs(self.text,stop=self.stop_event)
            else:
                raise InputError('未知的清单任务。')
            self.outcome = ('ok',result)
        except ListCheckCancelled:
            self.outcome = ('cancel', None)
        except Exception as exc:
            self.outcome = ('error', str(exc))


class SubnetListService(QObject):
    completed = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None

    @property
    def busy(self):
        return self._thread is not None

    def start(self, text, task='relations', parent_network=''):
        if self.busy:
            raise RuntimeError('清单检查正在进行。')
        thread = _ListThread(text, self, task=task, parent_network=parent_network)
        self._thread = thread
        thread.finished.connect(self._finish)
        try:
            thread.start()
            if not thread.isRunning() and not thread.isFinished():
                raise RuntimeError('无法启动检查线程，请稍后重试。')
        except Exception:
            self._thread = None
            thread.deleteLater()
            raise

    def cancel(self):
        if self._thread is not None:
            self._thread.stop_event.set()

    def _finish(self):
        thread = self._thread
        if thread is None:
            return
        outcome = ('cancel', None) if thread.stop_event.is_set() else (thread.outcome or ('error', '检查未返回结果。'))
        self._thread = None
        thread.deleteLater()
        self.completed.emit(outcome)
