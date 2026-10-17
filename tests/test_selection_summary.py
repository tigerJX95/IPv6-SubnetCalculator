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
from core.subnet_tools import summarize_selection

class SelectionSummaryTests(unittest.TestCase):

    def test_empty_selection(self):
        stats = summarize_selection([], range(1, 101), 2 ** 64)
        self.assertEqual((stats.count, stats.first, stats.last, stats.address_count), (0, None, None, 0))
        self.assertFalse(stats.contiguous)

    def test_single_subnet(self):
        stats = summarize_selection([5], range(1, 26), 2 ** 64)
        self.assertEqual((stats.count, stats.first, stats.last, stats.address_count), (1, 5, 5, 2 ** 64))
        self.assertTrue(stats.contiguous)

    def test_contiguous_unsorted_duplicates(self):
        stats = summarize_selection([6, 4, 5, 4], range(1, 26), 16)
        self.assertTrue(stats.contiguous)
        self.assertEqual((stats.count, stats.first, stats.last, stats.address_count), (3, 4, 6, 48))

    def test_non_contiguous_capacity_excludes_gaps(self):
        stats = summarize_selection([1, 100], range(1, 101), 2 ** 64)
        self.assertFalse(stats.contiguous)
        self.assertEqual(stats.address_count, 2 * 2 ** 64)

    def test_out_of_page_selection_is_excluded(self):
        stats = summarize_selection([1, 101, 120], range(101, 126), 1)
        self.assertEqual((stats.count, stats.first, stats.last), (2, 101, 120))

    def test_range_total_is_distinct_from_page_matches(self):
        stats = summarize_selection([90], range(1, 101), 1, (90, 210))
        self.assertEqual((stats.count, stats.highlighted_on_page, stats.highlighted_total), (1, 11, 121))

    def test_last_page_partial_range(self):
        stats = summarize_selection([], range(201, 218), 1, (90, 210))
        self.assertEqual((stats.highlighted_on_page, stats.highlighted_total), (10, 121))

    def test_maximum_ipv6_range_uses_bounded_page(self):
        total = 2 ** 128
        stats = summarize_selection([total], range(total - 15, total + 1), 1, (1, total))
        self.assertEqual((stats.highlighted_on_page, stats.highlighted_total), (16, total))
        self.assertEqual((stats.first, stats.address_count), (total, 1))

    def test_entire_space_address_capacity_is_exact(self):
        self.assertEqual(summarize_selection([1], [1], 2 ** 128).address_count, 2 ** 128)
