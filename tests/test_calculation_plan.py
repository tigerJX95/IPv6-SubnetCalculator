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

"""方案 JSON 的大整数、非法内容、限额及原子写入保护。"""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
from core.calculation_plan import CalculationPlan, plan_to_payload, plan_from_payload
from core.ipv6_core import InputError
from services.plan_storage import load_plan, save_plan, MAX_PLAN_BYTES


class PlanTests(unittest.TestCase):
    def test_roundtrip_unicode_and_maximum_ipv6_page(self):
        plan = CalculationPlan('::/0',128,'完整 IPv6 空间','中文备注\n保持精确整数',100,
            (2**128+99)//100,(2**128-20,2**128),(2**128,),1)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'中文方案.json';save_plan(path,plan)
            self.assertLess(path.stat().st_size,2000)
            self.assertEqual(load_plan(path),plan)
            self.assertIn('"'+str(2**128)+'"',path.read_text(encoding='utf-8'))

    def test_normalizes_host_bits(self):
        plan=CalculationPlan('2026:1015:ABCD::1234/48',64)
        restored=plan_from_payload(plan_to_payload(plan))
        self.assertEqual(restored.network,'2026:1015:abcd::/48')

    def test_invalid_schema_types_limits_and_indices(self):
        base=plan_to_payload(CalculationPlan('2026:1015:abcd::/48',64))
        cases=[('version',True),('version',2),('format','other'),('target_prefix',True),
               ('target_prefix',47),('network','192.0.2.0/24'),('name','x'*81),('name','\ud800'),('notes','x'*2001)]
        for key,value in cases:
            payload=copy.deepcopy(base);payload[key]=value
            with self.subTest(key=key,value=str(value)[:20]),self.assertRaises(InputError):plan_from_payload(payload)
        for key,value in (('page_size',True),('page_size',500),('page',1),('page','0'),
                          ('page','9'*50),('selected_indices',['101']),('selected_indices',['1','1']),
                          ('selected_indices',['1']*201),('locator_range',['2','1']),
                          ('locator_range',['0','10']),('tab',True),('tab',3)):
            payload=copy.deepcopy(base);payload['view'][key]=value
            with self.subTest(view=key,value=str(value)[:20]),self.assertRaises(InputError):plan_from_payload(payload)
        for payload in ([],{},dict(base,extra=True)):
            with self.assertRaises(InputError):plan_from_payload(payload)

    def test_corrupt_oversized_duplicate_and_non_utf8_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'invalid.json'
            for raw in (b'not json',b'{}',b'\xff',b'{"a":1,"a":2}',b'{"x":NaN}',
                        b'['*2000+b']'*2000,b'x'*(MAX_PLAN_BYTES+1)):
                path.write_bytes(raw)
                with self.subTest(prefix=raw[:20]),self.assertRaises(InputError):load_plan(path)

    def test_bom_is_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bom.json';plan=CalculationPlan('::1/128',128)
            path.write_text(json.dumps(plan_to_payload(plan)),encoding='utf-8-sig')
            self.assertEqual(load_plan(path),plan)

    def test_replace_failure_preserves_original_and_cleans_temporary(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'plan.json';path.write_bytes(b'original')
            with patch('services.plan_storage.os.replace',side_effect=OSError('locked')):
                with self.assertRaises(OSError):save_plan(path,CalculationPlan('::/0',128))
            self.assertEqual(path.read_bytes(),b'original')
            self.assertEqual(list(Path(directory).glob('.ipv6-plan-*')),[])

    def test_invalid_plan_is_rejected_before_any_file_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'plan.json';path.write_bytes(b'original')
            with self.assertRaises(InputError):save_plan(path,CalculationPlan('::/0',128,notes='x'*2001))
            self.assertEqual(path.read_bytes(),b'original')
            self.assertEqual(len(list(Path(directory).iterdir())),1)
