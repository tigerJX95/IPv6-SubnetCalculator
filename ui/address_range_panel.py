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

"""地址范围转换面板，独立维护验证、复制与清单发送。"""
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout
from ui.localized_widgets import QGroupBox, QLabel, QLineEdit, QPlainTextEdit
from core.address_range import range_to_cidrs
from core.ipv6_core import InputError
from core.localized_text import text as tx
from ui.fonts import data_font
from ui.widgets import IconButton
from ui.input_feedback import bind_input, clear_invalid, mark_invalid


class AddressRangePanel(QGroupBox):
    feedback=pyqtSignal(object,str)
    transfer_requested=pyqtSignal(str)

    def __init__(self,clipboard,parent=None):
        super().__init__(tx('IPv6 地址范围转 CIDR'),parent)
        self.clipboard=clipboard
        self.result=None
        grid=QGridLayout(self);grid.setHorizontalSpacing(12);grid.setVerticalSpacing(8)
        grid.setColumnStretch(0,1);grid.setColumnStretch(1,1)
        self.start_input=QLineEdit('2026:1015:abcd::1')
        self.end_input=QLineEdit('2026:1015:abcd::ff')
        grid.addWidget(QLabel(tx('起始地址（包含）')),0,0)
        grid.addWidget(QLabel(tx('结束地址（包含）')),0,1)
        for col,field in enumerate((self.start_input,self.end_input)):
            field.setMaxLength(200);field.setFont(data_font())
            field.setToolTip(tx('填写单个 IPv6 地址，不带 / 前缀或 % 区域标识。'))
            grid.addWidget(field,1,col);bind_input(field)
            field.textChanged.connect(self.clear_result)
            field.returnPressed.connect(self.convert)
        self.convert_button=IconButton('calculate',tx('将起止地址转换为精确覆盖范围的最简 CIDR（Enter）'))
        self.copy_button=IconButton('copy_page',tx('复制转换后的完整 CIDR 清单'))
        self.report_button=IconButton('copy',tx('复制地址范围及 CIDR 转换报告'))
        self.transfer_button=IconButton('check_list',tx('将转换结果送入子网清单并检查；替换已有输入前确认'))
        actions=QHBoxLayout()
        for button in (self.convert_button,self.copy_button,self.report_button,self.transfer_button):actions.addWidget(button)
        actions.addStretch()
        grid.addLayout(actions,2,0,1,2)
        self.summary=QLabel(tx('输入首末 IPv6 地址，生成不超出范围的最简 CIDR 清单。'));self.summary.setWordWrap(True)
        grid.addWidget(self.summary,3,0,1,2)
        self.output=QPlainTextEdit();self.output.setReadOnly(True);self.output.setFont(data_font());self.output.setFixedHeight(110)
        self.output.setAccessibleName(tx('地址范围 CIDR 结果'))
        grid.addWidget(self.output,4,0,1,2)
        self.convert_button.clicked.connect(self.convert)
        self.copy_button.clicked.connect(self.copy_cidrs)
        self.report_button.clicked.connect(self.copy_report)
        self.transfer_button.clicked.connect(self.send_to_list)
        self.clear_result()

    def clear_result(self):
        self.result=None;self.output.clear()
        self.summary.setText(tx('输入首末 IPv6 地址，生成不超出范围的最简 CIDR 清单。'))
        for button in (self.copy_button,self.report_button,self.transfer_button):button.setEnabled(False)

    def convert(self):
        for field in (self.start_input,self.end_input):clear_invalid(field)
        try:result=range_to_cidrs(self.start_input.text(),self.end_input.text())
        except InputError as exc:
            self.clear_result()
            field=self.end_input if exc.field=='end' else self.start_input
            mark_invalid(field,str(exc));field.setFocus()
            self.feedback.emit(tx('输入错误：')+str(exc),'error');return
        self.result=result;self.output.setPlainText(result.cidr_text())
        self.summary.setText(tx('地址总数：{0:,}；CIDR 数量：{1:,}',result.address_count,len(result.cidrs)))
        for button in (self.copy_button,self.report_button,self.transfer_button):button.setEnabled(True)
        self.feedback.emit(tx('地址范围转换完成。'),'success')

    def copy_cidrs(self):
        if self.result is not None:self.clipboard.copy_text(self.result.cidr_text(),tx('范围 CIDR 清单已复制。'),self)

    def copy_report(self):
        if self.result is not None:self.clipboard.copy_text(self.result.as_text(),tx('范围转换报告已复制。'),self)

    def send_to_list(self):
        if self.result is not None:self.transfer_requested.emit(self.result.cidr_text())
