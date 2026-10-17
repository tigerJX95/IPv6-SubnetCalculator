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

"""验证报告不能将旧报告、错误版本或错误构建误记为通过。"""
import json
import tempfile
import unittest
from pathlib import Path
from app_info import APP_VERSION
from tools.verify import read_check
from services.build_info import source_digest


class ReleaseValidationTests(unittest.TestCase):
    def test_matching_report_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'report.json'
            payload = dict(status='passed', environment=dict(app_version=APP_VERSION,
                           frozen=True, source_sha256='expected'))
            path.write_text(json.dumps(payload))
            self.assertEqual(read_check(path, 0, True, 'expected'), payload)

    def test_failed_stale_or_wrong_build_report_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'report.json'
            for field, value in (('status', 'running'), ('app_version', '0.8'),
                                 ('frozen', False), ('source_sha256', 'stale')):
                payload = dict(status='passed', environment=dict(app_version=APP_VERSION,
                               frozen=True, source_sha256='expected'))
                (payload if field == 'status' else payload['environment'])[field] = value
                path.write_text(json.dumps(payload))
                with self.subTest(field=field), self.assertRaises(RuntimeError):
                    read_check(path, 0, True, 'expected')
            with self.assertRaises(RuntimeError):
                read_check(path, 1, True, 'expected')

    def test_missing_report_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(RuntimeError):
            read_check(Path(directory)/'missing.json', 0, True, 'expected')

    def test_source_fingerprint_changes_when_runtime_code_changes(self):
        import shutil
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('main.py', 'app.py', 'app_info.py', 'app.ico', 'requirements.txt',
                         'build.cmd', 'LICENSE', 'NOTICE', 'THIRD_PARTY_NOTICES.md'):
                shutil.copyfile(source/name, root/name)
            for folder in ('core', 'ui', 'services', 'assets', 'docs/licenses'):
                shutil.copytree(source/folder, root/folder, ignore=shutil.ignore_patterns('__pycache__'))
            baseline = source_digest(root)
            self.assertEqual(baseline, source_digest(source))
            (root/'app.py').write_text((root/'app.py').read_text()+'\n# modified runtime source\n')
            modified = source_digest(root)
            self.assertNotEqual(baseline, modified)
            (root/'verification').mkdir()
            (root/'verification/summary.json').write_text('{}')
            self.assertEqual(source_digest(root), modified)
