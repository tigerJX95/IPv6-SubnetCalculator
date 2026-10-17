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

"""结果页负责表格、分页、定位与选择；导出任务由外部协调。"""
from PyQt6.QtCore import Qt, pyqtSignal, QItemSelectionModel
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableView,
                             QAbstractItemView, QHeaderView, QLineEdit, QComboBox, QMessageBox)
from core.ipv6_core import InputError
from core.subnet_export import page_subnets
from core.subnet_tools import LOCATOR_MODES, resolve_locator_range, summarize_selection, MAX_COPY_RECORDS
from core.formatting import compact_count
from ui.widgets import IconButton, ClickableLabel
from ui.subnet_model import SubnetTableModel
from ui.dialogs import RangeCopyDialog, SubnetDetailDialog


class ResultsPage(QWidget):
    feedback = pyqtSignal(str, str)
    export_requested = pyqtSignal()

    def __init__(self, clipboard, parent=None):
        super().__init__(parent)
        self.setObjectName('ResultsPage')
        self.clipboard = clipboard
        self.result = None
        self.page = 1
        self.locator_range = None
        self._updating = False
        self._export_enabled = True
        self._selection_stats_full = ''
        self._page_stats_full = ''
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(9)

        tools = QHBoxLayout()
        tools.setSpacing(10)
        self.copy_selected_button = IconButton('copy', '复制选中子网（Ctrl+C）\n按序号顺序复制本页选择。')
        self.copy_page_button = IconButton('copy_page', '复制本页全部子网\n无需先选中记录。')
        self.copy_range_button = IconButton('copy_range', f'按序号范围复制子网\n单次最多 {MAX_COPY_RECORDS:,} 条。')
        self.clear_selection_button = IconButton('clear_selection', '清除选择（Esc）\n保留定位范围高亮。')
        self.export_button = IconButton('export', '导出全部子网或指定范围（TXT / Excel）\nExcel 最多 1,048,575 条，超出可使用 TXT。')
        for widget in (self.copy_selected_button, self.copy_page_button, self.copy_range_button,
                       self.clear_selection_button):
            tools.addWidget(widget)
        tools.addStretch()
        tools.addWidget(self.export_button)
        layout.addLayout(tools)

        self.selection_label = ClickableLabel('本页选中 0 条 · 地址总量 0')
        self.selection_label.setObjectName('Hint')
        self.selection_label.setToolTip('点击复制完整精确统计。')
        self.selection_label.clicked.connect(self.copy_selection_statistics)
        self.range_label = QLabel('定位范围：未设置')
        self.range_label.setObjectName('Hint')
        self.range_label.setWordWrap(True)
        layout.addWidget(self.selection_label)
        layout.addWidget(self.range_label)

        self.model = SubnetTableModel(self)
        self.table = QTableView()
        self.table.setObjectName('subnet_table')
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 130)
        self.table.setMinimumHeight(150)
        self.table.setToolTip('Ctrl+单击多选，Shift+单击连续选择；Ctrl+A 全选本页，Ctrl+C 复制，Esc 清除选择。\n双击或按 Enter 查看子网详情。')
        layout.addWidget(self.table, 1)
        self.table.selectionModel().selectionChanged.connect(self.refresh_statistics)
        self.table.doubleClicked.connect(self.show_detail)

        paging = QHBoxLayout()
        paging.setSpacing(7)
        self.first_button = IconButton('first_small', '首页')
        self.previous_button = IconButton('previous_small', '上一页')
        self.next_button = IconButton('next_small', '下一页')
        self.last_button = IconButton('last_small', '末页')
        for widget in (self.first_button, self.previous_button, self.next_button, self.last_button):
            paging.addWidget(widget)
        paging.addSpacing(9)
        paging.addWidget(QLabel('页码：'))
        self.page_input = QLineEdit('1')
        self.page_input.setMaxLength(42)
        self.page_input.setMinimumWidth(90)
        self.page_input.setMaximumWidth(220)
        self.page_input.setToolTip('输入完整页码后按 Enter；支持巨大 IPv6 结果集。')
        paging.addWidget(self.page_input, 1)
        self.jump_button = IconButton('jump_small', '跳转到指定页码（Enter）')
        paging.addWidget(self.jump_button)
        paging.addStretch()
        paging.addWidget(QLabel('每页：'))
        self.page_size_combo = QComboBox()
        for size in (25, 50, 100, 200):
            self.page_size_combo.addItem(str(size), size)
        self.page_size_combo.setCurrentIndex(2)
        self.page_size_combo.setMinimumWidth(78)
        self.page_size_combo.setToolTip('修改每页条数时，保留原页首子网所在位置。')
        paging.addWidget(self.page_size_combo)
        layout.addLayout(paging)
        self.page_label = ClickableLabel('暂无计算结果')
        self.page_label.setObjectName('Hint')
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.page_label.clicked.connect(self.copy_page_statistics)
        layout.addWidget(self.page_label)

        locator = QHBoxLayout()
        locator.setSpacing(8)
        locator.addWidget(QLabel('定位方式：'))
        self.locator_mode_combo = QComboBox()
        self.locator_mode_combo.addItems(LOCATOR_MODES)
        self.locator_mode_combo.setMinimumWidth(175)
        self.locator_mode_combo.setToolTip('按 IPv6 地址、序号或对应范围定位。')
        locator.addWidget(self.locator_mode_combo)
        self.locator_input = QLineEdit()
        self.locator_input.setMaxLength(250)
        locator.addWidget(self.locator_input, 1)
        self.locator_button = IconButton('locate_small', '定位（Enter）\n范围高亮跨页保留，定位时只选中首条。')
        self.clear_range_button = IconButton('clear_highlight_small', '清除定位高亮\n保留本页手动选择。')
        locator.addWidget(self.locator_button)
        locator.addWidget(self.clear_range_button)
        layout.addLayout(locator)

        self.copy_selected_button.clicked.connect(self.copy_selected)
        self.copy_page_button.clicked.connect(self.copy_page)
        self.copy_range_button.clicked.connect(self.copy_range)
        self.clear_selection_button.clicked.connect(self.clear_selection)
        self.export_button.clicked.connect(self.export_requested)
        self.first_button.clicked.connect(lambda: self.show_page(1))
        self.previous_button.clicked.connect(lambda: self.show_page(self.page-1))
        self.next_button.clicked.connect(lambda: self.show_page(self.page+1))
        self.last_button.clicked.connect(lambda: self.show_page(self.total_pages))
        self.page_input.returnPressed.connect(self.jump)
        self.jump_button.clicked.connect(self.jump)
        self.page_size_combo.currentIndexChanged.connect(self.change_page_size)
        self.locator_mode_combo.currentIndexChanged.connect(self.locator_mode_changed)
        self.locator_input.returnPressed.connect(self.locate)
        self.locator_input.editingFinished.connect(self.normalize_locator)
        self.locator_button.clicked.connect(self.locate)
        self.clear_range_button.clicked.connect(self.clear_locator_range)

        for sequence, callback in ((QKeySequence.StandardKey.Copy, self.copy_selected),
                                    ('Escape', self.clear_selection), ('Return', self.show_detail)):
            shortcut = QShortcut(QKeySequence(sequence), self.table)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(callback)
        self.locator_mode_changed()
        self.set_result(None)

    @property
    def page_size(self):
        return self.page_size_combo.currentData()

    @property
    def total_pages(self):
        return (self.result.subnet_count+self.page_size-1)//self.page_size if self.result else 0

    def set_result(self, result):
        self.result, self.page, self.locator_range = result, 1, None
        if result:
            self.show_page(1)
        else:
            self._updating = True
            self.model.set_records([])
            self._updating = False
            self.page_input.setText('1')
            self.page_label.setText('暂无计算结果')
            self.page_label.setToolTip('计算后可查看并复制完整分页统计。')
            self._page_stats_full = ''
            self.refresh_statistics()
            self.update_actions()

    def set_export_enabled(self, enabled):
        self._export_enabled = enabled
        self.update_actions()

    def update_actions(self):
        exists = self.result is not None
        for widget in (self.copy_page_button, self.copy_range_button, self.jump_button, self.page_input,
                       self.page_size_combo, self.locator_mode_combo, self.locator_input, self.locator_button):
            widget.setEnabled(exists)
        self.first_button.setEnabled(exists and self.page > 1)
        self.previous_button.setEnabled(exists and self.page > 1)
        self.next_button.setEnabled(exists and self.page < self.total_pages)
        self.last_button.setEnabled(exists and self.page < self.total_pages)
        self.export_button.setEnabled(exists and self._export_enabled)
        selected = bool(self.selected_rows())
        self.copy_selected_button.setEnabled(selected)
        self.clear_selection_button.setEnabled(selected)
        self.clear_range_button.setEnabled(self.locator_range is not None)

    def selected_rows(self):
        return sorted(index.row() for index in self.table.selectionModel().selectedRows())

    def selected_indices(self):
        return [self.model.records[row][0] for row in self.selected_rows()]

    def refresh_statistics(self, *_):
        if self._updating:
            return
        selected = self.selected_indices()
        stats = summarize_selection(selected, (record[0] for record in self.model.records),
                                    self.result.addresses_per_subnet if self.result else 0, self.locator_range)
        span = ''
        if stats.count:
            span = (f' · 序号 {compact_count(stats.first)}' if stats.count == 1 else
                    f' · 序号 {compact_count(stats.first)}～{compact_count(stats.last)}'
                    f'（{"连续" if stats.contiguous else "非连续"}）')
        self.selection_label.setText(f'本页选中 {stats.count:,} 条{span} · 地址总量 {compact_count(stats.address_count)}')
        self._selection_stats_full = f'本页选中子网数：{stats.count:,}\n'
        if stats.count:
            self._selection_stats_full += (f'首个选中序号：{stats.first:,}\n末个选中序号：{stats.last:,}\n'
                                           f'选择连续性：{"连续" if stats.contiguous else "非连续"}\n')
        self._selection_stats_full += f'选中子网地址总量：{stats.address_count:,}'
        self.selection_label.setToolTip(self._selection_stats_full+'\n点击复制以上数据。')
        self.range_label.setText(
            f'定位范围：共 {compact_count(stats.highlighted_total)} 条 · 本页高亮 {stats.highlighted_on_page:,} 条'
            if self.locator_range else '定位范围：未设置')
        self.range_label.setToolTip(
            f'定位序号：{self.locator_range[0]:,}～{self.locator_range[1]:,}\n'
            f'范围总数：{stats.highlighted_total:,}\n本页高亮：{stats.highlighted_on_page:,}'
            if self.locator_range else '高亮与手动选择分别统计。')
        self.update_actions()

    def show_page(self, page):
        if not self.result or not 1 <= page <= self.total_pages:
            return
        self.page = page
        self._updating = True
        self.model.set_records(page_subnets(self.result.network, self.result.target_prefix, page, self.page_size),
                               self.locator_range)
        self._updating = False
        self.page_input.setText(str(page))
        self.page_label.setText(f'第 {compact_count(page)} / {compact_count(self.total_pages)} 页 · 共 {compact_count(self.result.subnet_count)} 项')
        self._page_stats_full = f'子网总数：{self.result.subnet_count:,}\n当前页码：{page:,}\n总页数：{self.total_pages:,}'
        self.page_label.setToolTip(self._page_stats_full+'\n点击复制完整统计。')
        # 极大序号可手工拖宽或横向滚动，显示和复制均保留完整整数。
        width = min(410, max(115, len(str(self.model.records[-1][0]))*9+30))
        self.table.setColumnWidth(0, width)
        self.refresh_statistics()

    def change_page_size(self, *_):
        if not self.result or not self.model.records:
            return
        anchor = self.model.records[0][0]
        self.show_page((anchor-1)//self.page_size+1)
        for row, (number, _) in enumerate(self.model.records):
            if number == anchor:
                index = self.model.index(row, 0)
                self.table.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectionFlag.NoUpdate)
                self.table.scrollTo(index)
                break

    def jump(self):
        if not self.result:
            return
        text = self.page_input.text().strip()
        if not text.isascii() or not text.isdecimal() or len(text) > 42 or not 1 <= int(text) <= self.total_pages:
            QMessageBox.warning(self, '页码错误', f'请输入 1 至 {self.total_pages:,} 之间的页码。')
            self.page_input.setText(str(self.page))
            return
        self.show_page(int(text))

    def normalize_locator(self):
        if self.locator_mode_combo.currentText() in (LOCATOR_MODES[0], LOCATOR_MODES[2]):
            self.locator_input.setText(self.locator_input.text().lower())

    def locator_mode_changed(self, *_):
        hints = ('例如：2026:1015:abcd::1', '例如：30（序号从 1 开始）',
                 '例如：2026:1015:abcd::1 - 2026:1015:abcd:2::1', '例如：1000-1500（包含起止序号）')
        self.locator_input.clear()
        hint = hints[max(0, self.locator_mode_combo.currentIndex())]
        self.locator_input.setPlaceholderText(hint)
        self.locator_input.setToolTip(hint)
        self.clear_locator_range()

    def locate(self):
        if not self.result:
            return
        self.normalize_locator()
        try:
            first, last = resolve_locator_range(self.locator_mode_combo.currentText(), self.locator_input.text(),
                                                self.result.network, self.result.target_prefix)
        except InputError as exc:
            self.feedback.emit('定位失败：'+str(exc), 'error')
            QMessageBox.warning(self, '定位失败', str(exc))
            return
        self.locator_range = (first, last)
        self.select_index(first)
        self.feedback.emit(f'定位成功：第 {first:,} 个子网。' if first == last else
                           f'已定位第 {first:,}～{last:,} 个子网，共 {last-first+1:,} 项；翻页仍保留范围高亮。', 'success')

    def select_index(self, index):
        self.show_page((index-1)//self.page_size+1)
        for row, (number, _) in enumerate(self.model.records):
            if number == index:
                item = self.model.index(row, 0)
                selection = self.table.selectionModel()
                selection.setCurrentIndex(item, QItemSelectionModel.SelectionFlag.NoUpdate)
                selection.select(item, QItemSelectionModel.SelectionFlag.ClearAndSelect |
                                 QItemSelectionModel.SelectionFlag.Rows)
                self.table.scrollTo(item)
                self.table.setFocus()
                break
        self.refresh_statistics()

    def clear_selection(self):
        had_selection = bool(self.selected_rows())
        self.table.clearSelection()
        self.refresh_statistics()
        if had_selection:
            self.feedback.emit('已清除本页手动选择；定位范围高亮已保留。' if self.locator_range
                               else '已清除本页手动选择。', 'info')

    def clear_locator_range(self):
        had_range = self.locator_range is not None
        self.locator_range = None
        self.model.set_locator_range(None)
        self.refresh_statistics()
        if had_range:
            self.feedback.emit('已清除定位范围高亮；本页手动选择已保留。', 'info')

    def copy_selected(self):
        rows = self.selected_rows()
        if rows:
            self.clipboard.copy_text('\n'.join(self.model.records[row][1] for row in rows),
                                     f'已复制 {len(rows)} 个子网。', self)

    def copy_page(self):
        if self.result:
            self.clipboard.copy_text('\n'.join(record[1] for record in self.model.records),
                                     f'已复制 {len(self.model.records)} 个子网。', self)

    def copy_selection_statistics(self):
        if self.result:
            self.clipboard.copy_text(self._selection_stats_full, '完整选择统计已复制到剪贴板。', self)

    def copy_page_statistics(self):
        if self.result:
            self.clipboard.copy_text(self._page_stats_full, '完整分页统计已复制到剪贴板。', self)

    def copy_range(self):
        if self.result:
            dialog = RangeCopyDialog(self.result, self.clipboard, self.locator_range, self)
            dialog.exec()

    def show_detail(self, index=None):
        if not self.result:
            return
        if index is not None and index.isValid():
            row = index.row()
        else:
            rows = self.selected_rows()
            if not rows:
                return
            current = self.table.currentIndex()
            row = current.row() if current.isValid() and current.row() in rows else rows[0]
        dialog = SubnetDetailDialog(self.result, self.model.records[row][0], self.clipboard, self)
        dialog.index_changed.connect(self.select_index)
        dialog.exec()
