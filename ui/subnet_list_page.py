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

"""独立清单页：文本导入、后台检查、原行号校验及精确关系统计。"""
from pathlib import Path
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal
from PyQt6.QtGui import QColor, QKeySequence, QShortcut
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QTabWidget, QTableView, QHeaderView, QAbstractItemView, QFileDialog, QApplication)
from core.ipv6_core import InputError
from core.subnet_list import MAX_RELATION_DETAILS
from services.subnet_list_service import SubnetListService, load_subnet_list
from ui.fonts import data_font
from ui.theme import current_colors
from ui.widgets import IconButton
from ui.planning_views import PlanningViews


class ListTableModel(QAbstractTableModel):
    def __init__(self, headers, parent=None):
        super().__init__(parent)
        self.headers = headers
        self.rows = []
        self.errors = set()
        manager = getattr(QApplication.instance(), 'theme_manager', None)
        if manager is not None:
            manager.changed.connect(self._theme_changed)

    def _theme_changed(self, *_args):
        if self.rows:
            self.dataChanged.emit(self.index(0,0), self.index(len(self.rows)-1,len(self.headers)-1),
                                  [Qt.ItemDataRole.ForegroundRole])

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.headers)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section] if 0<=section<len(self.headers) else None
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0<=index.row()<len(self.rows) or not 0<=index.column()<len(self.headers):
            return None
        row = self.rows[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return str(row[index.column()])
        if role == Qt.ItemDataRole.ToolTipRole:
            return '\n'.join(f'{name}：{value}' for name,value in zip(self.headers,row))
        if role == Qt.ItemDataRole.FontRole:
            return data_font()
        if role == Qt.ItemDataRole.ForegroundRole and index.row() in self.errors:
            return QColor(current_colors()['error'])
        return None

    def set_rows(self, rows, errors=()):
        self.beginResetModel()
        self.rows, self.errors = list(rows), set(errors)
        self.endResetModel()


def _table(model):
    table = QTableView()
    table.setModel(model)
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setWordWrap(False)
    table.verticalHeader().hide()
    table.verticalHeader().setDefaultSectionSize(38)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    table.horizontalHeader().setStretchLastSection(True)
    table.setMinimumHeight(100)
    return table


class SubnetListPage(QWidget):
    feedback = pyqtSignal(str, str)
    busy_changed = pyqtSignal(bool)

    def __init__(self, clipboard, parent=None):
        super().__init__(parent)
        self.setObjectName('SubnetListPage')
        self.clipboard = clipboard
        self.analysis = None
        self._task = 'relations'
        self.service = SubnetListService(self)
        self.service.completed.connect(self._completed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12,12,12,12)
        layout.setSpacing(8)
        hint = QLabel('每行一个 IPv6 CIDR：校验与关系检查、父网段空闲空间、等价 CIDR 整理。')
        hint.setWordWrap(True)
        hint.setObjectName('Hint')
        layout.addWidget(hint)
        self.editor = QPlainTextEdit()
        self.editor.setFont(data_font())
        self.editor.setMinimumHeight(100)
        self.editor.setMaximumHeight(150)
        self.editor.setTabChangesFocus(True)
        self.editor.setPlaceholderText('2026:1015:abcd::/48\n2026:1015:abcd:1::/64\n# 空行和以 # 开头的注释会被忽略')
        self.editor.setToolTip('每行一个 CIDR；最多 5,000 条网段记录、1,048,576 字节（1 MiB），UTF-8（允许 BOM）。\nCtrl+Enter 检查；此清单不写入计算方案。')
        self.editor.setAccessibleName('待检查的 IPv6 CIDR 清单')
        self.editor.textChanged.connect(self._invalidate)
        layout.addWidget(self.editor)
        actions = QHBoxLayout()
        self.import_button = IconButton('open_plan', '导入 IPv6 CIDR 清单（UTF-8 TXT／CIDR，每行一个）')
        self.analyze_button = IconButton('check_list', '检查清单格式与网段关系（Ctrl+Enter）')
        self.copy_networks_button = IconButton('copy_page', '复制有效网段：规范化并去重，保留首次出现顺序；错误行不复制')
        self.copy_report_button = IconButton('copy', '复制检查报告（包含错误行、精确统计及有限关系明细）')
        self.cancel_button = IconButton('stop_small', '取消当前清单检查，保留输入文本')
        self.cancel_button.setVisible(False)
        for button in (self.import_button, self.analyze_button, self.copy_networks_button, self.copy_report_button, self.cancel_button):
            actions.addWidget(button)
        self.source_label = QLabel('粘贴或导入后检查；原始文件不会被修改。')
        self.source_label.setObjectName('Reference')
        self.source_label.setTextFormat(Qt.TextFormat.PlainText)
        self.source_label.setWordWrap(True)
        actions.addWidget(self.source_label,1)
        layout.addLayout(actions)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setTextFormat(Qt.TextFormat.PlainText)
        self.summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.summary)
        self.result_tabs = QTabWidget()
        self.record_model = ListTableModel(('原始行号','原始输入','规范化 CIDR','校验状态'),self)
        self.relation_model = ListTableModel(('前者行号','后者行号','关系'),self)
        self.records_table = _table(self.record_model)
        self.relations_table = _table(self.relation_model)
        for column,width in enumerate((95,255,255,260)):
            self.records_table.setColumnWidth(column,width)
        self.relations_table.setColumnWidth(0,130)
        self.relations_table.setColumnWidth(1,130)
        self.result_tabs.addTab(self.records_table,'校验记录')
        self.result_tabs.addTab(self.relations_table,'关系检查')
        self.planning = PlanningViews(self,ListTableModel,_table)
        self.result_tabs.currentChanged.connect(self._result_tab_changed)
        layout.addWidget(self.result_tabs,1)
        self.import_button.clicked.connect(self.import_file)
        self.analyze_button.clicked.connect(self.analyze)
        self.cancel_button.clicked.connect(self.cancel)
        self.copy_networks_button.clicked.connect(self.copy_networks)
        self.copy_report_button.clicked.connect(self.copy_report)
        self.shortcut = QShortcut(QKeySequence('Ctrl+Return'),self)
        self.shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut.activated.connect(self.analyze)
        self._invalidate()

    def _result_tab_changed(self, index):
        planning=index>=2
        self.summary.setVisible(not planning)
        self.editor.setMinimumHeight(70 if planning else 100)
        self.editor.setMaximumHeight(100 if planning else 150)

    def _invalidate(self):
        self.analysis = None
        self.planning.clear_all()
        self.record_model.set_rows([])
        self.relation_model.set_rows([])
        self.copy_networks_button.setEnabled(False)
        self.copy_report_button.setEnabled(False)
        self.summary.setText('清单可用于关系检查、空闲空间和 CIDR 整理；内容不写入计算方案。')
        self.source_label.setText('输入已修改，需重新检查；原始文件不会被修改。'
                                 if self.editor.toPlainText().strip() else '粘贴或导入后检查；原始文件不会被修改。')
        self.source_label.setToolTip('')

    def _busy(self, busy):
        self.editor.setReadOnly(busy)
        self.import_button.setEnabled(not busy)
        self.analyze_button.setEnabled(not busy)
        self.cancel_button.setVisible(busy)
        self.cancel_button.setEnabled(busy)
        self.planning.refresh_buttons()
        self.busy_changed.emit(busy)

    def import_file(self):
        if self.service.busy:
            return
        selected,_ = QFileDialog.getOpenFileName(self,'导入 IPv6 CIDR 清单','',
            'IPv6 CIDR 清单 (*.txt *.cidr);;所有文件 (*)')
        if not selected:
            return
        try:
            text = load_subnet_list(selected)
        except (OSError, InputError) as exc:
            self.feedback.emit('导入失败：'+str(exc),'error')
            return
        self.editor.setPlainText(text)
        self.source_label.setText('已导入：'+Path(selected).name)
        self.source_label.setToolTip(str(selected))
        self.analyze()

    def analyze(self):
        if self.service.busy:
            return
        self.result_tabs.setCurrentIndex(0)
        self._task = 'relations'
        source, tooltip = self.source_label.text(), self.source_label.toolTip()
        self._invalidate()
        if source.startswith('已导入'):
            self.source_label.setText(source)
            self.source_label.setToolTip(tooltip)
        try:
            self.service.start(self.editor.toPlainText())
        except Exception as exc:
            self.feedback.emit('无法开始检查：'+str(exc),'error')
            return
        self._busy(True)
        self.summary.setText('正在检查清单，可取消；不会修改计算方案或原始文件。')
        self.feedback.emit('正在后台检查 IPv6 清单…','info')

    def start_planning(self, task):
        if self.service.busy:
            return
        self.result_tabs.setCurrentIndex(2 if task=='free' else 3)
        self._task=task
        if task=='free':
            self.planning.clear_free()
        else:
            self.planning.clear_aggregate()
        try:
            self.service.start(self.editor.toPlainText(),task,self.planning.parent_input.text())
        except Exception as exc:
            self.feedback.emit('无法开始规划：'+str(exc),'error')
            return
        self.planning.status(task).setText('正在后台规划，可点击停止图标取消…')
        self._busy(True)
        self.feedback.emit('正在后台计算空闲空间…' if task=='free' else '正在后台整理 CIDR…','info')

    def cancel(self):
        self.service.cancel()
        self.cancel_button.setEnabled(False)
        if self._task=='relations':
            self.summary.setText('正在取消清单检查…')
        else:
            self.planning.status(self._task).setText('正在取消规划…')

    def _completed(self, outcome):
        if self._task!='relations':
            self.planning.completed(self._task,outcome)
            self._busy(False)
            return
        kind,value = outcome
        if kind=='ok':
            self.set_analysis(value)
            if self.source_label.text().startswith('输入已修改'):
                self.source_label.setText('当前输入已检查；原始文件不会被修改。')
            severity='error' if value.error_count else 'success'
            self.feedback.emit(f'清单检查完成：有效 {value.valid_count:,} 条，错误 {value.error_count:,} 行。',severity)
        else:
            self.summary.setText('检查已取消，输入文本已保留。' if kind=='cancel' else '检查失败：'+value)
            self.feedback.emit(self.summary.text(),'info' if kind=='cancel' else 'error')
        self._busy(False)

    def set_analysis(self, result):
        self.analysis = result
        first_seen = {}
        rows = []
        errors = []
        for index,record in enumerate(result.records):
            if record.error:
                status = record.error
                errors.append(index)
            else:
                first = first_seen.setdefault(record.network,record.line)
                status = ('主机位已规范化' if record.normalized else '有效')
                if first!=record.line:
                    status += f'；重复（首见第 {first} 行）'
            rows.append((record.line,record.original,str(record.network) if record.network else '—',status))
        self.record_model.set_rows(rows,errors)
        self.relation_model.set_rows((item.first,item.second,item.description) for item in result.relations)
        self.summary.setText(f'有效 {result.valid_count:,} 条｜错误 {result.error_count:,} 行｜去重后 {len(result.unique_networks):,} 条\n'
            f'重复 {result.duplicate_pairs:,} 对｜包含 {result.containment_pairs:,} 对｜相邻 {result.adjacent_pairs:,} 对；'
            f'明细 {len(result.relations):,}/{result.relation_count:,} 对（最多 {MAX_RELATION_DETAILS:,} 对）。'
            + ('\n存在错误行：以下关系仅基于有效网段，不代表整份清单通过。' if result.error_count else ''))
        self.copy_networks_button.setEnabled(bool(result.unique_networks))
        self.copy_report_button.setEnabled(True)

    def copy_networks(self):
        if self.analysis is not None and self.analysis.unique_networks:
            result=self.analysis
            self.clipboard.copy_text(result.normalized_text(),
                f'已复制 {len(result.unique_networks):,} 条有效去重网段；跳过错误 {result.error_count:,} 行。',self)

    def copy_report(self):
        if self.analysis is not None:
            self.clipboard.copy_text(self.analysis.as_text(),'清单检查报告已复制；统计精确，明细数量见报告。',self)
