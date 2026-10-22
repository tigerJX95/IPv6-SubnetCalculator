# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Address membership and exact coverage comparison, without address enumeration."""
from dataclasses import dataclass
from ipaddress import IPv6Address
from core.localized_text import text as tx, join_text as jt
from core.ipv6_core import validate_ipv6_address
from core.subnet_planning import _records, _union


def difference(first, second):
    """Subtract sorted disjoint inclusive intervals in linear time."""
    result = []
    j = 0
    for start, end in first:
        while j < len(second) and second[j][1] < start:
            j += 1
        cursor, k = start, j
        while k < len(second) and second[k][0] <= end:
            left, right = second[k]
            if cursor < left:
                result.append((cursor, left - 1))
            cursor = max(cursor, right + 1)
            if cursor > end:
                break
            k += 1
        if cursor <= end:
            result.append((cursor, end))
        j = k
    return tuple(result)


def size(ranges):
    return sum(end - start + 1 for start, end in ranges)


def range_lines(ranges):
    return [tx('{0} ～ {1}｜{2:,} 个地址', IPv6Address(start), IPv6Address(end), end-start+1)
            for start, end in ranges] or [tx('无')]


@dataclass(frozen=True)
class Membership:
    address: IPv6Address
    matches: tuple

    def as_text(self):
        lines = [tx('IPv6 地址归属查询'), tx('查询地址：{0}', self.address),
                 tx('匹配网段：{0:,} 条（保留重复及包含项）', len(self.matches)),
                 tx('按最长前缀优先显示；原始行号包含空行和注释。')]
        lines.extend(tx('第 {0} 行：{1} → {2}', r.line, r.original, r.network) for r in self.matches)
        if not self.matches:
            lines.append(tx('当前清单中没有包含此地址的网段。'))
        lines.append(tx('归属仅根据当前清单判断，不代表实际分配或网络可达性。'))
        return jt('\n', lines)


def lookup_address(text, query):
    address = validate_ipv6_address(query)
    records = _records(text, None, allow_empty=True)
    matches = tuple(sorted((r for r in records if address in r.network),
                           key=lambda r: (-r.network.prefixlen, r.line)))
    return Membership(address, matches)


@dataclass(frozen=True)
class CoverageComparison:
    baseline: tuple
    candidate: tuple
    added: tuple
    removed: tuple
    common: tuple

    def as_text(self):
        lines = [tx('IPv6 清单覆盖差异报告'),
                 tx('基准：当前清单快照；对比：输入或导入的清单。'),
                 tx('基准覆盖地址数：{0:,}', size(self.baseline)),
                 tx('对比覆盖地址数：{0:,}', size(self.candidate)),
                 tx('新增地址数：{0:,}', size(self.added)),
                 tx('移除地址数：{0:,}', size(self.removed)),
                 tx('共同覆盖地址数：{0:,}', size(self.common)),
                 tx('覆盖相同：{0}', tx('是') if not self.added and not self.removed else tx('否')),
                 tx('重复、包含或等价 CIDR 拆分不计为覆盖变化；以下范围均包含首末地址。')]
        for heading, ranges in [(tx('新增覆盖范围：'), self.added),
                                (tx('移除覆盖范围：'), self.removed),
                                (tx('共同覆盖范围：'), self.common)]:
            lines.extend(['', heading, *range_lines(ranges)])
        return jt('\n', lines)


def compare_coverage(baseline, candidate):
    first = _union(_records(baseline, None, allow_empty=True), None)
    second = _union(_records(candidate, None, allow_empty=True), None)
    added, removed = difference(second, first), difference(first, second)
    return CoverageComparison(first, second, added, removed, difference(first, removed))
