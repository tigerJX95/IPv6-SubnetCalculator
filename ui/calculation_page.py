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

"""计算页：参数输入与结果展示，不执行导出或管理其他页面。"""
from ipaddress import IPv6Address
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QWidget, QScrollArea, QVBoxLayout, QGridLayout,
                             QHBoxLayout, QGroupBox, QLabel, QLineEdit, QComboBox)
from app_info import DEFAULT_NETWORK
from core.ipv6_core import common_target_prefixes, prefix_analysis, subnet_count_description
from core.address_usage import describe_network
from ui.widgets import IconButton, value_label


class CalculationPage(QWidget):
    calculate_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('CalculationPage')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        scroll = QScrollArea()
        scroll.viewport().setObjectName('CalculationViewport')
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setObjectName('CalculationContent')
        body = QVBoxLayout(content)
        body.setContentsMargins(4, 0, 4, 4)
        body.setSpacing(12)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        form = QGroupBox('计算参数')
        grid = QGridLayout(form)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(9)
        grid.setColumnStretch(0, 3)
        grid.setColumnStretch(1, 1)
        grid.addWidget(QLabel('IPv6 网络地址及前缀'), 0, 0)
        grid.addWidget(QLabel('目标子网前缀'), 0, 1)
        self.network_input = QLineEdit(DEFAULT_NETWORK)
        self.network_input.setObjectName('network_input')
        self.network_input.setFont(QFont('Consolas', 11))
        self.network_input.setMaxLength(200)
        self.network_input.setToolTip('填写 IPv6 网络地址及 CIDR 前缀，例如 2026:1015:abcd::/48。')
        grid.addWidget(self.network_input, 1, 0)
        prefix_area = QHBoxLayout()
        self.target_input = QLineEdit('64')
        self.target_input.setObjectName('target_input')
        self.target_input.setFont(QFont('Consolas', 11))
        self.target_input.setMaxLength(3)
        self.target_input.setMinimumWidth(55)
        self.target_input.setToolTip('输入 0～128 的目标前缀，不需要 /，且不得小于原网络前缀。')
        self.prefix_shortcuts = QComboBox()
        self.prefix_shortcuts.setMinimumWidth(110)
        self.prefix_shortcuts.setToolTip('选择适合当前网络的常用目标前缀，并立即计算。')
        prefix_area.addWidget(self.target_input, 1)
        prefix_area.addWidget(self.prefix_shortcuts)
        grid.addLayout(prefix_area, 1, 1)
        self.calculate_button = IconButton('calculate', '开始计算（输入框内按 Enter）')
        self.calculate_button.clicked.connect(self.calculate_requested)
        grid.addWidget(self.calculate_button, 2, 0, alignment=Qt.AlignmentFlag.AlignLeft)
        body.addWidget(form)

        summary = QGroupBox('网络计算摘要')
        summary_grid = QGridLayout(summary)
        summary_grid.setHorizontalSpacing(16)
        summary_grid.setVerticalSpacing(11)
        summary_grid.setColumnStretch(1, 1)
        self.fields = {}
        for row, (label, key) in enumerate((
                ('网络地址', 'network'), ('网络起始地址', 'start'), ('网络结束地址', 'end'),
                ('可划分子网数', 'count'), ('每个子网地址数', 'capacity'), ('新增子网位数', 'bits'))):
            summary_grid.addWidget(QLabel(label+'：'), row, 0, alignment=Qt.AlignmentFlag.AlignTop)
            value = value_label()
            summary_grid.addWidget(value, row, 1)
            self.fields[key] = value
        body.addWidget(summary)

        usage = QGroupBox('地址类型与部署提示')
        usage_layout = QVBoxLayout(usage)
        usage_layout.setSpacing(7)
        self.usage_type = QLabel('—')
        self.usage_type.setObjectName('UsageType')
        self.usage_type.setWordWrap(True)
        self.usage_guidance = QLabel('计算后显示网络地址用途与部署限制。')
        self.usage_guidance.setObjectName('UsageGuidance')
        self.usage_guidance.setWordWrap(True)
        self.usage_reference = QLabel()
        self.usage_reference.setObjectName('Reference')
        self.usage_reference.setWordWrap(True)
        for widget in (self.usage_type, self.usage_guidance, self.usage_reference):
            widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            usage_layout.addWidget(widget)
        body.addWidget(usage)
        body.addStretch()

        self.network_input.textChanged.connect(self._update_shortcuts)
        self.network_input.editingFinished.connect(self.normalize_network)
        self.network_input.returnPressed.connect(self.calculate_requested)
        self.target_input.returnPressed.connect(self.calculate_requested)
        self.prefix_shortcuts.activated.connect(self._choose_prefix)
        self._update_shortcuts()

    def normalize_network(self):
        self.network_input.setText(self.network_input.text().lower())

    def parameters(self):
        self.normalize_network()
        return self.network_input.text(), self.target_input.text()

    def _update_shortcuts(self):
        choices = ()
        source = self.network_input.text().strip()
        if source.count('/') == 1:
            address, prefix = (part.strip() for part in source.split('/'))
            if prefix.isascii() and prefix.isdecimal() and len(prefix) <= 3:
                try:
                    IPv6Address(address)
                    choices = common_target_prefixes(int(prefix))
                except ValueError:
                    pass
        self.prefix_shortcuts.clear()
        self.prefix_shortcuts.addItem('常用前缀', None)
        for prefix in choices:
            self.prefix_shortcuts.addItem(f'/{prefix}', prefix)
        self.prefix_shortcuts.setEnabled(bool(choices))

    def _choose_prefix(self, index):
        prefix = self.prefix_shortcuts.itemData(index)
        if prefix is not None:
            self.target_input.setText(str(prefix))
            self.calculate_requested.emit()

    def set_result(self, result):
        if result is None:
            for label in self.fields.values():
                label.setText('—')
            self.usage_type.setText('—')
            self.usage_guidance.setText('计算后显示网络地址用途与部署限制。')
            self.usage_reference.clear()
            return
        values = dict(network=str(result.network), start=str(result.start_address),
                      end=str(result.end_address), count=subnet_count_description(result),
                      capacity=f'{result.addresses_per_subnet:,}', bits=f'{prefix_analysis(result)} 位')
        for key, text in values.items():
            self.fields[key].setText(text)
        usage = describe_network(result.network)
        self.usage_type.setText('地址类型：'+usage.name)
        self.usage_guidance.setText(usage.guidance)
        self.usage_reference.setText('规范参考：'+usage.reference)
