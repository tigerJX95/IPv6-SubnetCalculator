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

"""子网范围复制与详情导航的独立计算逻辑。"""
from ipaddress import IPv6Network
from dataclasses import dataclass
from .ipv6_core import InputError, subnet_at_index, validate_subnet_index

MAX_COPY_RECORDS = 5000


def validate_copy_range(start_text: str, end_text: str, total: int) -> tuple[int, int]:
    """校验一基闭区间，限制剪贴板一次写入数量，避免界面卡顿。"""
    first = validate_subnet_index(start_text, total)
    last = validate_subnet_index(end_text, total)
    if last < first:
        raise InputError('结束序号不能小于起始序号。')
    if last - first + 1 > MAX_COPY_RECORDS:
        raise InputError(f'单次最多复制 {MAX_COPY_RECORDS:,} 条子网；更多记录请使用文件导出。')
    return first, last


def subnet_range_text(network: IPv6Network, prefix: int, start: int, end: int) -> str:
    """仅生成指定闭区间内的子网文本，不遍历此前的网段。"""
    total = 1 << (prefix - network.prefixlen)
    if not 1 <= start <= end <= total or end - start + 1 > MAX_COPY_RECORDS:
        raise InputError('子网序号范围无效，或超过单次复制上限。')
    return '\n'.join(f'{i}\t{subnet_at_index(network, prefix, i)}' for i in range(start, end + 1))


def adjacent_subnet_index(index: int, total: int, direction: int) -> int:
    """获取相邻子网序号，边界保持不变。"""
    if not 1 <= index <= total or direction not in (-1, 1):
        raise InputError('子网序号或浏览方向无效。')
    return max(1, min(total, index + direction))


# 单一定位入口使用的四种方式，内部范围统一为包含起止序号的闭区间。
LOCATOR_MODES = ('按 IPv6 地址', '按子网序号', '按 IPv6 地址范围', '按子网序号范围')


def resolve_locator_range(mode: str, value: str, network: IPv6Network, prefix: int) -> tuple[int, int]:
    """直接计算指定地址或序号所覆盖的子网范围，不逐条遍历。"""
    from .ipv6_core import locate_subnet
    total = 1 << (prefix - network.prefixlen)
    value = value.strip()
    if not value:
        raise InputError('请输入需要定位的地址、子网序号或范围。')
    if mode == '按 IPv6 地址':
        first = locate_subnet(network, prefix, value)
        return first, first
    if mode == '按子网序号':
        first = validate_subnet_index(value, total)
        return first, first
    if mode not in ('按 IPv6 地址范围', '按子网序号范围'):
        raise InputError('请选择有效的定位方式。')
    import re
    parts = re.split(r'\s*(?:-|～|~|至)\s*', value)
    if len(parts) != 2 or not all(parts):
        example = '1000-1500' if mode == '按子网序号范围' else '2026:1015:abcd::1 - 2026:1015:abcd:2::1'
        raise InputError(f'请输入包含起止两端的范围，例如：{example}')
    if mode == '按子网序号范围':
        first, last = (validate_subnet_index(part, total) for part in parts)
    else:
        first, last = (locate_subnet(network, prefix, part) for part in parts)
        # IPv6 地址范围不能逆序，包括位于同一子网的地址。
        from .ipv6_core import validate_ipv6_address
        if int(validate_ipv6_address(parts[0])) > int(validate_ipv6_address(parts[1])):
            raise InputError('起始 IPv6 地址不能大于结束 IPv6 地址。')
    if first > last:
        raise InputError('起始子网序号不能大于结束序号。')
    return first, last


def visible_selection_counts(selected_indices, visible_indices, highlighted_range=None):
    """分别统计当前页选中条数和定位范围命中条数，不枚举完整范围。"""
    visible = set(visible_indices)
    selected = len(visible.intersection(selected_indices))
    highlighted = (sum(1 for n in visible if highlighted_range[0] <= n <= highlighted_range[1])
                   if highlighted_range is not None else 0)
    return selected, highlighted


@dataclass(frozen=True)
class SelectionSummary:
    count: int
    first: int | None
    last: int | None
    contiguous: bool
    address_count: int
    highlighted_on_page: int
    highlighted_total: int


def summarize_selection(selected_indices, visible_indices, addresses_per_subnet: int,
                        highlighted_range=None) -> SelectionSummary:
    """仅处理当前页的行；全量范围数量使用整数运算，不枚举跨页范围。

    非连续选择的容量只累计实际选中子网，不将序号跨度中的空隙计入。
    """
    visible = set(visible_indices)
    selected = sorted(visible.intersection(selected_indices))
    count, highlighted = visible_selection_counts(selected, visible, highlighted_range)
    first, last = (selected[0], selected[-1]) if selected else (None, None)
    return SelectionSummary(
        count, first, last, bool(count and last - first + 1 == count),
        count * addresses_per_subnet, highlighted,
        highlighted_range[1] - highlighted_range[0] + 1 if highlighted_range else 0,
    )
