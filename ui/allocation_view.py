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

"""基于当前空闲快照的分配建议、复制及确认追加。"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from ui.localized_widgets import QLabel, QLineEdit
from ui.widgets import IconButton
from ui.input_feedback import bind_input, clear_invalid, mark_invalid
from ui.standard_dialogs import QMessageBox
from core.localized_text import text as tx
from core.ipv6_core import InputError
from core.subnet_allocation import suggest_subnets
from core.subnet_list import parse_subnet_records


class AllocationView(QWidget):
    def __init__(self, planning, model_class, table_factory):
        super().__init__()
        self.planning = planning
        self.owner = planning.owner
        self.result = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10,8,10,8)
        hint = QLabel(tx('先在“空闲空间”计算父网段及占用清单，再按目标前缀生成建议。'))
        hint.setWordWrap(True)
        layout.addWidget(hint)
        controls = QHBoxLayout()
        controls.addWidget(QLabel(tx('目标前缀：')))
        self.prefix_input = QLineEdit('64')
        self.prefix_input.setMaxLength(5)
        self.prefix_input.setMaximumWidth(100)
        self.prefix_input.setToolTip(tx('填写目标前缀（例如 64 或 /64），不得短于父网段前缀。'))
        controls.addWidget(self.prefix_input)
        controls.addWidget(QLabel(tx('请求数量：')))
        self.count_input = QLineEdit('1')
        self.count_input.setMaxLength(6)
        self.count_input.setMaximumWidth(100)
        self.count_input.setToolTip(tx('单次建议 1 至 5,000 个子网；容量统计保留精确整数。'))
        controls.addWidget(self.count_input)
        controls.addStretch(1)
        self.generate_button = IconButton('free_space', tx('统计可分配容量并生成按地址升序排列的子网建议'))
        self.copy_button = IconButton('copy_page', tx('复制本次建议 CIDR；不会自动占用地址'))
        self.copy_report_button = IconButton('copy', tx('复制分配建议报告，包含精确容量和请求数量'))
        self.save_button = IconButton('save_plan', tx('保存分配建议 CIDR 或报告为 TXT'))
        self.append_button = IconButton('check_list', tx('确认后将建议追加到占用清单，并重新计算剩余空闲空间'))
        for button in (self.generate_button,self.copy_button,self.copy_report_button,self.save_button,self.append_button):
            controls.addWidget(button)
        layout.addLayout(controls)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.status)
        self.model = model_class((tx('建议 CIDR'),tx('地址数量')),self)
        self.table = table_factory(self.model)
        self.table.setMinimumHeight(55)
        self.table.setColumnWidth(0,400)
        layout.addWidget(self.table,1)
        for edit in (self.prefix_input,self.count_input):
            bind_input(edit)
            edit.textChanged.connect(self.clear)
            edit.returnPressed.connect(self.generate)
        self.generate_button.clicked.connect(self.generate)
        self.copy_button.clicked.connect(self.copy_cidrs)
        self.copy_report_button.clicked.connect(self.copy_report)
        self.append_button.clicked.connect(self.append)
        self.clear()

    def clear(self, *_args):
        self.result = None
        self.model.set_rows([])
        self.status.setText(tx('建议尚未生成；修改占用清单、父网段或请求参数后须重新生成。'))
        self.refresh()

    def refresh(self):
        ready = not self.owner.service.busy
        available = self.planning.free_result is not None
        self.prefix_input.setReadOnly(not ready)
        self.count_input.setReadOnly(not ready)
        self.generate_button.setEnabled(ready and available)
        full = ready and self.result is not None and bool(self.result.cidrs)
        self.copy_button.setEnabled(full)
        self.append_button.setEnabled(full)
        self.copy_report_button.setEnabled(ready and self.result is not None)
        self.save_button.setEnabled(ready and self.result is not None)
        output = getattr(self.owner,'output_controller',None)
        if output is not None:
            output.refresh()

    def generate(self):
        if self.owner.service.busy or self.planning.free_result is None:
            return
        self.clear()
        for edit in (self.prefix_input,self.count_input):
            clear_invalid(edit)
        try:
            result = suggest_subnets(self.planning.free_result,self.prefix_input.text(),self.count_input.text())
        except InputError as exc:
            mark_invalid(self.prefix_input if exc.field=='prefix' else self.count_input,str(exc))
            self.status.setText(exc.args[0])
            self.owner.feedback.emit(exc.args[0],'error')
            return
        self.result = result
        self.model.set_rows((str(net),tx('{0:,}',net.num_addresses)) for net in result.cidrs)
        self.status.setText(tx('父网段：{0}\n可分配 /{1} 子网 {2:,} 个；请求 {3:,} 个，建议 {4:,} 个。',result.free.parent,result.prefix,result.capacity,result.requested,len(result.cidrs))+
            tx('\n建议尚未占用；确认追加后才更新当前占用清单。') if result.sufficient else
            tx('可分配 /{0} 子网仅 {1:,} 个，少于请求的 {2:,} 个；未生成部分建议。',result.prefix,result.capacity,result.requested))
        self.refresh()

    def copy_cidrs(self):
        if not self.owner.service.busy and self.result is not None and self.result.cidrs:
            self.owner.clipboard.copy_text(self.result.cidr_text(),tx('分配建议 CIDR 已复制。'),self)

    def copy_report(self):
        if not self.owner.service.busy and self.result is not None:
            self.owner.clipboard.copy_text(self.result.as_text(),tx('分配建议报告已复制。'),self)

    def append(self):
        page = self.owner
        result = self.result
        if page.service.busy or result is None or not result.cidrs:
            return
        previous = page.editor.toPlainText()
        combined = previous + ('\n' if previous and not previous.endswith('\n') else '') + str(result.cidr_text()) + '\n'
        try:
            parse_subnet_records(combined, allow_empty=True)
        except InputError as exc:
            page.feedback.emit(tx('无法追加建议：')+exc.args[0],'error')
            return
        answer = QMessageBox.question(self,tx('追加分配建议'),
            tx('将 {0:,} 个建议子网追加到当前占用清单，保留已有内容，并重新计算空闲空间。是否继续？',len(result.cidrs)),
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        if page.service.busy or self.result is not result or self.planning.free_result is not result.free or page.editor.toPlainText()!=previous:
            page.feedback.emit(tx('清单、参数或规划结果已变化，请重新生成建议后再追加。'),'info')
            return
        page.editor.setPlainText(combined)
        page.start_planning('free')
