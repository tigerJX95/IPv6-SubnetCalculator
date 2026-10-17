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

"""独立的 IPv6 子网计算逻辑，不依赖图形界面。"""
from __future__ import annotations

from dataclasses import dataclass
from ipaddress import IPv6Address, IPv6Network, AddressValueError, NetmaskValueError
import re

MAX_PREVIEW = 100


class InputError(ValueError):
    """面向用户的输入校验错误。"""


@dataclass(frozen=True)
class SubnetResult:
    network: IPv6Network
    target_prefix: int
    normalized: bool
    subnet_count: int
    addresses_per_subnet: int
    preview: tuple[IPv6Network, ...]

    @property
    def start_address(self) -> IPv6Address:
        return self.network.network_address

    @property
    def end_address(self) -> IPv6Address:
        return IPv6Address(int(self.network.network_address) + self.network.num_addresses - 1)



def validate_ipv6_address(text: str) -> IPv6Address:
    """校验单个 IPv6 地址，并对常见输入错误给出针对性提示。"""
    value = text.strip()
    if not value:
        raise InputError('请输入 IPv6 地址。')
    if '/' in value:
        raise InputError('IPv6 地址部分不能包含 / 前缀，请只填写地址。')
    if value.count('::') > 1 or ':::' in value:
        raise InputError('IPv6 地址中双冒号 :: 只能出现一次，且不能写成三个连续冒号。')
    if '%' in value:
        raise InputError('请输入不带区域标识（例如 %12）的 IPv6 地址。')
    # 带点分十进制尾部的 IPv4 映射写法属于合法 IPv6 表示形式。
    if '.' in value:
        try:
            return IPv6Address(value)
        except ValueError as exc:
            raise InputError('IPv6 地址中的 IPv4 尾部格式不正确，请检查四段数字（0～255）。') from exc
    if not re.fullmatch(r'[0-9a-fA-F:.]+', value):
        raise InputError('IPv6 地址包含非法字符，请使用 0–9、a–f 和冒号（:）；大写 A–F 会自动转换为小写。')
    if re.search(r'(^:[^:]|[^:]:$)', value):
        raise InputError('IPv6 地址首尾若需压缩零组，必须使用双冒号 ::。')
    try:
        return IPv6Address(value)
    except ValueError as exc:
        groups = value.split(':')
        if any(len(group) > 4 for group in groups if group):
            raise InputError('IPv6 地址每组最多 4 位十六进制字符。') from exc
        if '::' not in value and len(groups) != 8:
            raise InputError('未使用 :: 压缩时，IPv6 地址必须完整填写 8 组。') from exc
        if '::' in value and len([g for g in groups if g]) >= 8:
            raise InputError('使用 :: 时必须至少压缩一组全零地址。') from exc
        raise InputError('IPv6 地址格式不正确，请检查冒号位置及地址组数。') from exc


def normalize_ipv6_input(text: str) -> str:
    """把输入中的 A～F 规范为小写，保留用户填写的完整地址形式。"""
    return text.lower()

def calculate(network_text: str, target_text: str, *, preview_limit: int = MAX_PREVIEW) -> SubnetResult:
    """校验 CIDR 并计算子网信息，不遍历整个 IPv6 地址空间。"""
    source = network_text.strip()
    target = target_text.strip()
    if not source:
        raise InputError("请输入 IPv6 网络地址及前缀，例如 2026:1015:abcd::/48。")
    if source.count("/") != 1:
        raise InputError("网络地址必须包含一个 CIDR 前缀，例如 2026:1015:abcd::/48。")
    addr, prefix = (part.strip() for part in source.split("/"))
    if not addr or not prefix or not re.fullmatch(r"[0-9]{1,3}", prefix):
        raise InputError("原始网络前缀必须为 0～128 的整数。")
    original_prefix = int(prefix)
    if not 0 <= original_prefix <= 128:
        raise InputError("原始网络前缀必须为 0～128 的整数。")
    if not target or not re.fullmatch(r"[0-9]{1,3}", target):
        raise InputError("目标子网前缀必须为 0～128 的整数（不需要输入 /）。")
    target_prefix = int(target)
    if not 0 <= target_prefix <= 128:
        raise InputError("目标子网前缀必须为 0～128 的整数。")
    if target_prefix < original_prefix:
        raise InputError("目标子网前缀不能小于原始网络前缀。")
    ip = validate_ipv6_address(addr)
    net = IPv6Network((ip, original_prefix), strict=False)
    if isinstance(preview_limit, bool) or not isinstance(preview_limit, int) or not 0 <= preview_limit <= MAX_PREVIEW:
        raise ValueError(f"preview_limit must be an integer from 0 to {MAX_PREVIEW}")
    count = 1 << (target_prefix - original_prefix)
    step = 1 << (128 - target_prefix)
    first = int(net.network_address)
    preview = tuple(IPv6Network((IPv6Address(first + i * step), target_prefix)) for i in range(min(count, preview_limit)))
    return SubnetResult(net, target_prefix, ip != net.network_address, count, step, preview)


def locate_subnet(network: IPv6Network, target_prefix: int, address_text: str) -> int:
    """返回指定 IPv6 地址所属子网的一基序号，计算复杂度与子网数量无关。"""
    text = address_text.strip()
    if not text:
        raise InputError('请输入需要定位的 IPv6 地址。')
    address = validate_ipv6_address(text)
    if address not in network:
        raise InputError('该 IPv6 地址不在当前计算的网络范围内。')
    step = 1 << (128 - target_prefix)
    return (int(address) - int(network.network_address)) // step + 1


COMMON_TARGET_PREFIXES = (48, 56, 60, 64, 127, 128)


def common_target_prefixes(original_prefix: int) -> tuple[int, ...]:
    """返回不小于原网络前缀的常用目标前缀。"""
    if isinstance(original_prefix, bool) or not isinstance(original_prefix, int) or not 0 <= original_prefix <= 128:
        raise ValueError('原始网络前缀必须为 0～128 的整数。')
    return tuple(prefix for prefix in COMMON_TARGET_PREFIXES if prefix >= original_prefix)


def prefix_analysis(result: SubnetResult) -> int:
    """返回目标子网前缀相对原网络新增的子网位数。"""
    return result.target_prefix - result.network.prefixlen


def subnet_count_description(result: SubnetResult) -> str:
    """根据划分边界生成不引起误解的子网数量说明。"""
    if result.network.prefixlen == 128:
        return '1（已是单个 IPv6 地址，无法继续划分子网）'
    if result.target_prefix == result.network.prefixlen:
        return '1（未进一步划分，保留原网络）'
    return f'{result.subnet_count:,}'


def subnet_at_index(network: IPv6Network, target_prefix: int, index: int) -> IPv6Network:
    """通过一基序号直接获取目标子网，不枚举此前的网段。"""
    if not network.prefixlen <= target_prefix <= 128:
        raise InputError('目标子网前缀必须介于原网络前缀与 128 之间。')
    total = 1 << (target_prefix - network.prefixlen)
    if isinstance(index, bool) or not isinstance(index, int) or not 1 <= index <= total:
        raise InputError(f'子网序号必须在 1～{total:,} 之间。')
    start = int(network.network_address) + (index - 1) * (1 << (128 - target_prefix))
    return IPv6Network((IPv6Address(start), target_prefix))


def validate_subnet_index(text: str, total: int) -> int:
    """严格校验子网序号，拒绝小数、负数及超出范围的数值。"""
    value = text.strip()
    if not value.isascii() or not value.isdecimal() or len(value) > 40:
        raise InputError('请输入有效的正整数子网序号。')
    index = int(value)
    if not 1 <= index <= total:
        raise InputError(f'子网序号超出范围，请输入 1～{total:,}。')
    return index
