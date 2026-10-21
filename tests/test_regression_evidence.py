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

"""发布门禁拒绝缺失、空、旧版或部分结构化测试证据。"""
import json,tempfile,unittest
from pathlib import Path
from tools.verify import read_regression,read_check
from app_info import APP_VERSION
from services.release_contract import REQUIRED_RELEASE_CHECKS


class RegressionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'result.json'
        self.good=dict(status='passed',complete=True,tests_run=1,expected_tests=1,failures=0,errors=0,
            unexpected_successes=0,skipped=0,app_version=APP_VERSION,source_sha256='digest',run_id='current')
    def tearDown(self):self.temp.cleanup()
    def test_complete_matching_evidence_accepted(self):
        self.path.write_text(json.dumps(self.good));self.assertEqual(read_regression(self.path,0,'digest','current'),self.good)
    def test_missing_or_truncated_evidence_rejected_even_with_zero_exit(self):
        for value in (None,'','{'):
            if value is not None:self.path.write_text(value)
            with self.assertRaises(RuntimeError):read_regression(self.path,0,'digest','current')
    def test_zero_partial_failed_or_stale_result_rejected(self):
        for key,value in [('tests_run',0),('tests_run',True),('expected_tests',True),('failures',False),('skipped',-1),('expected_tests',2),('complete',False),('status','running'),('failures',1),('errors',1),('unexpected_successes',1),('run_id','old'),('source_sha256','old'),('app_version','old')]:
            payload=dict(self.good);payload[key]=value;self.path.write_text(json.dumps(payload))
            with self.subTest(key=key,value=value),self.assertRaises(RuntimeError):read_regression(self.path,0,'digest','current')
    def test_failed_process_rejected_even_with_good_report(self):
        self.path.write_text(json.dumps(self.good))
        with self.assertRaises(RuntimeError):read_regression(self.path,1,'digest','current')
    def test_self_check_missing_workflow_rejected(self):
        payload=dict(status='passed',environment=dict(app_version=APP_VERSION,source_sha256='digest',frozen=True),checks=sorted(REQUIRED_RELEASE_CHECKS)[:-1])
        self.path.write_text(json.dumps(payload))
        with self.assertRaises(RuntimeError):read_check(self.path,0,True,'digest')
