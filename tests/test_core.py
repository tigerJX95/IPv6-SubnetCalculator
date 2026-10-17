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

import ipaddress
import unittest
from core.ipv6_core import calculate, InputError


class CalculatorTests(unittest.TestCase):
    def test_reference_48_to_64(self):
        r = calculate("2026:1015:abcd::/48", "64")
        self.assertEqual(str(r.start_address), "2026:1015:abcd::")
        self.assertEqual(str(r.end_address), "2026:1015:abcd:ffff:ffff:ffff:ffff:ffff")
        self.assertEqual(r.subnet_count, 65536)
        self.assertEqual(r.addresses_per_subnet, 2**64)
        self.assertEqual(str(r.preview[0]), "2026:1015:abcd::/64")
        self.assertEqual(str(r.preview[1]), "2026:1015:abcd:1::/64")
        self.assertEqual(len(r.preview), 100)

    def test_same_prefix(self):
        r = calculate("2026:1015:abcd::/64", "64")
        self.assertEqual(r.subnet_count, 1)
        self.assertEqual(str(r.preview[0]), "2026:1015:abcd::/64")

    def test_normalized_input(self):
        r = calculate("2026:1015:ABCD:5678::1/48", "64")
        self.assertTrue(r.normalized)
        self.assertEqual(str(r.network), "2026:1015:abcd::/48")

    def test_small_subnets(self):
        r = calculate("2026:1015:abcd::/126", "128")
        self.assertEqual([str(x) for x in r.preview], [
            "2026:1015:abcd::/128", "2026:1015:abcd::1/128", "2026:1015:abcd::2/128", "2026:1015:abcd::3/128"])

    def test_all_space(self):
        r = calculate("::/0", "128")
        self.assertEqual(r.subnet_count, 2**128)
        self.assertEqual(r.addresses_per_subnet, 1)
        self.assertEqual(str(r.end_address), "ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff")
        self.assertEqual(len(r.preview), 100)

    def test_boundary_128(self):
        r = calculate("ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128", "128")
        self.assertEqual(r.start_address, r.end_address)
        self.assertEqual(r.subnet_count, 1)

    def test_prefix_examples(self):
        for src, target, expected in [("2026:1015:abcd::/48", "64", 65536),
                                      ("2026:1015:abcd::/64", "65", 2),
                                      ("2026:1015:abcd::/56", "64", 256)]:
            with self.subTest(src=src, target=target):
                self.assertEqual(calculate(src, target).subnet_count, expected)

    def test_all_small_results_match_stdlib(self):
        for initial, target in [("2026:1015:abcd::/124", 128), ("fd12::/120", 123), ("::/125", 127)]:
            r = calculate(initial, str(target))
            expected = list(ipaddress.IPv6Network(initial).subnets(new_prefix=target))
            self.assertEqual(list(r.preview), expected)

    def test_bad_input(self):
        invalid = [("", "64"), ("2026:1015:abcd::", "64"), ("2026:1015:abcd::/129", "129"),
                   ("gggg::/64", "64"), ("2026:1015:abcd::/64", "63"),
                   ("2026:1015:abcd::/64", "abc"), ("2026:1015:abcd::/64", "-1"),
                   ("2026:1015:abcd::/64", "129"), ("2001:::db8/64", "64"),
                   ("2026:1015:abcd::/64/65", "65"), ("2026:1015:abcd::/64", "")]
        for a, b in invalid:
            with self.subTest(a=a, b=b), self.assertRaises(InputError):
                calculate(a, b)

    def test_preview_limits(self):
        self.assertEqual(len(calculate("::/0", "128", preview_limit=0).preview), 0)
        self.assertEqual(len(calculate("::/0", "128", preview_limit=8).preview), 8)
        with self.assertRaises(ValueError):
            calculate("::/0", "128", preview_limit=101)


if __name__ == "__main__":
    unittest.main()
