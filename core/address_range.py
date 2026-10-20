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

"""将包含首末地址的 IPv6 范围精确转换为最少 CIDR，无需枚举地址。"""
from dataclasses import dataclass
from ipaddress import IPv6Address, summarize_address_range
from core.ipv6_core import validate_ipv6_address, InputError
from core.localized_text import text as tx, join_text as jt


@dataclass(frozen=True)
class AddressRangeResult:
    start: IPv6Address
    end: IPv6Address
    cidrs: tuple

    @property
    def address_count(self):
        return int(self.end)-int(self.start)+1

    def cidr_text(self):
        return '\n'.join(str(net) for net in self.cidrs)

    def as_text(self):
        return jt('\n', (tx('IPv6 地址范围转 CIDR'),
            tx('起始地址：{0}', self.start), tx('结束地址：{0}', self.end),
            tx('地址总数：{0:,}；CIDR 数量：{1:,}', self.address_count, len(self.cidrs)),
            self.cidr_text()))


def range_to_cidrs(start_text, end_text):
    values=[]
    for name,value,label in (('start',start_text,tx('起始地址')),('end',end_text,tx('结束地址'))):
        try:
            values.append(validate_ipv6_address(value))
        except InputError as exc:
            raise InputError(tx('{0}：{1}',label,exc),field=name) from exc
    start,end=values
    if int(end)<int(start):
        raise InputError(tx('结束地址不能小于起始地址。'),field='end')
    return AddressRangeResult(start,end,tuple(summarize_address_range(start,end)))
