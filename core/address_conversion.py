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

"""单个 IPv6 地址的无损格式转换。"""
from dataclasses import dataclass
from core.ipv6_core import validate_ipv6_address


@dataclass(frozen=True)
class AddressFormats:
    compressed: str
    expanded: str
    binary: str

    @property
    def normalized(self):
        return self.compressed

    def as_text(self):
        return '\n'.join(('IPv6 地址格式转换', f'压缩 / 规范化：{self.normalized}',
                          f'完整展开：{self.expanded}', f'二进制（128 位）：{self.binary}'))


def convert_address(text: str) -> AddressFormats:
    address = validate_ipv6_address(text)
    # 明确输出 8 组十六进制，避免不同 Python 版本对 IPv4 映射尾部的显示差异。
    hexadecimal = f'{int(address):032x}'
    expanded = ':'.join(hexadecimal[index:index+4] for index in range(0, 32, 4))
    return AddressFormats(address.compressed, expanded, f'{int(address):0128b}')
