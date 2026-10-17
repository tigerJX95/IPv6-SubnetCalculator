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
from ipaddress import IPv6Network
from core.export_estimate import estimate_export_range, format_size_range

class EstimateTests(unittest.TestCase):
    def test_txt_range_contains_actual_small_file(self):
        n=IPv6Network('2026:1015:abcd::/120')
        low, high=estimate_export_range(n,128,'txt',256)
        actual=sum(len(str(x).encode('utf-8'))+1 for x in n.subnets(new_prefix=128))
        self.assertLessEqual(low,actual)
        self.assertGreaterEqual(high,actual)

    def test_huge_count_is_fast_and_bounded(self):
        n=IPv6Network('2026:1015:abcd::/48')
        low,high=estimate_export_range(n,80,'txt',2**32)
        self.assertLess(low,high)
        self.assertGreater(high,2**32*10)

    def test_xlsx_range(self):
        n=IPv6Network('2026:1015:abcd::/120')
        low,high=estimate_export_range(n,128,'xlsx',256)
        self.assertLess(low,high)

    def test_units(self):
        self.assertIn('MiB',format_size_range(0,1000000))
        self.assertIn('GiB',format_size_range(2**30,2**31))
