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

"""V0.4 子网详情与序号定位边界测试。"""
import unittest
from ipaddress import IPv6Network
from core.ipv6_core import InputError, subnet_at_index, validate_subnet_index


class SubnetDetailAndIndexTest(unittest.TestCase):
    def setUp(self):
        self.network = IPv6Network('2026:1015:abcd::/48')

    def test_first_subnet(self):
        self.assertEqual(str(subnet_at_index(self.network, 64, 1)), '2026:1015:abcd::/64')

    def test_second_subnet(self):
        self.assertEqual(str(subnet_at_index(self.network, 64, 2)), '2026:1015:abcd:1::/64')

    def test_last_subnet(self):
        self.assertEqual(str(subnet_at_index(self.network, 64, 65536)), '2026:1015:abcd:ffff::/64')

    def test_same_prefix(self):
        self.assertEqual(subnet_at_index(self.network, 48, 1), self.network)

    def test_127_to_128(self):
        net = IPv6Network('::/127')
        self.assertEqual(str(subnet_at_index(net, 128, 2)), '::1/128')

    def test_128_boundary(self):
        self.assertEqual(str(subnet_at_index(IPv6Network('::1/128'), 128, 1)), '::1/128')

    def test_massive_index_without_enumeration(self):
        net = IPv6Network('::/0')
        self.assertEqual(str(subnet_at_index(net, 128, 2**128)), 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128')

    def test_out_of_bounds(self):
        for bad in (0, -1, 65537, True, 1.0):
            with self.subTest(bad=bad), self.assertRaises(InputError):
                subnet_at_index(self.network, 64, bad)

    def test_invalid_prefix(self):
        for bad in (47, 129):
            with self.subTest(bad=bad), self.assertRaises(InputError):
                subnet_at_index(self.network, bad, 1)

    def test_index_validation(self):
        self.assertEqual(validate_subnet_index(' 65 ', 65536), 65)
        self.assertEqual(validate_subnet_index(str(2**128), 2**128), 2**128)

    def test_index_validation_failure(self):
        for bad in ('', '0', '-1', '1.5', 'abc', '６', '65537', '1,000'):
            with self.subTest(bad=bad), self.assertRaises(InputError):
                validate_subnet_index(bad, 65536)
