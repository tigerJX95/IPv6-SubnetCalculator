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

"""独立结果窗口与当前页统计的专项测试。"""
import unittest
from pathlib import Path
from core.subnet_tools import visible_selection_counts


class TestV05(unittest.TestCase):
    def test_no_selection(self):
        self.assertEqual(visible_selection_counts([], range(1, 101)), (0, 0))

    def test_selected_vs_range(self):
        self.assertEqual(visible_selection_counts([30, 31, 900], range(1, 101), (25, 40)),
                         (2, 16))

    def test_out_of_page_range(self):
        self.assertEqual(visible_selection_counts([2], range(101, 201), (1, 100)), (0, 0))

    def test_huge_range_constant_page(self):
        self.assertEqual(visible_selection_counts([], range(201, 301), (1, 10**30)), (0, 100))

    def test_one_matching_row(self):
        self.assertEqual(visible_selection_counts([5], range(1, 26), (5, 5)), (1, 1))



if __name__ == '__main__':
    unittest.main()
