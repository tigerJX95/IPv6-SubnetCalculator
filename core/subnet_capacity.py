# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Exact capacity for every prefix using complete free ranges, never previews."""
from dataclasses import dataclass
from ipaddress import IPv6Network
from core.localized_text import text as tx, join_text as jt
from core.subnet_planning import free_space
from core.subnet_allocation import aligned_blocks


@dataclass(frozen=True)
class PrefixCapacity:
    prefix: int
    capacity: int
    fragmented_addresses: int


@dataclass(frozen=True)
class CapacityOverview:
    free: object
    rows: tuple
    largest: object

    def as_text(self):
        lines = [tx('IPv6 空闲容量总览'), tx('父网段：{0}', self.free.parent),
                 tx('占用并集地址数：{0:,}', self.free.occupied_addresses),
                 tx('空闲地址数：{0:,}', self.free.free_addresses),
                 tx('最大可用子网（同等大小取地址最小者）：{0}', self.largest if self.largest is not None else tx('无')),
                 tx('各行是同一空闲空间的不同划分方式，容量不能跨行相加。'),
                 tx('零散地址仍为空闲，但无法组成该前缀下完整且对齐的子网。'),
                 tx('空闲仅指父网段扣除当前清单的数学差集，不证明地址已获分配或可部署。'), '',
                 tx('前缀｜可分配子网数｜零散地址数')]
        lines.extend(tx('/{0}｜{1:,}｜{2:,}', row.prefix, row.capacity, row.fragmented_addresses)
                     for row in self.rows)
        return jt('\n', lines)


def capacity_overview(text, parent):
    free = free_space(text, parent)
    rows, largest = [], None
    for prefix in range(free.parent.prefixlen, 129):
        aligned = aligned_blocks(free.free_ranges, prefix)
        capacity = sum(count for _, count in aligned)
        rows.append(PrefixCapacity(prefix, capacity,
                                  free.free_addresses-capacity*(1 << (128-prefix))))
        if largest is None and aligned:
            largest = IPv6Network((aligned[0][0], prefix))
    return CapacityOverview(free, tuple(rows), largest)
