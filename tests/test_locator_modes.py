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

"""统一定位入口的单项与区间边界测试。"""
import unittest
from ipaddress import IPv6Network
from core.ipv6_core import InputError
from core.subnet_tools import LOCATOR_MODES, resolve_locator_range


class LocatorModesTests(unittest.TestCase):
    def setUp(self):
        self.network = IPv6Network('2026:1015:abcd::/48')

    def resolve(self, mode, text, network=None, prefix=64):
        return resolve_locator_range(mode, text, network or self.network, prefix)

    def test_mode_names(self):
        self.assertEqual(len(LOCATOR_MODES), 4)

    def test_single_address(self):
        self.assertEqual(self.resolve('按 IPv6 地址', '2026:1015:ABCD:2::9'), (3, 3))

    def test_single_index(self):
        self.assertEqual(self.resolve('按子网序号', '50000'), (50000, 50000))

    def test_index_range(self):
        self.assertEqual(self.resolve('按子网序号范围', '1000-1500'), (1000, 1500))

    def test_address_range(self):
        self.assertEqual(self.resolve('按 IPv6 地址范围', '2026:1015:abcd:1::1 - 2026:1015:abcd:3::1'), (2, 4))

    def test_address_range_same_subnet(self):
        self.assertEqual(self.resolve('按 IPv6 地址范围', '2026:1015:abcd::1～2026:1015:abcd::ffff'), (1, 1))

    def test_index_range_extremely_large(self):
        n = IPv6Network('::/0')
        self.assertEqual(self.resolve('按子网序号范围', f'{2**128 - 1}-{2**128}', n, 128), (2**128 - 1, 2**128))

    def test_bad_values(self):
        cases = [
            ('按子网序号范围', '0-100'),
            ('按子网序号范围', '1500-1000'),
            ('按子网序号范围', '1000'),
            ('按 IPv6 地址范围', '2026:1015:abcd:3::1 - 2026:1015:abcd:1::1'),
            ('按 IPv6 地址范围', '2026:1015:abcd:1::2 - 2026:1015:abcd:1::1'),
            ('按 IPv6 地址范围', '2001:db8::1 - 2026:1015:abcd::1'),
            ('未知方式', '1'),
            ('按 IPv6 地址', ''),
        ]
        for mode, value in cases:
            with self.subTest(mode=mode, value=value), self.assertRaises(InputError):
                self.resolve(mode, value)
