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

"""计算摘要的精度、规范化及容量边界。"""
import unittest
from core.ipv6_core import calculate
from core.calculation_summary import format_calculation_summary


class CalculationSummaryTests(unittest.TestCase):
    def test_default_summary_is_complete_and_document_ready(self):
        text = format_calculation_summary(calculate('2026:1015:abcd::/48', '64', preview_limit=0))
        for line in ('网络地址：2026:1015:abcd::/48', '源网络前缀：/48', '目标子网前缀：/64',
                     '网络起始地址：2026:1015:abcd::',
                     '网络结束地址：2026:1015:abcd:ffff:ffff:ffff:ffff:ffff',
                     '可划分子网数：65,536', f'网络地址总量：{2**80:,}',
                     f'每个子网地址数：{2**64:,}', '新增子网位数：16 位'):
            self.assertIn(line, text.splitlines())
        self.assertIn('地址类型：', text)
        self.assertIn('部署提示：', text)
        self.assertIn('规范参考：', text)
        self.assertIn('IPv6 没有广播地址', text)
        self.assertIn('不代表实际可分配主机数量', text)

    def test_normalized_network_and_usage_match_the_calculation(self):
        result = calculate('FD12:3456:789A::1234/48', '64', preview_limit=0)
        text = format_calculation_summary(result)
        self.assertTrue(result.normalized)
        self.assertIn('网络地址：fd12:3456:789a::/48', text)
        self.assertNotIn('::1234', text)
        self.assertIn('ULA', text)

    def test_full_ipv6_space_uses_exact_integer_without_enumeration(self):
        result = calculate('::/0', '128', preview_limit=0)
        text = format_calculation_summary(result)
        self.assertEqual(result.preview, ())
        self.assertIn(f'网络地址总量：{2**128:,}', text.splitlines())
        self.assertIn(f'可划分子网数：{2**128:,}', text.splitlines())
        self.assertIn('每个子网地址数：1', text.splitlines())
        self.assertIn('新增子网位数：128 位', text.splitlines())

    def test_unchanged_prefix_and_single_address_capacity(self):
        for network, prefix, capacity in (('2026:1015:abcd::/48', '48', 2**80),
                                           ('::1/128', '128', 1)):
            with self.subTest(network=network):
                text = format_calculation_summary(calculate(network, prefix, preview_limit=0))
                self.assertIn('可划分子网数：1', text.splitlines())
                self.assertIn(f'每个子网地址数：{capacity:,}', text.splitlines())
                self.assertIn('新增子网位数：0 位', text.splitlines())
