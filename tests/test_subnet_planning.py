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

"""空闲差集与最简覆盖的独立地址集合、边界和资源上限检查。"""
import random
import unittest
from threading import Event
from ipaddress import IPv6Network,IPv6Address,collapse_addresses
from core.ipv6_core import InputError
from core.subnet_planning import free_space,aggregate_cidrs,MAX_FREE_DETAILS
from core.subnet_list import ListCheckCancelled


class PlanningTests(unittest.TestCase):
    def test_empty_occupancy_full_space_and_full_occupancy(self):
        result=free_space('# no occupancy','::/0')
        self.assertEqual(result.free_addresses,2**128)
        self.assertEqual(result.cidrs,(IPv6Network('::/0'),))
        result=free_space('::/0\n::/128','::/0')
        self.assertEqual((result.occupied_addresses,result.free_addresses),(2**128,0))
        self.assertEqual(result.cidrs,())

    def test_single_address_parent_and_last_ipv6_address(self):
        maximum='ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128'
        result=free_space('',maximum)
        self.assertEqual(result.free_addresses,1)
        self.assertEqual(result.cidr_text(),maximum)
        self.assertEqual(free_space(maximum,maximum).free_addresses,0)
        result=free_space(maximum,'::/0')
        self.assertEqual(result.free_addresses,2**128-1)
        self.assertEqual(result.cidr_count,128)

    def test_overlap_duplicates_and_host_bits_count_union_only(self):
        result=free_space('::1/126\n::/126\n::1/128','::1/124')
        self.assertTrue(result.parent_normalized)
        self.assertEqual(result.normalized_count,1)
        self.assertEqual(result.occupied_addresses,4)
        self.assertEqual(result.free_addresses,12)
        self.assertEqual(result.cidrs,(IPv6Network('::4/126'),IPv6Network('::8/125')))

    def test_invalid_or_outside_entries_reject_whole_planning(self):
        for text,parent in [('::/0\nbad','::/0'),('::/0','::/64'),('::10/128','::/124'),('fe80::1%1/64','::/0')]:
            with self.subTest(text=text),self.assertRaises(InputError):free_space(text,parent)
        with self.assertRaises(InputError):aggregate_cidrs('::/0\nbad')
        with self.assertRaises(InputError):aggregate_cidrs('#empty')
        with self.assertRaises(InputError):free_space('::/128','bad')

    def test_exact_aggregation_never_expands_unaligned_ranges(self):
        result=aggregate_cidrs('::1/128\n::2/128')
        self.assertEqual(result.cidrs,(IPv6Network('::1/128'),IPv6Network('::2/128')))
        result=aggregate_cidrs('::/127\n::2/128')
        self.assertEqual(result.cidrs,(IPv6Network('::/127'),IPv6Network('::2/128')))
        self.assertEqual(result.address_count,3)

    def test_aggregation_merges_exact_siblings_removes_covered_subnets(self):
        result=aggregate_cidrs('::/127\n::2/127\n::1/128\n::/127')
        self.assertEqual(result.cidrs,(IPv6Network('::/126'),))
        self.assertEqual((result.input_count,result.address_count),(4,4))
        self.assertIn('覆盖集合保持不变',result.as_text())

    def test_seeded_free_and_aggregate_match_explicit_address_sets(self):
        rng=random.Random(20261019)
        for case in range(60):
            entries=[IPv6Network((rng.randrange(256),rng.randrange(124,129)),strict=False) for _ in range(14)]
            text='\n'.join(map(str,entries))
            occupied=set().union(*(set(map(int,net)) for net in entries))
            free=free_space(text,'::/120')
            actual_free=set().union(*(set(map(int,net)) for net in free.cidrs)) if free.cidrs else set()
            aggregate=aggregate_cidrs(text)
            actual_aggregate=set().union(*(set(map(int,net)) for net in aggregate.cidrs))
            with self.subTest(case=case):
                self.assertEqual(actual_free,set(range(256))-occupied)
                self.assertEqual(actual_aggregate,occupied)
                self.assertEqual(free.free_addresses+free.occupied_addresses,256)
                self.assertEqual(aggregate.cidrs,tuple(collapse_addresses(entries)))
                self.assertEqual(sum(net.num_addresses for net in free.cidrs),free.free_addresses)
                self.assertEqual(sum(end-start+1 for start,end in free.free_ranges),free.free_addresses)

    def test_sparse_full_space_limits_details_but_counts_all_ranges(self):
        text='\n'.join(f'{IPv6Address((index<<112)+1)}/128' for index in range(100))
        result=free_space(text,'::/0')
        self.assertGreater(result.cidr_count,MAX_FREE_DETAILS)
        self.assertEqual(len(result.cidrs),MAX_FREE_DETAILS)
        self.assertFalse(result.complete)
        self.assertEqual(result.free_addresses,2**128-100)
        self.assertEqual(len(result.free_ranges),101)
        with self.assertRaises(InputError):result.cidr_text()
        self.assertIn('CIDR 明细已截断',result.as_text())

    def test_cancel_and_input_limits_apply_to_both_operations(self):
        stop=Event();stop.set()
        with self.assertRaises(ListCheckCancelled):free_space('::/0','::/0',stop=stop)
        with self.assertRaises(ListCheckCancelled):aggregate_cidrs('::/0',stop=stop)
        for text in ('\n'.join(['::/128']*5001),'\ud800','x'*(1024*1024+1)):
            with self.subTest(text=text[:20]),self.assertRaises(InputError):free_space(text,'::/0')
            with self.assertRaises(InputError):aggregate_cidrs(text)

    def test_5000_inputs_and_report_precision(self):
        text='\n'.join(f'2026:1015:abcd:{index:x}::/64' for index in range(5000))
        result=aggregate_cidrs(text)
        self.assertLessEqual(len(result.cidrs),5000)
        self.assertEqual(result.address_count,5000*(2**64))
        report=free_space('::/128','::/0').as_text()
        self.assertIn(f'{2**128-1:,}',report)
        self.assertIn('并集',report)
