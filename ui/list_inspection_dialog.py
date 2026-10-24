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
from ui.localized_widgets import QDialog, QLabel, QLineEdit, QPlainTextEdit, QTextBrowser, QTabWidget, QComboBox
from ui.widgets import IconButton
from ui.fonts import data_font


class InspectionPanel(QWidget):
    def __init__(self, page, source, comparison=False):
        super().__init__()
        self.page, self.source, self.comparison = page, source, comparison
        self.result = None
        layout = QVBoxLayout(self)
        hint = self.hint = QLabel(tx('粘贴对比清单，或导入 TXT／规划项目 JSON。留空表示空清单。') if comparison
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
        output_row = QHBoxLayout()
        self.category = QComboBox()
        self.category.setAccessibleName(tx('输出 CIDR 类别'))
        if comparison:
            for label, key in [(tx('新增覆盖 CIDR'), 'added'), (tx('移除覆盖 CIDR'), 'removed'),
                               (tx('共同覆盖 CIDR'), 'common')]:
                self.category.addItem(label, key)
        else:
            self.category.addItem(tx('匹配网段 CIDR（去重，保留包含项）'), 'matches')
        output_row.addWidget(self.category, 1)
        self.copy_cidrs_button = IconButton('copy', tx('复制完整 CIDR 清单'))
        self.save_cidrs_button = IconButton('save_plan', tx('保存完整 CIDR 清单为 TXT'))
        output_row.addWidget(self.copy_cidrs_button)
        output_row.addWidget(self.save_cidrs_button)
        layout.addLayout(output_row)
        self.cidr_status = QLabel('')
        self.cidr_status.setWordWrap(True)
        layout.addWidget(self.cidr_status)
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
        self.category.currentIndexChanged.connect(self.refresh_cidrs)
        self.copy_cidrs_button.clicked.connect(self.copy_cidrs)
        self.save_cidrs_button.clicked.connect(self.save_cidrs)
        self.invalidate()

    def invalidate(self):
        self.result = None
        self.report.setPlainText('')
        self.copy_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.refresh_cidrs()

    def refresh_cidrs(self):
        self.cidr_output = None
        if self.result is not None:
            self.cidr_output = (self.result.cidr_output(self.category.currentData()) if self.comparison
                                else self.result.cidr_output())
        output = self.cidr_output
        available = output is not None and output.complete and bool(output.count)
        self.copy_cidrs_button.setEnabled(available)
        self.save_cidrs_button.setEnabled(available)
        if output is None:
            self.cidr_status.setText('')
        elif not output.complete:
            self.cidr_status.setText(tx('共 {0:,} 条 CIDR，超过 5,000 条；请保存完整范围报告。', output.count))
        elif not output.count:
            self.cidr_status.setText(tx('所选结果为空，没有可输出的 CIDR。'))
        else:
            self.cidr_status.setText(tx('完整 CIDR：{0:,} 条，可复制或保存后重新导入清单。', output.count))

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
        self.refresh_cidrs()
        return True

    def copy_cidrs(self):
        output = self.cidr_output
        if output is not None and output.complete and output.count:
            self.page.clipboard.copy_text(output.as_text(), tx('CIDR 清单已复制。'), self)

    def save_cidrs(self):
        result, output = self.result, self.cidr_output
        if output is None or not output.complete or not output.count:
            return
        category = self.category.currentData()
        self.page.output_controller._save('IPv6_'+category+'_CIDRs.txt', output.as_text()+'\n',
            lambda: self.result is result and self.cidr_output is output
            and self.category.currentData() == category)

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


class CapacityPanel(InspectionPanel):
    """Read-only snapshot analysis, reusing report copy/save conflict protection."""
    def __init__(self, page, source):
        super().__init__(page, source)
        self.hint.setText(tx('输入父网段，按当前清单快照统计每个前缀的完整可分配容量。'))
        self.input.setAccessibleName(tx('容量总览父网段'))
        self.input.setPlaceholderText('2001:db8::/48')
        self.input.setMaxLength(200)
        self.input.setText(page.planning.parent_input.text())
        self.run_button.setToolTip(tx('计算空闲容量总览'))
        self.run_button.setAccessibleName(tx('计算空闲容量总览'))
        for widget in (self.category, self.copy_cidrs_button, self.save_cidrs_button, self.cidr_status):
            widget.hide()

    def refresh_cidrs(self):
        self.cidr_output = None
        self.copy_cidrs_button.setEnabled(False)
        self.save_cidrs_button.setEnabled(False)

    def run(self):
        from core.subnet_capacity import capacity_overview
        self.invalidate()
        try:
            self.result = capacity_overview(self.source, self.value())
        except InputError as exc:
            self.report.setPlainText(tx('无法规划：')+describe_error(exc))
            return False
        self.report.setPlainText(self.result.as_text())
        self.copy_button.setEnabled(True)
        self.save_button.setEnabled(True)
        return True

    def save(self):
        result = self.result
        if result is not None:
            self.page.output_controller._save('IPv6_CapacityOverview.txt', result.as_text(),
                                             lambda: self.result is result)


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
        self.capacity = CapacityPanel(page, source)
        tabs.addTab(self.capacity, tx('空闲容量总览'))
        layout.addWidget(tabs)


def show_inspection(page):
    if page.service.busy:
        return
    dialog = ListInspectionDialog(page)
    dialog.exec()
