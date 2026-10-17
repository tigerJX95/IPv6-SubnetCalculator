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

"""结果表格的数据模型：只保存当前页，完整序号始终保留 Python 整数。"""
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication
from ui.fonts import data_font
from ui.theme import current_colors


class SubnetTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.records = []
        self.locator_range = None
        application = QApplication.instance()
        if application is not None and hasattr(application, 'theme_manager'):
            application.theme_manager.changed.connect(self._theme_changed)

    def _theme_changed(self, _name):
        if self.records:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self.records)-1, 1),
                                  [Qt.ItemDataRole.BackgroundRole])

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.records)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else 2

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self.records):
            return None
        number, subnet = self.records[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return str(number) if index.column() == 0 else subnet
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        if role == Qt.ItemDataRole.FontRole:
            return data_font()
        if role == Qt.ItemDataRole.BackgroundRole and self.locator_range:
            if self.locator_range[0] <= number <= self.locator_range[1]:
                return QColor(current_colors()['highlight'])
        if role == Qt.ItemDataRole.ToolTipRole:
            return f'子网序号：{number:,}\n{subnet}\n双击或按 Enter 查看详情。'
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return ('序号', 'IPv6 子网')[section] if section in (0, 1) else None
        return None

    def set_records(self, records, locator_range=None):
        self.beginResetModel()
        self.records = list(records)
        self.locator_range = locator_range
        self.endResetModel()

    def set_locator_range(self, span):
        self.locator_range = span
        if self.records:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self.records)-1, 1),
                                  [Qt.ItemDataRole.BackgroundRole])
