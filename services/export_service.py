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

"""后台导出生命周期。工作线程不接触窗口，计数保持 Python 整数精度。"""
from core.localized_text import text as tx, join_text as jt
from threading import Event
from time import monotonic
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from services.error_messages import describe_error
from core.subnet_export import export_all, ExportCancelled


class _ExportThread(QThread):
    progress = pyqtSignal(object, object)

    def __init__(self, path, result, fmt, start, end, parent=None):
        super().__init__(parent)
        self.path, self.result, self.fmt = path, result, fmt
        self.start_index, self.end_index = start, end
        self.stop_event = Event()
        self.outcome = None
        self._last_progress = 0.0

    def report_progress(self, done, total):
        now = monotonic()
        if done == total or now - self._last_progress >= 0.1:
            self._last_progress = now
            self.progress.emit(done, total)

    def run(self):
        try:
            report = export_all(self.path, self.result.network, self.result.target_prefix, self.fmt,
                                start=self.start_index, end=self.end_index,
                                stop=self.stop_event, progress=self.report_progress)
            self.outcome = ('ok', report)
        except ExportCancelled:
            self.outcome = ('cancel', None)
        except Exception as exc:
            self.outcome = ('error', describe_error(exc))


class ExportService(QObject):
    progress = pyqtSignal(object, object)
    completed = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None

    @property
    def busy(self):
        # 即使 run 已返回，也等 GUI 线程处理 finished 后再允许启动新任务。
        return self._thread is not None

    def start(self, path, result, fmt, start, end):
        if self.busy:
            raise RuntimeError(tx('已有导出任务正在运行。'))
        thread = _ExportThread(path, result, fmt, start, end, self)
        self._thread = thread
        thread.progress.connect(self.progress)
        thread.finished.connect(self._finish)
        try:
            thread.start()
            # Qt may report OS thread creation failure without raising Python exceptions.
            if not thread.isRunning() and not thread.isFinished():
                raise RuntimeError(tx('无法启动导出线程，请稍后重试。'))
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
        outcome = thread.outcome or ('error', tx('导出线程未返回结果，请重试。'))
        self._thread = None
        thread.deleteLater()
        self.completed.emit(outcome)
