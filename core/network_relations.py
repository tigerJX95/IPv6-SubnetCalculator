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

"""两个 IPv6 CIDR 的关系分析，不遍历地址空间。"""
from dataclasses import dataclass
from ipaddress import IPv6Network
from core.ipv6_core import calculate, InputError


@dataclass(frozen=True)
class NetworkRelation:
    network_a: IPv6Network
    network_b: IPv6Network
    normalized_a: bool
    normalized_b: bool
    kind: str
    title: str
    detail: str
    overlap_count: int
    gap_count: int

    def as_text(self):
        a, b = self.network_a, self.network_b
        return '\n'.join(('IPv6 双网段关系分析',
            f'网段 A：{a}', f'A 地址范围：{a.network_address} ～ {a.broadcast_address}',
            f'网段 B：{b}', f'B 地址范围：{b.network_address} ～ {b.broadcast_address}',
            f'关系：{self.title}', f'重叠地址数：{self.overlap_count:,}',
            f'间隔地址数：{self.gap_count:,}', f'说明：{self.detail}',
            f'主机位规范化：A {"是" if self.normalized_a else "否"}；B {"是" if self.normalized_b else "否"}'))


def analyze_networks(text_a: str, text_b: str) -> NetworkRelation:
    results = []
    for label, text in (('A', text_a), ('B', text_b)):
        try:
            # 复用计算器的 CIDR 校验和主机位规范化，关闭预览，不生成子网。
            results.append(calculate(text, '128', preview_limit=0))
        except InputError as exc:
            raise InputError(f'网段 {label}：{exc}') from exc
    first, second = results
    a, b = first.network, second.network
    overlap = gap = 0
    if a == b:
        kind, title = 'same', '相同'
        overlap = a.num_addresses
        detail = '两个 CIDR 规范化后表示相同的地址范围。'
    elif b.subnet_of(a):
        kind, title = 'a_contains_b', 'A 包含 B'
        overlap = b.num_addresses
        detail = '网段 B 的全部地址都在网段 A 内，且 B 是更小的网段。'
    elif a.subnet_of(b):
        kind, title = 'b_contains_a', 'B 包含 A'
        overlap = a.num_addresses
        detail = '网段 A 的全部地址都在网段 B 内，且 A 是更小的网段。'
    else:
        lower, upper = sorted((a, b), key=lambda net: int(net.network_address))
        gap = int(upper.network_address) - int(lower.broadcast_address) - 1
        if gap == 0:
            kind, title = 'adjacent', '相邻（无重叠）'
            detail = '两个网段首尾相接，没有重叠或间隔；相邻不代表一定能合并为单个 CIDR。'
        else:
            kind, title = 'independent', '完全独立（不相邻）'
            detail = '两个网段没有重叠，且地址范围之间存在间隔。'
    return NetworkRelation(a, b, first.normalized, second.normalized,
                           kind, title, detail, overlap, gap)
