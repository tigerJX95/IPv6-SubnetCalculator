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

"""地址格式与双网段分析独立页面，结果不改变计算器状态。"""
from ui.localized_widgets import QGroupBox, QLabel, QLineEdit
from core.localized_text import text as tx, join_text as jt
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QGridLayout
from app_info import DEFAULT_NETWORK
from core.ipv6_core import InputError
from core.address_conversion import convert_address
from core.network_relations import analyze_networks
from ui.input_feedback import bind_input, mark_invalid, clear_invalid
from ui.fonts import data_font
from ui.widgets import IconButton, value_label


def _input(text, tooltip):
    widget = QLineEdit(text)
    widget.setMaxLength(200)
    widget.setFont(data_font())
    widget.setToolTip(tooltip)
    return widget


def _copy_button(name, tooltip):
    button = IconButton('copy', tooltip)
    button.setObjectName(name)
    button.setIconSize(QSize(30, 30))
    button.setFixedSize(36, 36)
    button.setEnabled(False)
    return button


class AddressToolsPage(QWidget):
    feedback = pyqtSignal(object, str)

    def __init__(self, clipboard, parent=None):
        super().__init__(parent)
        self.setObjectName('AddressToolsPage')
        self.clipboard = clipboard
        self.formats = None
        self.relation = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.viewport().setObjectName('ToolsViewport')
        content = QWidget()
        content.setObjectName('ToolsContent')
        body = QVBoxLayout(content)
        body.setContentsMargins(4, 0, 4, 4)
        body.setSpacing(12)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        conversion = QGroupBox(tx('IPv6 地址格式转换'))
        grid = QGridLayout(conversion)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(7)
        grid.setColumnStretch(1, 1)
        self.address_input = _input(DEFAULT_NETWORK.split('/')[0], tx('填写单个 IPv6 地址，不带 / 前缀或 % 区域标识。'))
        self.address_input.setObjectName('format_address_input')
        self.convert_button = IconButton('calculate', tx('转换地址格式（输入框内按 Enter）'))
        self.copy_formats_button = _copy_button('copy_all_formats', tx('复制全部地址格式\n二进制以连续 128 位复制。'))
        grid.addWidget(self.address_input, 0, 0, 1, 2)
        grid.addWidget(self.convert_button, 0, 2)
        grid.addWidget(self.copy_formats_button, 0, 3)
        self.format_fields, self.format_copy_buttons = {}, {}
        for row, (label, key) in enumerate(((tx('压缩 / 规范化'), 'compressed'),
                                            (tx('完整展开'), 'expanded'), (tx('二进制 · 128 位'), 'binary')), 1):
            grid.addWidget(QLabel(label+'：'), row, 0)
            field = value_label()
            if key == 'binary':
                field.setFont(data_font(dense=True))
            grid.addWidget(field, row, 1, 1, 2)
            button = _copy_button('copy_format_'+key, tx('复制')+label+tx('\n复制当前显示的转换结果。'))
            button.clicked.connect(lambda _checked=False, key=key: self.copy_format(key))
            grid.addWidget(button, row, 3)
            self.format_fields[key], self.format_copy_buttons[key] = field, button
        hint = QLabel(tx('规范化采用小写压缩表示；二进制按 16 位分组显示，复制为连续 128 位。'))
        hint.setObjectName('Reference')
        hint.setWordWrap(True)
        grid.addWidget(hint, 4, 0, 1, 4)
        body.addWidget(conversion)

        networks = QGroupBox(tx('双网段关系分析'))
        grid = QGridLayout(networks)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        self.network_a_input = _input(DEFAULT_NETWORK, tx('网段 A：填写 IPv6 CIDR；主机位自动规范化到所属网络。'))
        self.network_b_input = _input('2026:1015:abcd::/64', tx('网段 B：填写 IPv6 CIDR；主机位自动规范化到所属网络。'))
        self.network_a_input.setObjectName('relation_network_a')
        self.network_b_input.setObjectName('relation_network_b')
        grid.addWidget(QLabel(tx('网段 A')), 0, 0)
        grid.addWidget(QLabel(tx('网段 B')), 0, 1)
        grid.addWidget(self.network_a_input, 1, 0)
        grid.addWidget(self.network_b_input, 1, 1)
        self.analyze_button = IconButton('calculate', tx('分析双网段关系（输入框内按 Enter）'))
        self.copy_relation_button = _copy_button('copy_network_relation', tx('复制关系分析\n包含两个网段的范围、精确重叠和间隔地址数。'))
        grid.addWidget(self.analyze_button, 1, 2)
        grid.addWidget(self.copy_relation_button, 1, 3)
        self.relation_title = QLabel(tx('输入两个 CIDR 后点击分析图标。'))
        self.relation_title.setObjectName('Hint')
        self.relation_title.setWordWrap(True)
        grid.addWidget(self.relation_title, 2, 0, 1, 4)
        self.relation_fields = {}
        for row, key in enumerate(('a', 'b', 'counts'), 3):
            field = value_label()
            grid.addWidget(field, row, 0, 1, 4)
            self.relation_fields[key] = field
        self.relation_detail = QLabel(tx('识别相同、包含、相邻或完全独立；输入主机位会自动规范化。'))
        self.relation_detail.setObjectName('Reference')
        self.relation_detail.setWordWrap(True)
        grid.addWidget(self.relation_detail, 6, 0, 1, 4)
        body.addWidget(networks)
        body.addStretch()

        self.address_input.textChanged.connect(self._clear_formats)
        self.network_a_input.textChanged.connect(self._clear_relation)
        self.network_b_input.textChanged.connect(self._clear_relation)
        self.address_input.returnPressed.connect(self.convert)
        self.network_a_input.returnPressed.connect(self.analyze)
        self.network_b_input.returnPressed.connect(self.analyze)
        self.convert_button.clicked.connect(self.convert)
        self.analyze_button.clicked.connect(self.analyze)
        self.copy_formats_button.clicked.connect(self.copy_formats)
        self.copy_relation_button.clicked.connect(self.copy_relation)
        for field in (self.address_input,self.network_a_input,self.network_b_input):
            bind_input(field)

    def _clear_formats(self):
        self.formats = None
        for key, field in self.format_fields.items():
            field.setText('—')
            self.format_copy_buttons[key].setEnabled(False)
        self.copy_formats_button.setEnabled(False)

    def _clear_relation(self):
        self.relation = None
        self.relation_title.setText(tx('输入两个 CIDR 后点击分析图标。'))
        for field in self.relation_fields.values():
            field.setText('—')
        self.relation_detail.setText(tx('识别相同、包含、相邻或完全独立；输入主机位会自动规范化。'))
        self.copy_relation_button.setEnabled(False)

    def convert(self):
        clear_invalid(self.address_input)
        try:
            formats = convert_address(self.address_input.text())
        except InputError as exc:
            self._clear_formats()
            mark_invalid(self.address_input,str(exc))
            self.address_input.setFocus()
            self.feedback.emit(tx('输入错误：')+str(exc), 'error')
            return
        self.formats = formats
        for key, field in self.format_fields.items():
            text = getattr(formats, key)
            if key == 'binary':
                groups = [text[index:index+16] for index in range(0, 128, 16)]
                text = jt(' ', groups[:4])+'\n'+jt(' ', groups[4:])
            field.setText(text)
            self.format_copy_buttons[key].setEnabled(True)
        self.copy_formats_button.setEnabled(True)
        self.feedback.emit(tx('地址格式转换完成。'), 'success')

    def analyze(self):
        clear_invalid(self.network_a_input)
        clear_invalid(self.network_b_input)
        try:
            relation = analyze_networks(self.network_a_input.text(), self.network_b_input.text())
        except InputError as exc:
            self._clear_relation()
            field=self.network_b_input if exc.field=='B' else self.network_a_input
            mark_invalid(field,str(exc))
            field.setFocus()
            self.feedback.emit(tx('输入错误：')+str(exc), 'error')
            return
        self.relation = relation
        self.relation_title.setText(tx('分析结果：')+relation.title)
        self.relation_fields['a'].setText('A：'+str(relation.network_a))
        self.relation_fields['b'].setText('B：'+str(relation.network_b))
        self.relation_fields['counts'].setText(tx('重叠地址数：{0:,}    间隔地址数：{1:,}', relation.overlap_count, relation.gap_count))
        self.relation_detail.setText(relation.detail)
        self.copy_relation_button.setEnabled(True)
        normalized = tx('（主机位已规范化：')+ jt('、', (label for label, flag in (('A', relation.normalized_a), ('B', relation.normalized_b)) if flag))+'）' if relation.normalized_a or relation.normalized_b else ''
        self.feedback.emit(tx('网段关系分析完成')+normalized+'。', 'success')

    def copy_format(self, key):
        if self.formats is not None:
            self.clipboard.copy_text(getattr(self.formats, key), tx('地址格式已复制到剪贴板。'), self)

    def copy_formats(self):
        if self.formats is not None:
            self.clipboard.copy_text(self.formats.as_text(), tx('全部地址格式已复制到剪贴板。'), self)

    def copy_relation(self):
        if self.relation is not None:
            self.clipboard.copy_text(self.relation.as_text(), tx('关系分析已复制到剪贴板。'), self)
