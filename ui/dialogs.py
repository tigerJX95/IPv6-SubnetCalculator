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

"""详情、范围复制、导出范围及导出进度窗口。"""
from ui.standard_dialogs import QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QRadioButton, QProgressBar)
from core.ipv6_core import InputError, validate_subnet_index, subnet_at_index
from core.subnet_tools import (MAX_COPY_RECORDS, validate_copy_range, subnet_range_text,
                                adjacent_subnet_index)
from ui.widgets import IconButton, value_label, FeedbackLabel
from ui.input_feedback import bind_input, mark_invalid, clear_invalid


class AppDialog(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(470)

    def showEvent(self, event):
        super().showEvent(event)
        if self.parentWidget():
            area = self.screen().availableGeometry()
            center = self.parentWidget().window().frameGeometry().center()
            x = max(area.left(), min(center.x()-self.width()//2, area.right()-self.width()+1))
            y = max(area.top(), min(center.y()-self.height()//2, area.bottom()-self.height()+1))
            self.move(x, y)


class RangeCopyDialog(AppDialog):
    def __init__(self, result, clipboard, suggested=None, parent=None):
        super().__init__('按序号范围复制子网', parent)
        self.subnet_result, self.clipboard = result, clipboard
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 16)
        layout.setSpacing(14)
        title = QLabel(f'选择需要复制的子网序号（最多 {MAX_COPY_RECORDS:,} 条）')
        title.setWordWrap(True)
        layout.addWidget(title)
        first, last = suggested or (1, min(100, result.subnet_count))
        self.start_input = QLineEdit(str(first))
        self.end_input = QLineEdit(str(last))
        for field in (self.start_input, self.end_input):
            bind_input(field)
            field.setMaxLength(42)
            field.returnPressed.connect(self.perform)
        form = QFormLayout()
        form.setSpacing(12)
        form.addRow('起始序号：', self.start_input)
        form.addRow('结束序号（包含）：', self.end_input)
        layout.addLayout(form)
        self.input_feedback=FeedbackLabel()
        self.input_feedback.clear()
        self.input_feedback.hide()
        layout.addWidget(self.input_feedback)
        actions = QHBoxLayout()
        actions.addStretch()
        self.copy_button = IconButton('copy', '复制指定范围（Enter）')
        self.copy_button.clicked.connect(self.perform)
        close = IconButton('close_small', '取消并关闭（Esc）')
        close.clicked.connect(self.reject)
        actions.addWidget(self.copy_button)
        actions.addWidget(close)
        layout.addLayout(actions)

    def perform(self):
        for field in (self.start_input,self.end_input):clear_invalid(field)
        try:
            first, last = validate_copy_range(self.start_input.text(), self.end_input.text(), self.subnet_result.subnet_count)
            text = subnet_range_text(self.subnet_result.network, self.subnet_result.target_prefix, first, last)
        except InputError as exc:
            for field in (self.start_input,self.end_input):mark_invalid(field,str(exc))
            self.input_feedback.set_message(str(exc),'error')
            self.input_feedback.show()
            QMessageBox.warning(self, '无法复制', str(exc))
            return
        if self.clipboard.copy_text(text,
                f'已复制第 {first:,}～{last:,} 项，共 {last-first+1:,} 个子网。', self):
            self.accept()


class SubnetDetailDialog(AppDialog):
    index_changed = pyqtSignal(object)

    def __init__(self, result, index, clipboard, parent=None):
        super().__init__('IPv6 子网详情', parent)
        self.subnet_result, self.current_index, self.clipboard = result, index, clipboard
        self.resize(760, 350)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 16)
        form = QFormLayout()
        form.setSpacing(13)
        self.values = {}
        for name in ('子网序号', 'IPv6 子网', '起始地址', '结束地址', '地址数量'):
            self.values[name] = value_label()
            form.addRow(name+'：', self.values[name])
        layout.addLayout(form)
        actions = QHBoxLayout()
        self.previous_button = IconButton('previous_small', '上一个子网')
        self.next_button = IconButton('next_small', '下一个子网')
        self.previous_button.clicked.connect(lambda: self.step(-1))
        self.next_button.clicked.connect(lambda: self.step(1))
        actions.addWidget(self.previous_button)
        actions.addWidget(self.next_button)
        actions.addStretch()
        self.copy_button = IconButton('copy', '复制完整子网详情')
        self.copy_button.clicked.connect(self.copy_details)
        close = IconButton('close_small', '关闭详情（Esc）')
        close.clicked.connect(self.accept)
        actions.addWidget(self.copy_button)
        actions.addWidget(close)
        layout.addLayout(actions)
        self._update_values()

    def _update_values(self):
        subnet = subnet_at_index(self.subnet_result.network, self.subnet_result.target_prefix, self.current_index)
        data = (f'{self.current_index:,}', str(subnet), str(subnet.network_address),
                str(subnet.broadcast_address), f'{subnet.num_addresses:,}')
        for label, text in zip(self.values.values(), data):
            label.setText(text)
        self.previous_button.setEnabled(self.current_index > 1)
        self.next_button.setEnabled(self.current_index < self.subnet_result.subnet_count)

    def step(self, direction):
        self.current_index = adjacent_subnet_index(self.current_index, self.subnet_result.subnet_count, direction)
        self._update_values()
        self.index_changed.emit(self.current_index)

    def copy_details(self):
        self.clipboard.copy_text('\n'.join(f'{name}：{label.text()}' for name, label in self.values.items()),
                                 '子网详细信息已复制到剪贴板。', self)


class ExportRangeDialog(AppDialog):
    def __init__(self, total, parent=None):
        super().__init__('选择子网导出范围', parent)
        self.total, self.span = total, None
        self.resize(640, 320)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 16)
        layout.setSpacing(12)
        summary = QLabel(f'本次计算共有 {total:,} 个子网。')
        summary.setWordWrap(True)
        layout.addWidget(summary)
        self.all_radio = QRadioButton('导出全部子网')
        self.range_radio = QRadioButton('按序号范围导出（包含起止项）')
        self.all_radio.setChecked(True)
        layout.addWidget(self.all_radio)
        layout.addWidget(self.range_radio)
        form = QFormLayout()
        self.start_input = QLineEdit('1')
        self.end_input = QLineEdit(str(min(total, 1000)))
        for field in (self.start_input, self.end_input):
            field.setEnabled(False)
            bind_input(field)
            field.setMaxLength(42)
            field.returnPressed.connect(self.confirm)
        self.start_input.setToolTip('输入子网序号，最小为 1。')
        self.end_input.setToolTip(f'最大为 {total:,}，包含此项。')
        form.addRow('起始序号：', self.start_input)
        form.addRow('结束序号：', self.end_input)
        layout.addLayout(form)
        self.input_feedback=FeedbackLabel()
        self.input_feedback.clear()
        self.input_feedback.hide()
        layout.addWidget(self.input_feedback)
        self.range_radio.toggled.connect(self.start_input.setEnabled)
        self.range_radio.toggled.connect(self.end_input.setEnabled)
        actions = QHBoxLayout()
        actions.addStretch()
        self.confirm_button = IconButton('confirm_small', '确认导出范围（Enter）')
        self.confirm_button.clicked.connect(self.confirm)
        cancel = IconButton('close_small', '取消（Esc）')
        cancel.clicked.connect(self.reject)
        actions.addWidget(self.confirm_button)
        actions.addWidget(cancel)
        layout.addLayout(actions)

    def confirm(self):
        for field in (self.start_input,self.end_input):clear_invalid(field)
        try:
            if self.all_radio.isChecked():
                span = (1, self.total)
            else:
                first = validate_subnet_index(self.start_input.text(), self.total)
                last = validate_subnet_index(self.end_input.text(), self.total)
                if last < first:
                    raise InputError('结束序号不能小于起始序号。')
                span = (first, last)
        except InputError as exc:
            for field in (self.start_input,self.end_input):mark_invalid(field,str(exc))
            self.input_feedback.set_message(str(exc),'error')
            self.input_feedback.show()
            QMessageBox.warning(self, '导出范围错误', str(exc))
            return
        self.span = span
        self.accept()


class ExportProgressDialog(AppDialog):
    cancel_requested = pyqtSignal()

    def __init__(self, filename, total, parent=None):
        super().__init__('正在导出子网', parent)
        self._active, self._cancelling = True, False
        self.resize(620, 250)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 16)
        layout.setSpacing(14)
        destination = QLabel('正在导出至：'+filename)
        destination.setTextFormat(Qt.TextFormat.PlainText)
        destination.setWordWrap(True)
        layout.addWidget(destination)
        self.count_label = QLabel(f'0 / {total:,} 项（0.00%）')
        self.count_label.setWordWrap(True)
        layout.addWidget(self.count_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 10000)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)
        actions = QHBoxLayout()
        actions.addStretch()
        self.cancel_button = IconButton('stop_small', '取消导出并清理未完成文件（Esc）')
        self.cancel_button.clicked.connect(self.request_cancel)
        actions.addWidget(self.cancel_button)
        layout.addLayout(actions)

    def set_progress(self, done, total):
        self.progress_bar.setValue(done * 10000 // total)
        if not self._cancelling:
            self.count_label.setText(f'{done:,} / {total:,} 项（{done*100/total:.2f}%）')

    def request_cancel(self):
        if self._active and not self._cancelling:
            self._cancelling = True
            self.cancel_button.setEnabled(False)
            self.count_label.setText('正在取消并清理临时文件，请稍候…')
            self.cancel_requested.emit()

    def finish(self):
        self._active = False
        self.accept()

    def reject(self):
        if self._active:
            self.request_cancel()
        else:
            super().reject()

    def closeEvent(self, event):
        if self._active:
            self.request_cancel()
            event.ignore()
        else:
            super().closeEvent(event)
