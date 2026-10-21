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

"""协调文件选择、导出确认和进度窗口；实际写文件交给导出服务。"""
from ui.localized_widgets import QDialog
from core.localized_text import text as tx, join_text as jt
import shutil
from core.file_commit import capture_file
from pathlib import Path
from ui.standard_dialogs import QFileDialog, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from core.subnet_export import XLSX_MAX_RECORDS
from core.export_estimate import estimate_export_range, format_size_range
from core.formatting import determine_export_format
from ui.dialogs import ExportRangeDialog, ExportProgressDialog


class ExportController(QObject):
    feedback = pyqtSignal(object, str)
    busy_changed = pyqtSignal(bool)

    def __init__(self, window, service):
        super().__init__(window)
        self.window, self.service = window, service
        self.progress_dialog = None
        service.progress.connect(self._progress)
        service.completed.connect(self._completed)

    def request_export(self, result):
        if result is None or self.service.busy:
            return
        selector = ExportRangeDialog(result.subnet_count, self.window)
        if selector.exec() != QDialog.DialogCode.Accepted:
            return
        start, end = selector.span
        count = end-start+1
        oversized = count > XLSX_MAX_RECORDS
        if oversized and not self._confirm(tx('超出 Excel 限制'),
                tx('本次选中的 {0:,} 个子网超过 Excel 单工作表最多 {1:,} 条的限制。\n\n如需继续保存选定范围，只能使用 TXT 格式。是否继续？', count, XLSX_MAX_RECORDS)):
            return
        filters = tx('文本文件 (*.txt)') if oversized else tx('Excel 工作簿 (*.xlsx);;文本文件 (*.txt)')
        default = 'txt' if oversized else 'xlsx'
        selected, selected_filter = QFileDialog.getSaveFileName(
            self.window, tx('导出 IPv6 子网'), tx('IPv6Subnets.{0}', default), filters,
            options=QFileDialog.Option.DontConfirmOverwrite)
        if not selected:
            return
        path = Path(selected)
        if not path.suffix:
            suffix = '.txt' if oversized or '*.txt' in selected_filter else '.xlsx'
            path = path.with_suffix(suffix)
        try:
            fmt = determine_export_format(path, oversized)
        except ValueError as exc:
            QMessageBox.warning(self.window, tx('格式错误'), str(exc))
            return
        lower, upper = estimate_export_range(result.network, result.target_prefix, fmt, count, start-1)
        disk_hint = format_size_range(lower, upper)
        if count > 100_000 and not self._confirm(tx('确认导出'),
                tx('将导出序号 {0:,}～{1:,}，共 {2:,} 个子网。\n预计占用磁盘空间约 {3}（范围估算）。\n实际大小取决于地址长度、压缩格式及文件内容。\n数据量较大，导出可能耗时较长。\n\n是否继续？', start, end, count, disk_hint)):
            return
        try:expected=capture_file(path)
        except (OSError,ValueError) as exc:
            from services.error_messages import describe_error
            QMessageBox.warning(self.window,tx('保存目标错误'),describe_error(exc));return
        if expected.exists and not self._confirm(tx('覆盖确认'), tx('文件已存在，是否覆盖？\n{0}', path)):
            return
        try:
            usage = shutil.disk_usage(path.parent)
            reserve = max(256*1024**2, usage.total//100)
            if upper+reserve > usage.free and not self._confirm(tx('磁盘空间提醒'),
                    tx('可用空间约 {0:.2f} GiB。\n预计文件大小约 {1}，另需预留安全空间。\n磁盘空间可能不足，是否仍尝试导出？', usage.free / 1024 ** 3, disk_hint)):
                return
        except OSError:
            pass
        self.start_export(path, fmt, result, start, end,expected=expected)

    def _confirm(self, title, text):
        return QMessageBox.question(self.window, title, text,
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes

    def start_export(self, path, fmt, result, start, end, *, expected=None):
        if self.service.busy:
            return
        dialog = ExportProgressDialog(Path(path).name, end-start+1, self.window)
        self.progress_dialog = dialog
        dialog.cancel_requested.connect(self.cancel)
        self.busy_changed.emit(True)
        self.feedback.emit(tx('正在导出子网…'), 'info')
        dialog.open()
        try:
            self.service.start(path, result, fmt, start, end,expected=expected)
        except Exception as exc:
            self._completed(('error', str(exc)))

    def _progress(self, done, total):
        if self.progress_dialog is not None:
            self.progress_dialog.set_progress(done, total)

    def cancel(self):
        self.service.cancel()
        if self.progress_dialog is not None:
            self.progress_dialog.request_cancel()

    def _completed(self, outcome):
        if self.progress_dialog is not None:
            self.progress_dialog.finish()
            self.progress_dialog.deleteLater()
            self.progress_dialog = None
        self.busy_changed.emit(False)
        kind, payload = outcome
        closing = self.window.closing_after_export
        if kind == 'ok':
            self.feedback.emit(tx('导出成功：共 {0:,} 项，保存至 {1}', payload.rows, payload.path), 'success')
            if not closing:
                QMessageBox.information(self.window, tx('导出完成'), tx('已导出 {0:,} 项。\n保存位置：{1}', payload.rows, payload.path))
        elif kind == 'cancel':
            self.feedback.emit(tx('导出已取消，未保留未完成文件。'), 'info')
        else:
            self.feedback.emit(tx('导出失败：')+str(payload), 'error')
            if not closing:
                QMessageBox.warning(self.window, tx('导出失败'), str(payload))
        if closing:
            QTimer.singleShot(0, self.window.close)
