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

"""与清单输入共享快照的两个独立规划结果页。"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit
from app_info import DEFAULT_NETWORK
from ui.input_feedback import bind_input, mark_invalid
from ui.fonts import data_font
from ui.widgets import IconButton


class PlanningViews:
    def __init__(self, owner, model_class, table_factory):
        self.owner=owner
        self.free_result=None
        self.aggregate_result=None
        self.free_page=QWidget()
        layout=QVBoxLayout(self.free_page)
        layout.setContentsMargins(10,8,10,8)
        controls=QHBoxLayout()
        controls.addWidget(QLabel('父网段：'))
        self.parent_input=QLineEdit(DEFAULT_NETWORK)
        bind_input(self.parent_input)
        self.parent_input.setFont(data_font())
        self.parent_input.setMaxLength(200)
        self.parent_input.setToolTip('占用清单必须全部位于此父网段内；空清单表示父网段尚无占用。')
        controls.addWidget(self.parent_input,1)
        self.free_button=IconButton('free_space','计算父网段减去当前占用清单后的空闲空间')
        self.copy_free_button=IconButton('copy_page','复制完整空闲 CIDR；明细截断时禁用，避免漏复制')
        self.copy_free_report_button=IconButton('copy','复制空闲报告：含全部空闲地址范围与精确容量')
        for button in (self.free_button,self.copy_free_button,self.copy_free_report_button):controls.addWidget(button)
        layout.addLayout(controls)
        self.free_status=QLabel()
        self.free_status.setWordWrap(True)
        self.free_status.setTextFormat(Qt.TextFormat.PlainText)
        self.free_status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.free_status)
        self.free_model=model_class(('空闲 CIDR','地址数量'),owner)
        self.free_table=table_factory(self.free_model)
        self.free_table.setMinimumHeight(55)
        self.free_table.setColumnWidth(0,400)
        layout.addWidget(self.free_table,1)
        self.aggregate_page=QWidget()
        layout=QVBoxLayout(self.aggregate_page)
        layout.setContentsMargins(10,8,10,8)
        controls=QHBoxLayout()
        note=QLabel('保持地址覆盖范围不变，移除重复及已覆盖子网，并精确合并。')
        note.setWordWrap(True)
        controls.addWidget(note,1)
        self.aggregate_button=IconButton('aggregate','整理为覆盖范围完全相同的最简 CIDR 集合；不修改原始清单')
        self.copy_aggregate_button=IconButton('copy_page','复制整理后的完整 CIDR 集合')
        self.copy_aggregate_report_button=IconButton('copy','复制 CIDR 整理报告与完整结果')
        for button in (self.aggregate_button,self.copy_aggregate_button,self.copy_aggregate_report_button):controls.addWidget(button)
        layout.addLayout(controls)
        self.aggregate_status=QLabel()
        self.aggregate_status.setWordWrap(True)
        self.aggregate_status.setTextFormat(Qt.TextFormat.PlainText)
        self.aggregate_status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.aggregate_status)
        self.aggregate_model=model_class(('整理后的 CIDR','地址数量'),owner)
        self.aggregate_table=table_factory(self.aggregate_model)
        self.aggregate_table.setMinimumHeight(55)
        self.aggregate_table.setColumnWidth(0,400)
        layout.addWidget(self.aggregate_table,1)
        owner.result_tabs.addTab(self.free_page,'空闲空间')
        owner.result_tabs.addTab(self.aggregate_page,'CIDR 整理')
        self.free_button.clicked.connect(lambda:owner.start_planning('free'))
        self.parent_input.returnPressed.connect(lambda:owner.start_planning('free'))
        self.aggregate_button.clicked.connect(lambda:owner.start_planning('aggregate'))
        self.parent_input.textChanged.connect(self.clear_free)
        self.copy_free_button.clicked.connect(self.copy_free)
        self.copy_aggregate_button.clicked.connect(self.copy_aggregate)
        self.copy_free_report_button.clicked.connect(lambda:self.copy_report('free'))
        self.copy_aggregate_report_button.clicked.connect(lambda:self.copy_report('aggregate'))
        self.clear_all()

    def clear_free(self, *_args):
        self.free_result=None
        self.free_status.setToolTip('')
        self.free_model.set_rows([])
        self.free_status.setText('填写父网段后计算。所有占用记录须有效且完全位于父网段内。')
        self.refresh_buttons()

    def clear_aggregate(self):
        self.aggregate_result=None
        self.aggregate_model.set_rows([])
        self.aggregate_status.setText('整理仅改变表示方式，不保留原始分配层级；请确认业务边界后使用。')
        self.refresh_buttons()

    def clear_all(self):
        self.clear_free()
        self.clear_aggregate()

    def refresh_buttons(self):
        busy=self.owner.service.busy
        self.parent_input.setReadOnly(busy)
        self.free_button.setEnabled(not busy)
        self.aggregate_button.setEnabled(not busy)
        self.copy_free_button.setEnabled(not busy and self.free_result is not None and self.free_result.complete and bool(self.free_result.cidrs))
        self.copy_free_report_button.setEnabled(not busy and self.free_result is not None)
        self.copy_aggregate_button.setEnabled(not busy and self.aggregate_result is not None)
        self.copy_aggregate_report_button.setEnabled(not busy and self.aggregate_result is not None)

    def status(self, task):
        return self.free_status if task=='free' else self.aggregate_status

    def completed(self, task, outcome):
        kind,result=outcome
        if kind!='ok':
            if kind!='cancel':
                mark_invalid(self.owner.editor,str(result))
            self.status(task).setText('已取消规划，原始输入已保留。' if kind=='cancel' else '无法规划：'+result)
            self.owner.feedback.emit(self.status(task).text(),'info' if kind=='cancel' else 'error')
            return
        if task=='free':
            self.free_result=result
            self.free_model.set_rows((str(net),f'{net.num_addresses:,}') for net in result.cidrs)
            self.free_status.setToolTip(f'占用并集：{result.occupied_addresses:,} 个地址\n空闲：{result.free_addresses:,} 个地址')
            self.free_status.setText(f'父网段：{result.parent}'+('（主机位已规范化）' if result.parent_normalized else '')+
                f'｜空闲 CIDR {result.cidr_count:,} 条，显示 {len(result.cidrs):,} 条。\n'+
                ('明细已截断；完整 CIDR 复制已禁用。' if not result.complete else '')+
                '精确地址容量见悬停提示或复制报告。')
        else:
            self.aggregate_result=result
            self.aggregate_model.set_rows((str(net),f'{net.num_addresses:,}') for net in result.cidrs)
            self.aggregate_status.setText(f'输入 {result.input_count:,} 条 → 整理后 {len(result.cidrs):,} 条；'
                f'覆盖地址并集 {result.address_count:,} 个。\n地址覆盖范围不变；原始输入未修改。')
        self.owner.feedback.emit('空闲空间计算完成。' if task=='free' else '等价 CIDR 整理完成。','success')

    def copy_free(self):
        result=self.free_result
        if result is not None and result.complete and result.cidrs:
            self.owner.clipboard.copy_text(result.cidr_text(),'完整空闲 CIDR 已复制。',self.free_page)

    def copy_aggregate(self):
        if self.aggregate_result is not None:
            self.owner.clipboard.copy_text(self.aggregate_result.cidr_text(),'整理后的完整 CIDR 已复制。',self.aggregate_page)

    def copy_report(self, task):
        result=self.free_result if task=='free' else self.aggregate_result
        if result is not None:
            self.owner.clipboard.copy_text(result.as_text(),'规划报告已复制。',self.free_page if task=='free' else self.aggregate_page)
