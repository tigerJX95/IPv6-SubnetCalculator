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

"""子网导出磁盘占用的参考区间，并非容量保证。"""
from __future__ import annotations
from core.localized_text import text as tx, join_text as jt
from ipaddress import IPv6Network
from .subnet_export import subnet_at
from .ipv6_core import validate_subnet_parameters

GIB = 1024 ** 3
MIB = 1024 ** 2


def estimate_export_range(network: IPv6Network, prefix: int, fmt: str, count: int, start_index: int = 0) -> tuple[int, int]:
    """在子网序号范围内分布采样，返回近似容量区间。"""
    validate_subnet_parameters(network, prefix)
    total = 1 << (prefix-network.prefixlen)
    if (isinstance(count, bool) or isinstance(start_index, bool) or
            not isinstance(count, int) or not isinstance(start_index, int) or
            count <= 0 or start_index < 0 or start_index+count > total or fmt not in ('txt', 'xlsx')):
        raise ValueError(tx('导出估算参数无效'))
    sample_count = min(128, count)
    indices = {(i * (count - 1)) // max(sample_count - 1, 1) for i in range(sample_count)}
    lengths = [len(str(subnet_at(network, prefix, start_index + i)).encode('utf-8')) + 2 for i in indices]
    average = sum(lengths) / len(lengths)
    if fmt == 'txt':
        # Windows 导出采用 UTF-8 编码和换行符，同时预留余量以应对
        # 不同地址段压缩形式造成的长度变化。
        lower = int(count * average * 0.8)
        upper = int(count * average * 1.3) + 1024
    else:
        # XLSX 使用压缩的 XML 内容，压缩比例受数据影响。
        # 采用较宽的区间，避免将压缩后容量误认为精确值。
        raw = count * (average + 105)
        lower = int(raw * 0.2)
        upper = int(raw * 1.1) + 65536
    return max(0, lower), max(lower, upper)


def format_size_range(low: int, high: int) -> str:
    unit, divisor = ('GiB', GIB) if high >= GIB else ('MiB', MIB)
    return tx('{0:,.2f}～{1:,.2f} {2}', low / divisor, high / divisor, unit)
