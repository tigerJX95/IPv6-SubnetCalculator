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
from core.localized_text import text as tx, join_text as jt
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
        return jt('\n', (tx('IPv6 双网段关系分析'), tx('网段 A：{0}', a), tx('A 地址范围：{0} ～ {1}', a.network_address, a.broadcast_address), tx('网段 B：{0}', b), tx('B 地址范围：{0} ～ {1}', b.network_address, b.broadcast_address), tx('关系：{0}', self.title), tx('重叠地址数：{0:,}', self.overlap_count), tx('间隔地址数：{0:,}', self.gap_count), tx('说明：{0}', self.detail), tx('主机位规范化：A {0}；B {1}', tx('是') if self.normalized_a else tx('否'), tx('是') if self.normalized_b else tx('否'))))


def analyze_networks(text_a: str, text_b: str) -> NetworkRelation:
    results = []
    for label, text in (('A', text_a), ('B', text_b)):
        try:
            # 复用计算器的 CIDR 校验和主机位规范化，关闭预览，不生成子网。
            results.append(calculate(text, '128', preview_limit=0))
        except InputError as exc:
            raise InputError(tx('网段 {0}：{1}', label, exc), field=label) from exc
    first, second = results
    a, b = first.network, second.network
    overlap = gap = 0
    if a == b:
        kind, title = 'same', tx('相同')
        overlap = a.num_addresses
        detail = tx('两个 CIDR 规范化后表示相同的地址范围。')
    elif b.subnet_of(a):
        kind, title = 'a_contains_b', tx('A 包含 B')
        overlap = b.num_addresses
        detail = tx('网段 B 的全部地址都在网段 A 内，且 B 是更小的网段。')
    elif a.subnet_of(b):
        kind, title = 'b_contains_a', tx('B 包含 A')
        overlap = a.num_addresses
        detail = tx('网段 A 的全部地址都在网段 B 内，且 A 是更小的网段。')
    else:
        lower, upper = sorted((a, b), key=lambda net: int(net.network_address))
        gap = int(upper.network_address) - int(lower.broadcast_address) - 1
        if gap == 0:
            kind, title = 'adjacent', tx('相邻（无重叠）')
            detail = tx('两个网段首尾相接，没有重叠或间隔；相邻不代表一定能合并为单个 CIDR。')
        else:
            kind, title = 'independent', tx('完全独立（不相邻）')
            detail = tx('两个网段没有重叠，且地址范围之间存在间隔。')
    return NetworkRelation(a, b, first.normalized, second.normalized,
                           kind, title, detail, overlap, gap)
