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

"""运行完整 unittest suite 并输出带运行标识的结构化结果。"""
import argparse
import json
import sys
import time
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app_info import APP_VERSION
from services.build_info import source_digest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--run-id',required=True)
    args=parser.parse_args()
    args.report.unlink(missing_ok=True)
    fingerprint=source_digest()
    started=time.monotonic()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    expected=suite.countTestCases()
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    passed=expected>0 and result.testsRun==expected and result.wasSuccessful() and source_digest()==fingerprint
    payload=dict(app_version=APP_VERSION,source_sha256=fingerprint,run_id=args.run_id,
        status='passed' if passed else 'failed',complete=result.testsRun==expected,
        expected_tests=expected,tests_run=result.testsRun,failures=len(result.failures),
        errors=len(result.errors),skipped=len(result.skipped),expected_failures=len(result.expectedFailures),
        unexpected_successes=len(result.unexpectedSuccesses),elapsed_seconds=round(time.monotonic()-started,3))
    args.report.write_text(json.dumps(payload,indent=2),encoding='utf-8')
    return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
