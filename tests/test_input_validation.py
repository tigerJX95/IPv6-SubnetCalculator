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

import unittest
from core.ipv6_core import calculate, locate_subnet, validate_ipv6_address, normalize_ipv6_input, InputError


class InputValidationTests(unittest.TestCase):
    def test_uppercase_input_is_valid_and_normalizable(self):
        self.assertEqual(normalize_ipv6_input('2026:1015:ABCD::/48'), '2026:1015:abcd::/48')
        self.assertEqual(str(calculate('2026:1015:ABCD::/48', '64').network), '2026:1015:abcd::/48')

    def test_duplicate_compression(self):
        for address in ('2001::abcd::1', '2001:::1'):
            with self.subTest(address=address), self.assertRaisesRegex(InputError, '双冒号'):
                validate_ipv6_address(address)

    def test_illegal_character(self):
        with self.assertRaisesRegex(InputError, '非法字符.*0–9、a–f'):
            calculate('2026:1015:gggg::/48', '64')

    def test_hextet_too_long(self):
        with self.assertRaisesRegex(InputError, '最多 4 位'):
            validate_ipv6_address('12345::1')

    def test_missing_groups(self):
        with self.assertRaisesRegex(InputError, '8 组'):
            validate_ipv6_address('2001:db8:1:2')

    def test_prefix_errors(self):
        for prefix in ('129', '-1', 'abc'):
            with self.subTest(prefix=prefix), self.assertRaisesRegex(InputError, '0～128'):
                calculate('2026:1015:abcd::/' + prefix, '64')

    def test_ipv4_mapped_not_regressed(self):
        from ipaddress import IPv4Address, IPv6Address
        address = validate_ipv6_address('::ffff:192.0.2.1')
        self.assertEqual(address, IPv6Address('::ffff:c000:201'))
        self.assertEqual(address.ipv4_mapped, IPv4Address('192.0.2.1'))

    def test_location_validates(self):
        r = calculate('2026:1015:abcd::/48', '64')
        with self.assertRaisesRegex(InputError, '双冒号'):
            locate_subnet(r.network, 64, '2026::abcd::1')
        self.assertEqual(locate_subnet(r.network, 64, '2026:1015:ABCD::1'), 1)

    def test_normalizer_preserves_compression(self):
        self.assertEqual(normalize_ipv6_input('FD00:ABCD::1'), 'fd00:abcd::1')
