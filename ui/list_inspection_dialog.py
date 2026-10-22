# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Read-only list snapshot inspection; shares existing conflict-safe text output."""
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from core.localized_text import text as tx
from core.ipv6_core import InputError
from core.list_inspection import lookup_address, compare_coverage
from services.language_service import display
from services.project_storage import load_project
from services.subnet_list_service import load_subnet_list
from services.error_messages import describe_error
from ui.standard_dialogs import QFileDialog
from ui.localized_widgets import QDialog, QLabel, QLineEdit, QPlainTextEdit, QTextBrowser, QTabWidget
from ui.widgets import IconButton
from ui.fonts import data_font


class InspectionPanel(QWidget):
    def __init__(self, page, source, comparison=False):
        super().__init__()
        self.page, self.source, self.comparison = page, source, comparison
        self.result = None
        layout = QVBoxLayout(self)
        hint = QLabel(tx('粘贴对比清单，或导入 TXT／规划项目 JSON。留空表示空清单。') if comparison
                      else tx('输入一个 IPv6 地址，查询基准清单中所有包含它的网段。'))
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.input = QPlainTextEdit() if comparison else QLineEdit()
        self.input.setFont(data_font())
        self.input.setAccessibleName(tx('对比清单') if comparison else tx('查询 IPv6 地址'))
        self.input.setPlaceholderText(tx('每行一个 IPv6 CIDR，允许空行和 # 注释') if comparison else '2001:db8::1')
        if comparison:
            self.input.setFixedHeight(100)
        layout.addWidget(self.input)
        row = QHBoxLayout()
        self.import_button = IconButton('open_plan', tx('导入对比 TXT 或规划项目 JSON'))
        self.import_button.setVisible(comparison)
        self.run_button = IconButton('check_list', tx('比较覆盖差异') if comparison else tx('查询地址归属'))
        self.copy_button = IconButton('copy', tx('复制查询或比较报告'))
        self.save_button = IconButton('save_plan', tx('保存查询或比较报告为 TXT'))
        for button in (self.import_button, self.run_button, self.copy_button, self.save_button):
            row.addWidget(button)
        row.addStretch()
        layout.addLayout(row)
        self.report = QTextBrowser()
        self.report.setFont(data_font())
        self.report.setOpenLinks(False)
        self.report.setAccessibleName(tx('查询或比较报告'))
        layout.addWidget(self.report, 1)
        self.input.textChanged.connect(self.invalidate)
        if not comparison:
            self.input.returnPressed.connect(self.run)
        self.import_button.clicked.connect(self.import_file)
        self.run_button.clicked.connect(self.run)
        self.copy_button.clicked.connect(self.copy)
        self.save_button.clicked.connect(self.save)
        self.invalidate()

    def invalidate(self):
        self.result = None
        self.report.setPlainText('')
        self.copy_button.setEnabled(False)
        self.save_button.setEnabled(False)

    def value(self):
        return self.input.toPlainText() if self.comparison else self.input.text()

    def run(self):
        self.invalidate()
        try:
            self.result = compare_coverage(self.source, self.value()) if self.comparison else lookup_address(self.source, self.value())
        except InputError as exc:
            self.report.setPlainText(tx('查询或比较失败：{0}', exc))
            return False
        self.report.setPlainText(self.result.as_text())
        self.copy_button.setEnabled(True)
        self.save_button.setEnabled(True)
        return True

    def import_file(self):
        before = self.value()
        path, _ = QFileDialog.getOpenFileName(self, tx('导入对比清单'), '',
                                             tx('清单或规划项目 (*.txt *.cidr *.json)'))
        if not path:
            return False
        try:
            text = load_project(path).text if Path(path).suffix.lower() == '.json' else load_subnet_list(path)
        except (OSError, InputError) as exc:
            self.invalidate()
            self.report.setPlainText(tx('导入对比清单失败：{0}', describe_error(exc)))
            return False
        if self.value() != before:
            return False
        self.input.setPlainText(text)
        return True

    def copy(self):
        if self.result is not None:
            self.page.clipboard.copy_text(self.result.as_text(), tx('报告已复制。'), self)

    def save(self):
        result = self.result
        if result is None:
            return
        self.page.output_controller._save('IPv6_CoverageComparison.txt' if self.comparison else 'IPv6_AddressMembership.txt',
            result.as_text(), lambda: self.result is result)


class ListInspectionDialog(QDialog):
    def __init__(self, page):
        super().__init__(page)
        self.setWindowTitle(tx('清单查询与覆盖比较'))
        self.resize(820, 640)
        self.setMinimumSize(600, 460)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        layout = QVBoxLayout(self)
        hint = QLabel(tx('基于打开窗口时的当前清单快照；关闭窗口后可修改原清单。'))
        hint.setWordWrap(True)
        layout.addWidget(hint)
        tabs = QTabWidget()
        source = page.editor.toPlainText()
        self.lookup = InspectionPanel(page, source)
        self.comparison = InspectionPanel(page, source, comparison=True)
        tabs.addTab(self.lookup, tx('地址归属查询'))
        tabs.addTab(self.comparison, tx('覆盖差异比较'))
        layout.addWidget(tabs)


def show_inspection(page):
    if page.service.busy:
        return
    dialog = ListInspectionDialog(page)
    dialog.exec()
