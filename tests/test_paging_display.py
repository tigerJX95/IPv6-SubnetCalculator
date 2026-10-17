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

"""超大分页统计的紧凑显示专项测试。"""
import unittest
from core.formatting import compact_count

class PagingDisplayTests(unittest.TestCase):
    def test_normal_count_is_exact(self):
        self.assertEqual(compact_count(656), '656')
        self.assertEqual(compact_count(12345), '12,345')

    def test_large_count_is_compact(self):
        self.assertEqual(compact_count(123456789), '1.23亿')
        self.assertEqual(compact_count(180143985094820), '180.14万亿')
        self.assertEqual(compact_count(18014398509481984), '1.80京')

    def test_extreme_ipv6_number_uses_scientific(self):
        summary = compact_count(2**128)
        self.assertIn('×10^38', summary)
        self.assertLess(len(summary), 16)

if __name__ == '__main__':
    unittest.main()
