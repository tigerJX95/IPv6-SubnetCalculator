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

"""通过闭区间求并集、差集与精确 CIDR 覆盖，不枚举 IPv6 地址。"""
from core.localized_text import text as tx, join_text as jt
from dataclasses import dataclass
from ipaddress import IPv6Address, IPv6Network
from core.ipv6_core import InputError, calculate
from core.subnet_list import parse_subnet_records, _check_stop

MAX_FREE_DETAILS = 5000


def _records(text, stop, allow_empty=False):
    records = parse_subnet_records(text, stop=stop, allow_empty=allow_empty)
    invalid = [record for record in records if record.error]
    if invalid:
        lines = jt('、', (str(record.line) for record in invalid[:5]))
        raise InputError(tx('第 {0} 行存在错误。规划要求所有网段有效，请先修正清单。', lines))
    return records


def _union(records, stop):
    intervals = sorted((int(r.network.network_address), int(r.network.broadcast_address)) for r in records)
    result = []
    for start,end in intervals:
        _check_stop(stop)
        if result and start<=result[-1][1]+1:
            result[-1] = (result[-1][0],max(end,result[-1][1]))
        else:
            result.append((start,end))
    return tuple(result)


def _cidrs(intervals, stop):
    for start,end in intervals:
        while start<=end:
            _check_stop(stop)
            alignment = 128 if start==0 else (start & -start).bit_length()-1
            exponent = min(alignment,(end-start+1).bit_length()-1)
            yield start,128-exponent
            start += 1<<exponent


@dataclass(frozen=True)
class FreeSpaceResult:
    parent: IPv6Network
    parent_normalized: bool
    input_count: int
    normalized_count: int
    occupied_addresses: int
    free_ranges: tuple
    cidrs: tuple
    cidr_count: int

    @property
    def free_addresses(self):
        return self.parent.num_addresses-self.occupied_addresses

    @property
    def complete(self):
        return len(self.cidrs)==self.cidr_count

    def cidr_text(self):
        if not self.complete:
            raise InputError(tx('空闲 CIDR 明细已截断，不能作为完整清单复制；请复制含全部地址范围的报告。'))
        return jt('\n', map(str, self.cidrs))

    def as_text(self):
        lines=[tx('IPv6 空闲空间报告'),tx('父网段：{0}', self.parent),
            tx('父网段主机位规范化：{0}', tx('是') if self.parent_normalized else tx('否')),
            tx('占用清单：{0:,} 条；主机位规范化：{1:,} 条', self.input_count, self.normalized_count),
            tx('父网段地址数：{0:,}', self.parent.num_addresses),tx('占用并集地址数：{0:,}', self.occupied_addresses),
            tx('空闲地址数：{0:,}', self.free_addresses),tx('空闲连续范围：{0:,} 段', len(self.free_ranges)),
            tx('最简空闲 CIDR：{0:,} 条；明细显示 {1:,} 条', self.cidr_count, len(self.cidrs)),
            tx('空闲仅指父网段扣除当前清单的数学差集，不证明地址已获分配或可部署。'),
            '', tx('全部空闲地址范围（包含首末地址）：')]
        lines.extend(tx('{0} ～ {1}｜{2:,} 个地址', IPv6Address(start), IPv6Address(end), end - start + 1) for start,end in self.free_ranges)
        lines.extend(['',tx('空闲 CIDR 明细：'),*(str(net) for net in self.cidrs)])
        if not self.complete:
            lines.append(tx('CIDR 明细已截断；上方全部地址范围与精确总数未截断。请勿把部分 CIDR 当成完整清单。'))
        return jt('\n', lines)


@dataclass(frozen=True)
class AggregateResult:
    input_count: int
    normalized_count: int
    cidrs: tuple
    address_count: int

    def cidr_text(self):
        return jt('\n', map(str, self.cidrs))

    def as_text(self):
        return jt('\n', [tx('IPv6 等价 CIDR 整理报告'), tx('输入网段：{0:,} 条', self.input_count), tx('主机位规范化：{0:,} 条', self.normalized_count), tx('整理后：{0:,} 条', len(self.cidrs)), tx('覆盖地址数（并集）：{0:,}', self.address_count), tx('移除重复与已覆盖子网，仅合并能够精确合并的相邻范围；地址覆盖集合保持不变。'), tx('本结果不保留原始分配层级或业务边界，请确认后再用于规划。'), '', tx('整理后的完整 CIDR：'), self.cidr_text()])


def free_space(text, parent_text, *, stop=None):
    _check_stop(stop)
    parent_result=calculate(parent_text,'128',preview_limit=0)
    parent=parent_result.network
    records=_records(text,stop,allow_empty=True)
    for record in records:
        _check_stop(stop)
        if not record.network.subnet_of(parent):
            raise InputError(tx('第 {0} 行网段 {1} 不完全位于父网段 {2} 内，请修正后再规划。', record.line, record.network, parent))
    occupied=_union(records,stop)
    gaps=[]
    cursor=int(parent.network_address)
    for start,end in occupied:
        _check_stop(stop)
        if cursor<start:
            gaps.append((cursor,start-1))
        cursor=end+1
    if cursor<=int(parent.broadcast_address):
        gaps.append((cursor,int(parent.broadcast_address)))
    details=[];count=0
    for address,prefix in _cidrs(gaps,stop):
        count+=1
        if len(details)<MAX_FREE_DETAILS:
            details.append(IPv6Network((address,prefix)))
    _check_stop(stop)
    return FreeSpaceResult(parent,parent_result.normalized,len(records),sum(r.normalized for r in records),
        sum(end-start+1 for start,end in occupied),tuple(gaps),tuple(details),count)


def aggregate_cidrs(text, *, stop=None):
    records=_records(text,stop)
    intervals=_union(records,stop)
    cidrs=tuple(IPv6Network((address,prefix)) for address,prefix in _cidrs(intervals,stop))
    _check_stop(stop)
    return AggregateResult(len(records),sum(r.normalized for r in records),cidrs,
                           sum(end-start+1 for start,end in intervals))
