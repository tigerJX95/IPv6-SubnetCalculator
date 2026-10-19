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

"""独立清单的关系正确性、资源上限、编码和取消行为。"""
import random
import tempfile
import unittest
from pathlib import Path
from threading import Event
from ipaddress import IPv6Network
from core.ipv6_core import InputError
from core.subnet_list import (analyze_subnet_list, validate_list_text, ListCheckCancelled,
                             MAX_LIST_BYTES, MAX_RELATION_DETAILS)
from services.subnet_list_service import load_subnet_list


class SubnetListTests(unittest.TestCase):
    def test_original_line_numbers_normalization_and_all_relation_kinds(self):
        result=analyze_subnet_list('# example\n\n2026:1015:abcd:1::1/64\n2026:1015:abcd::/48\n2026:1015:abcd:1::/64\n2026:1015:abcd:2::/64\nbad\n')
        self.assertEqual([r.line for r in result.records],[3,4,5,6,7])
        self.assertTrue(result.records[0].normalized)
        self.assertEqual((result.valid_count,result.error_count),(4,1))
        self.assertEqual((result.duplicate_pairs,result.containment_pairs,result.adjacent_pairs),(1,3,2))
        self.assertIn((4,3,'contains'),[(r.first,r.second,r.kind) for r in result.relations])
        self.assertEqual(result.normalized_text().splitlines(),['2026:1015:abcd:1::/64','2026:1015:abcd::/48','2026:1015:abcd:2::/64'])
        self.assertIn('错误行不参与分析',result.as_text())
        self.assertIn('第 7 行：bad',result.as_text())

    def test_maximum_space_single_address_and_no_wraparound(self):
        result=analyze_subnet_list('::/0\n::/128\nffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128')
        self.assertEqual((result.duplicate_pairs,result.containment_pairs,result.adjacent_pairs),(0,2,0))
        result=analyze_subnet_list('::/128\n::1/128\n::2/127')
        self.assertEqual(result.adjacent_pairs,2)
        self.assertEqual(result.containment_pairs,0)

    def test_randomized_relations_match_exhaustive_interval_oracle(self):
        randomizer=random.Random(20261019)
        for case in range(60):
            entries=[]
            for i in range(28):
                if entries and randomizer.random()<0.2:
                    entries.append(randomizer.choice(entries))
                else:
                    prefix=randomizer.randrange(118,129)
                    entries.append(IPv6Network((randomizer.randrange(512),prefix),strict=False))
            result=analyze_subnet_list('\n'.join(map(str,entries)))
            expected=dict(duplicate=0,contains=0,adjacent=0)
            pairs=[]
            for i,a in enumerate(entries):
                for j,b in enumerate(entries[i+1:],i+1):
                    a0,a1=int(a.network_address),int(a.broadcast_address)
                    b0,b1=int(b.network_address),int(b.broadcast_address)
                    if a0==b0 and a1==b1:
                        kind='duplicate'
                    elif max(a0,b0)<=min(a1,b1):
                        kind='contains'
                    elif a1+1==b0 or b1+1==a0:
                        kind='adjacent'
                    else:
                        continue
                    expected[kind]+=1
                    pairs.append((i+1,j+1,kind))
            with self.subTest(case=case):
                self.assertEqual((result.duplicate_pairs,result.containment_pairs,result.adjacent_pairs),tuple(expected.values()))
                actual={(min(r.first,r.second),max(r.first,r.second),r.kind) for r in result.relations}
                self.assertEqual(actual,set(pairs))

    def test_relation_cap_keeps_exact_dense_duplicate_count(self):
        result=analyze_subnet_list('\n'.join(['::/0']*5000))
        self.assertEqual(result.duplicate_pairs,5000*4999//2)
        self.assertEqual(len(result.relations),MAX_RELATION_DETAILS)
        self.assertEqual(len(result.unique_networks),1)
        self.assertIn('明细已截断',result.as_text())

    def test_relation_cap_keeps_exact_containment_and_adjacency_counts(self):
        result=analyze_subnet_list('\n'.join(['::/127']*1800+['::/128']*1600+['::1/128']*1600))
        self.assertEqual(result.containment_pairs,1800*3200)
        self.assertEqual(result.adjacent_pairs,1600*1600)
        self.assertEqual(len(result.relations),MAX_RELATION_DETAILS)

    def test_5000_unique_networks_produce_bounded_details(self):
        result=analyze_subnet_list('\n'.join(f'2026:1015:abcd:{i:x}::/64' for i in range(5000)))
        self.assertEqual(result.valid_count,5000)
        self.assertEqual(result.adjacent_pairs,4999)
        self.assertEqual(len(result.relations),1000)

    def test_empty_comments_limits_and_invalid_unicode(self):
        for text in ('','# only comments\n\n','x'*(MAX_LIST_BYTES+1),'\ud800','::/0\x00',
                     '\n'.join(['::/128']*5001),'#\n'*20001):
            with self.subTest(text=text[:30]),self.assertRaises(InputError):
                analyze_subnet_list(text)
        with self.assertRaises(InputError):
            validate_list_text(None)

    def test_invalid_lines_remain_visible_and_do_not_participate(self):
        result=analyze_subnet_list('192.0.2.0/24\nfe80::1%1/64\n::/129\n::\n::/64 # comment\n'+'a'*201)
        self.assertEqual(result.valid_count,0)
        self.assertEqual(result.error_count,6)
        self.assertEqual(result.relation_count,0)
        self.assertEqual(result.normalized_text(),'')

    def test_cancel_before_and_during_processing(self):
        stop=Event();stop.set()
        with self.assertRaises(ListCheckCancelled):
            analyze_subnet_list('::/0',stop=stop)
        class StopLater:
            def __init__(self):self.calls=0
            def is_set(self):
                self.calls+=1
                return self.calls>10
        with self.assertRaises(ListCheckCancelled):
            analyze_subnet_list('\n'.join(['::/128']*100),stop=StopLater())

    def test_utf8_bom_crlf_file_and_unchanged_original(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'子网清单.txt'
            original=b'\xef\xbb\xbf# '+ '示例'.encode('utf-8')+b'\r\n::/0\r\n::1/128\r\n'
            path.write_bytes(original)
            text=load_subnet_list(path)
            self.assertEqual(analyze_subnet_list(text).containment_pairs,1)
            self.assertEqual(path.read_bytes(),original)

    def test_bad_encoding_oversized_empty_and_missing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'list.txt'
            with self.assertRaises(OSError):load_subnet_list(path)
            for value in (b'\xff',b'x'*(MAX_LIST_BYTES+1),b'',b'::/0\x00'):
                path.write_bytes(value)
                with self.subTest(value=value[:10]),self.assertRaises(InputError):load_subnet_list(path)
