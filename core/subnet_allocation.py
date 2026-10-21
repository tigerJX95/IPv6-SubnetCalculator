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

"""从完整空闲区间按 CIDR 对齐统计容量并生成有界建议；不枚举地址。"""
from dataclasses import dataclass
from ipaddress import IPv6Network
import re
from core.ipv6_core import InputError
from core.localized_text import text as tx, join_text as jt

MAX_ALLOCATION_SUGGESTIONS = 5000


def _number(value, minimum, maximum, message, field):
    value = str(value).strip()
    if field == 'prefix' and value.startswith('/'):
        value = value[1:]
    if not re.fullmatch(r'[0-9]{1,6}', value):
        raise InputError(message, field=field)
    number = int(value)
    if not minimum <= number <= maximum:
        raise InputError(message, field=field)
    return number


@dataclass(frozen=True)
class AllocationResult:
    free: object
    prefix: int
    requested: int
    capacity: int
    cidrs: tuple

    @property
    def sufficient(self):
        return self.capacity >= self.requested

    def cidr_text(self):
        return jt('\n', map(str, self.cidrs))

    def as_text(self):
        return jt('\n', [tx('IPv6 子网分配建议报告'),
            tx('父网段：{0}', self.free.parent),
            tx('目标前缀：/{0}', self.prefix),
            tx('可分配子网总数：{0:,}', self.capacity),
            tx('请求数量：{0:,}', self.requested),
            tx('建议数量：{0:,}', len(self.cidrs)),
            tx('每个子网地址数：{0:,}', 1 << (128-self.prefix)),
            tx('按地址从小到大选择完整且对齐的空闲子网；请求超过容量时不生成部分建议。'),
            tx('建议尚未占用；追加到清单前请确认用途、授权及实际网络状态。'),
            '', tx('建议 CIDR：'), self.cidr_text()])


def suggest_subnets(free, prefix, count):
    target = _number(prefix, free.parent.prefixlen, 128,
        tx('目标前缀须为 /{0} 至 /128 的整数。', free.parent.prefixlen), 'prefix')
    requested = _number(count, 1, MAX_ALLOCATION_SUGGESTIONS,
        tx('请求数量须为 1 至 {0:,} 的整数。', MAX_ALLOCATION_SUGGESTIONS), 'count')
    block = 1 << (128-target)
    aligned = []
    capacity = 0
    for start, end in free.free_ranges:
        first = ((start+block-1)//block)*block
        available = max(0, (end-first+1)//block)
        if available:
            capacity += available
            aligned.append((first, available))
    suggestions = []
    if capacity >= requested:
        remaining = requested
        for first, available in aligned:
            take = min(available, remaining)
            suggestions.extend(IPv6Network((first+index*block, target)) for index in range(take))
            remaining -= take
            if not remaining:
                break
    return AllocationResult(free, target, requested, capacity, tuple(suggestions))
