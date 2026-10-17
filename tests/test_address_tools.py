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

"""格式转换与网段关系的精度、错误输入和区间交叉验证。"""
import random
import unittest
from ipaddress import IPv6Address, IPv6Network
from core.address_conversion import convert_address
from core.network_relations import analyze_networks
from core.ipv6_core import InputError


class AddressConversionTests(unittest.TestCase):
    def test_compressed_expanded_and_normalized(self):
        result = convert_address(' 2026:1015:ABCD:0000:0000:0000:0000:0001 ')
        self.assertEqual(result.compressed, '2026:1015:abcd::1')
        self.assertEqual(result.normalized, result.compressed)
        self.assertEqual(result.expanded, '2026:1015:abcd:0000:0000:0000:0000:0001')
        self.assertEqual(result.as_text().splitlines()[-1], '二进制（128 位）：'+result.binary)

    def test_zero_maximum_and_single_bit_preserve_all_128_bits(self):
        for text, expected in (('::','0'*128), ('::1','0'*127+'1'),
                                ('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff','1'*128)):
            with self.subTest(text=text):
                result=convert_address(text)
                self.assertEqual(result.binary, expected)
                self.assertEqual(len(result.expanded), 39)

    def test_zero_run_tie_and_single_zero(self):
        self.assertEqual(convert_address('2001:0:0:1:0:0:1:1').compressed, '2001::1:0:0:1:1')
        self.assertEqual(convert_address('2001:db8:0:1:1:1:1:1').compressed, '2001:db8:0:1:1:1:1:1')

    def test_ipv4_mapped_address_is_lossless(self):
        result=convert_address('::FFFF:192.0.2.1')
        self.assertIn(result.compressed, ('::ffff:c000:201', '::ffff:192.0.2.1'))
        self.assertEqual(result.expanded, '0000:0000:0000:0000:0000:ffff:c000:0201')
        self.assertEqual(int(IPv6Address(result.compressed)), int(IPv6Address(result.expanded)))
        self.assertEqual(int(result.binary,2), int(IPv6Address('::ffff:192.0.2.1')))

    def test_seeded_roundtrips(self):
        rng=random.Random(20261017)
        for _ in range(300):
            number=rng.getrandbits(128)
            result=convert_address(IPv6Address(number).exploded.upper())
            self.assertEqual(int(IPv6Address(result.compressed)), number)
            self.assertEqual(int(IPv6Address(result.expanded)), number)
            self.assertEqual(len(result.binary),128)
            self.assertEqual(int(result.binary,2),number)

    def test_invalid_inputs(self):
        for text in ('', '192.0.2.1', '::/64', 'fe80::1%12', '2001:::1', '2001::db8::1',
                     'gggg::1', '1:2:3:4:5:6:7', '::ffff:256.0.0.1'):
            with self.subTest(text=text), self.assertRaises(InputError):
                convert_address(text)


class NetworkRelationTests(unittest.TestCase):
    def test_all_relationships_and_direction(self):
        cases=(('::/126','::/126','same',4,0), ('::/126','::/128','a_contains_b',1,0),
               ('::/128','::/126','b_contains_a',1,0), ('::/127','::2/127','adjacent',0,0),
               ('::/128','::2/128','independent',0,1))
        for a,b,kind,overlap,gap in cases:
            with self.subTest(a=a,b=b):
                relation=analyze_networks(a,b)
                self.assertEqual((relation.kind,relation.overlap_count,relation.gap_count),(kind,overlap,gap))

    def test_normalization_and_copy_report(self):
        result=analyze_networks(' 2026:1015:ABCD::1234 / 048 ', '2026:1015:abcd::5678/64')
        self.assertEqual(result.kind,'a_contains_b')
        self.assertTrue(result.normalized_a)
        self.assertTrue(result.normalized_b)
        self.assertEqual(str(result.network_a),'2026:1015:abcd::/48')
        self.assertIn('A 地址范围：', result.as_text())
        self.assertIn(f'重叠地址数：{2**64:,}', result.as_text())
        self.assertIn('主机位规范化：A 是；B 是',result.as_text())

    def test_full_space_and_no_wraparound_at_boundary(self):
        result=analyze_networks('::/0','::/0')
        self.assertEqual(result.overlap_count,2**128)
        self.assertIn(f'{2**128:,}', result.as_text())
        self.assertEqual(analyze_networks('::/0','ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128').kind,'a_contains_b')
        result=analyze_networks('::/128','ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128')
        self.assertEqual(result.kind,'independent')
        self.assertEqual(result.gap_count,2**128-2)

    def test_unequal_prefix_adjacency_does_not_imply_one_cidr(self):
        result=analyze_networks('::/127','::2/128')
        self.assertEqual(result.kind,'adjacent')
        self.assertIn('不代表一定能合并', result.detail)
        reverse=analyze_networks('::2/128','::/127')
        self.assertEqual((reverse.kind,reverse.gap_count),('adjacent',0))

    def test_invalid_cidr_identifies_input(self):
        for invalid in ('', '::', '192.0.2.0/24', '::/129', '::/-1', '::/６４', 'fe80::1%eth0/64', ':://64'):
            for side in ('A','B'):
                with self.subTest(invalid=invalid,side=side), self.assertRaisesRegex(InputError,'网段 '+side+'：'):
                    analyze_networks(invalid if side=='A' else '::/0',invalid if side=='B' else '::/0')

    def test_all_small_network_pairs_match_independent_interval_oracle(self):
        networks=[IPv6Network((start,prefix)) for prefix in range(125,129)
                  for start in range(0,8,1<<(128-prefix))]
        for a in networks:
            for b in networks:
                a0,a1=int(a.network_address),int(a.broadcast_address)
                b0,b1=int(b.network_address),int(b.broadcast_address)
                overlap=max(0,min(a1,b1)-max(a0,b0)+1)
                gap=max(0,max(a0,b0)-min(a1,b1)-1)
                if (a0,a1)==(b0,b1): kind='same'
                elif a0<=b0 and a1>=b1: kind='a_contains_b'
                elif b0<=a0 and b1>=a1: kind='b_contains_a'
                elif gap==0: kind='adjacent'
                else: kind='independent'
                result=analyze_networks(str(a),str(b))
                self.assertEqual((result.kind,result.overlap_count,result.gap_count),(kind,overlap,gap),(a,b))
