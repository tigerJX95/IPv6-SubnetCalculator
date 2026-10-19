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

"""不依赖界面框架的数字显示及导出格式校验。"""
from core.localized_text import text as tx, join_text as jt
from pathlib import Path


def determine_export_format(path: Path, oversized: bool) -> str:
    suffix = path.suffix.lower()
    if suffix not in ('.xlsx', '.txt'):
        raise ValueError(tx('请选择 Excel（.xlsx）或 TXT（.txt）格式保存。'))
    if oversized and suffix != '.txt':
        raise ValueError(tx('当前子网数量超过 Excel 容量限制，只能导出 TXT（.txt）。'))
    return suffix[1:]


def compact_count(number: int) -> str:
    if number >= 10**20:
        exponent = len(str(number)) - 1
        divisor = 10**exponent
        scaled = (number * 100 + divisor // 2) // divisor
        return tx('{0}.{1:02d}×10^{2}', scaled // 100, scaled % 100, exponent)
    for unit, divisor in ((tx('京'), 10**16), (tx('万亿'), 10**12), (tx('亿'), 10**8)):
        if number >= divisor:
            scaled = (number * 100 + divisor // 2) // divisor
            whole, fractional = divmod(scaled, 100)
            return (str(whole) if fractional == 0 else tx('{0}.{1:02d}', whole, fractional)) + unit
    return tx('{0:,}', number)
