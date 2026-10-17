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

"""V0.4 新增范围复制及详情相邻导航测试。"""
import unittest
from ipaddress import IPv6Network
from core.ipv6_core import InputError
from core.subnet_tools import MAX_COPY_RECORDS, adjacent_subnet_index, subnet_range_text, validate_copy_range

class ExtraFunctionsTest(unittest.TestCase):
    def setUp(self):
        self.net = IPv6Network('2026:1015:abcd::/48')

    def test_copy_single(self):
        self.assertEqual(subnet_range_text(self.net, 64, 2, 2), '2\t2026:1015:abcd:1::/64')

    def test_copy_range(self):
        self.assertEqual(subnet_range_text(self.net, 64, 1, 3).count('\n'), 2)

    def test_copy_last(self):
        self.assertIn('ffff::/64', subnet_range_text(self.net, 64, 65536, 65536))

    def test_validate_copy_range(self):
        self.assertEqual(validate_copy_range('2', '5', 65536), (2, 5))

    def test_copy_limit(self):
        with self.assertRaises(InputError):
            validate_copy_range('1', str(MAX_COPY_RECORDS + 1), 65536)

    def test_copy_invalid_bounds(self):
        for start, end in [('5','2'), ('0','1'), ('1','65537'), ('abc','2')]:
            with self.subTest(start=start, end=end), self.assertRaises(InputError):
                validate_copy_range(start, end, 65536)

    def test_no_unbounded_copy(self):
        with self.assertRaises(InputError):
            subnet_range_text(self.net, 64, 1, MAX_COPY_RECORDS + 1)

    def test_adjacent(self):
        self.assertEqual(adjacent_subnet_index(2, 10, -1), 1)
        self.assertEqual(adjacent_subnet_index(2, 10, 1), 3)

    def test_adjacent_boundaries(self):
        self.assertEqual(adjacent_subnet_index(1, 10, -1), 1)
        self.assertEqual(adjacent_subnet_index(10, 10, 1), 10)

    def test_adjacent_huge(self):
        self.assertEqual(adjacent_subnet_index(2**128-1, 2**128, 1), 2**128)

    def test_adjacent_invalid(self):
        with self.assertRaises(InputError):
            adjacent_subnet_index(1, 10, 0)
