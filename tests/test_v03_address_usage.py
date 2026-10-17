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

"""V0.3 地址用途识别专项测试。"""
import unittest
from ipaddress import IPv6Network
from core.address_usage import describe_network
from core.ipv6_core import calculate

class UsageTests(unittest.TestCase):
    def check(self, cidr, expected, level=None):
        info = describe_network(IPv6Network(cidr))
        self.assertIn(expected, info.name)
        if level:
            self.assertEqual(info.level, level)
        self.assertTrue(info.guidance)
        self.assertTrue(info.reference)

    def test_documentation(self):
        self.check('2001:db8::/32', '文档', '警告')
        self.check('3fff::/20', '文档', '警告')
    def test_6to4(self):
        self.check('2002::/32', '6to4', '注意')
    def test_teredo_more_specific_than_ietf(self):
        self.check('2001::/48', 'Teredo', '注意')
    def test_ula(self):
        self.check('fd12:3456:789a::/48', 'ULA', '信息')
        self.check('fc00::/8', '保留', '注意')
        self.check('fc00::/7', 'ULA', '注意')
    def test_local(self):
        self.check('fe80::/64', '链路本地', '注意')
    def test_loopback(self):
        self.check('::1/128', '环回', '警告')
    def test_unspecified(self):
        self.check('::/128', '未指定', '警告')
    def test_multicast(self):
        self.check('ff02::/16', '组播', '警告')
    def test_translation(self):
        self.check('64:ff9b::/96', '转换', '注意')
    def test_normal_global(self):
        self.check('2026:1015:abcd::/48', '全球单播', '信息')
    def test_mixed(self):
        self.check('2000::/3', '混合', '注意')
        self.check('::/0', '混合', '注意')
        self.check('2001::/16', '混合', '注意')
    def test_explicit_address_types(self):
        self.check('fd00:1000:a12b::/48', 'ULA')
        self.check('2002::/32', '6to4')
        self.check('ff02::/16', '组播')
        self.check('fe80::/64', '链路本地')
        self.check('fec0::/64', '已废弃')
        self.check('2001:20::/32', 'ORCHIDv2')

    def test_fd_shorthand_is_not_fd00(self):
        info = describe_network(IPv6Network('fd:1000:a12b::/48'))
        self.assertIn('非 ULA', info.name)
        self.assertIn('00fd', info.guidance)

    def test_calculation_unchanged(self):
        for net in ('2002::/32', '2001:db8::/32', 'fd12:3456:789a::/48'):
            r=calculate(net, '64', preview_limit=0)
            self.assertGreater(r.subnet_count,0)
            describe_network(r.network)

if __name__ == '__main__':
    unittest.main()
