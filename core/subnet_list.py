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

"""IPv6 清单校验与关系统计；仅处理网段边界，不枚举地址。"""
from core.localized_text import text as tx, join_text as jt
from dataclasses import dataclass
from collections import defaultdict
from core.ipv6_core import calculate, InputError

MAX_LIST_BYTES = 1024 * 1024
MAX_LIST_RECORDS = 5000
MAX_LIST_LINES = 20000
MAX_RELATION_DETAILS = 1000


class ListCheckCancelled(Exception):
    """用户取消后台检查。"""


def _check_stop(stop):
    if stop is not None and stop.is_set():
        raise ListCheckCancelled()


@dataclass(frozen=True)
class ListRecord:
    line: int
    original: str
    network: object = None
    normalized: bool = False
    error: str = ''


@dataclass(frozen=True)
class ListRelation:
    first: int
    second: int
    kind: str

    @property
    def description(self):
        return {'duplicate': tx('重复网段'), 'contains': tx('前者包含后者'),
                'adjacent': tx('相邻（无重叠）')}[self.kind]


@dataclass(frozen=True)
class ListAnalysis:
    records: tuple
    relations: tuple
    duplicate_pairs: int
    containment_pairs: int
    adjacent_pairs: int
    unique_networks: tuple

    @property
    def valid_count(self):
        return sum(record.network is not None for record in self.records)

    @property
    def error_count(self):
        return len(self.records)-self.valid_count

    @property
    def relation_count(self):
        return self.duplicate_pairs+self.containment_pairs+self.adjacent_pairs

    def normalized_text(self):
        return jt('\n', (str(network) for network in self.unique_networks))

    def as_text(self):
        lines = [tx('IPv6 子网清单检查报告'),
            tx('有效网段：{0:,}；错误行：{1:,}；去重后：{2:,}', self.valid_count, self.error_count, len(self.unique_networks)),
            tx('重复关系：{0:,} 对；包含关系：{1:,} 对；相邻关系：{2:,} 对', self.duplicate_pairs, self.containment_pairs, self.adjacent_pairs),
            tx('重叠关系（重复＋包含）：{0:,} 对', self.duplicate_pairs + self.containment_pairs),
            tx('关系明细：{0:,} / {1:,} 对（最多 {2:,} 对）', len(self.relations), self.relation_count, MAX_RELATION_DETAILS),
            tx('关系只统计有效网段；错误行不参与分析。原始行号包含空行和注释行。'),
            tx('相邻不代表一定能合并为一个 CIDR；本报告不证明地址分配权或实际可达性。'),
            tx('去重仅移除相同网段，不移除包含的子网，也不合并相邻网段。'), '', tx('网段校验：')]
        for record in self.records:
            if record.error:
                lines.append(tx('第 {0} 行：{1}｜错误：{2}', record.line, record.original, record.error))
            else:
                lines.append(tx('第 {0} 行：{1} → {2}｜', record.line, record.original, record.network)+
                             (tx('主机位已规范化') if record.normalized else tx('有效')))
        lines.extend(('', tx('关系明细：')))
        lines.extend(tx('第 {0} 行 / 第 {1} 行：{2}', item.first, item.second, item.description) for item in self.relations)
        if self.relation_count > len(self.relations):
            lines.append(tx('关系明细已截断；上方统计仍为精确总数。'))
        return jt('\n', lines)


def validate_list_text(text, *, allow_empty=False):
    if not isinstance(text, str):
        raise InputError(tx('清单内容必须是文本。'))
    try:
        size = len(text.encode('utf-8'))
    except UnicodeError as exc:
        raise InputError(tx('清单包含无效的 Unicode 字符。')) from exc
    if size > MAX_LIST_BYTES:
        raise InputError(tx('清单不能超过 1 MiB，请拆分后检查。'))
    if '\x00' in text:
        raise InputError(tx('清单包含空字符，请使用 UTF-8 纯文本文件。'))
    lines = text.removeprefix('\ufeff').splitlines()
    if len(lines) > MAX_LIST_LINES:
        raise InputError(tx('清单不能超过 {0:,} 个物理行。', MAX_LIST_LINES))
    entries = [(line, value.strip()) for line, value in enumerate(lines, 1)
               if value.strip() and not value.lstrip().startswith('#')]
    if not entries and not allow_empty:
        raise InputError(tx('请输入每行一个 IPv6 CIDR；空行和以 # 开头的注释会被忽略。'))
    if len(entries) > MAX_LIST_RECORDS:
        raise InputError(tx('每次最多检查 {0:,} 条网段，请拆分清单。', MAX_LIST_RECORDS))
    return entries


def parse_subnet_records(text, *, stop=None, allow_empty=False):
    _check_stop(stop)
    records = []
    for line, value in validate_list_text(text, allow_empty=allow_empty):
        _check_stop(stop)
        try:
            if len(value) > 200:
                raise InputError(tx('单条网段不能超过 200 个字符。'))
            result = calculate(value, '128', preview_limit=0)
            record = ListRecord(line, value, result.network, result.normalized)
        except InputError as exc:
            record = ListRecord(line, value, error=str(exc))
        records.append(record)
    return tuple(records)


def analyze_subnet_list(text, *, stop=None):
    records = parse_subnet_records(text, stop=stop)
    groups = defaultdict(list)
    for record in records:
        if record.network is not None:
            groups[record.network].append(record.line)
    details = []
    counts = dict(duplicate=0, contains=0, adjacent=0)

    def add(kind, first, second, same=False):
        counts[kind] += len(first)*(len(first)-1)//2 if same else len(first)*len(second)
        if len(details) >= MAX_RELATION_DETAILS:
            return
        for i, left in enumerate(first):
            _check_stop(stop)
            for right in second[i+1:] if same else second:
                details.append(ListRelation(left, right, kind))
                if len(details) >= MAX_RELATION_DETAILS:
                    return

    ordered = sorted(groups, key=lambda net: (int(net.network_address), net.prefixlen))
    ancestors = []
    starts = {int(net.network_address): [] for net in ordered}
    for net in ordered:
        starts[int(net.network_address)].append(net)
    # 优先列出重复和包含明细，再列出相邻；总数始终精确。
    for net in ordered:
        _check_stop(stop)
        rows = groups[net]
        if len(rows)>1:
            add('duplicate', rows, rows, same=True)
    for net in ordered:
        _check_stop(stop)
        start = int(net.network_address)
        while ancestors and int(ancestors[-1].broadcast_address) < start:
            ancestors.pop()
        for parent in ancestors:
            add('contains', groups[parent], groups[net])
        ancestors.append(net)
    for net in ordered:
        _check_stop(stop)
        next_start = int(net.broadcast_address)+1
        for right in starts.get(next_start, ()):
            add('adjacent', groups[net], groups[right])
    _check_stop(stop)
    return ListAnalysis(tuple(records), tuple(details), counts['duplicate'], counts['contains'],
                        counts['adjacent'], tuple(groups))
