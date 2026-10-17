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

"""统一 Qt 剪贴板访问及错误反馈。"""
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMessageBox


class ClipboardService(QObject):
    feedback = pyqtSignal(str, str)

    def copy_text(self, text, success_message, parent=None):
        try:
            clipboard = QApplication.clipboard()
            if clipboard is None:
                raise RuntimeError('Clipboard unavailable')
            clipboard.setText(text)
            if clipboard.text() != text:
                raise RuntimeError('Clipboard content not accepted')
        except (RuntimeError, OSError):
            message = '复制失败：暂时无法访问剪贴板，请稍后重试。'
            self.feedback.emit(message, 'error')
            QMessageBox.warning(parent, '复制失败', message)
            return False
        self.feedback.emit(success_message, 'success')
        return True
