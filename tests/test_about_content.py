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

"""关于窗口文档边界、错误提示及打包资源指纹。"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from services.about_content import read_document, program_information, HELP_DOCUMENT, LEGAL_DOCUMENT
from services.build_info import source_digest


class AboutContentTests(unittest.TestCase):
    def test_runtime_sip_distribution_is_not_generator_version(self):
        from importlib.metadata import version
        self.assertIn('| PyQt6-sip | '+version('PyQt6-sip')+' |', program_information())

    def test_missing_metadata_does_not_invent_a_distribution_version(self):
        from importlib.metadata import PackageNotFoundError
        with patch('services.about_content.version', side_effect=PackageNotFoundError):
            self.assertIn('发行元数据不可用（SIP 引擎', program_information())

    def test_unlisted_paths_are_rejected(self):
        for path in ('../LICENSE', '/etc/passwd', 'https://example.com', 'docs/about/missing.md'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                read_document(path)

    def test_missing_invalid_utf8_and_empty_files_have_clear_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'help.md'
            with patch('services.about_content.resource_path', return_value=path):
                for content in (None, b'\xff', b' '):
                    if content is not None:
                        path.write_bytes(content)
                    with self.subTest(content=content), self.assertRaisesRegex(RuntimeError, '无法读取内置文档'):
                        read_document(HELP_DOCUMENT)
                path.write_text('使用说明', encoding='utf-8')
                self.assertEqual(read_document(HELP_DOCUMENT), '使用说明')

    def test_help_and_legal_are_in_runtime_fingerprint(self):
        import shutil
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('main.py', 'app.py', 'app_info.py', 'app.ico', 'requirements.txt',
                         'build.cmd', 'LICENSE', 'NOTICE', 'THIRD_PARTY_NOTICES.md'):
                shutil.copyfile(source/name, root/name)
            for folder in ('core','ui','services','assets','docs/licenses','docs/about'):
                shutil.copytree(source/folder, root/folder, ignore=shutil.ignore_patterns('__pycache__'))
            baseline = source_digest(root)
            for name in (HELP_DOCUMENT, LEGAL_DOCUMENT):
                path=root/name
                original=path.read_bytes()
                path.write_bytes(original+b'\nChanged bundled content\n')
                self.assertNotEqual(source_digest(root),baseline)
                path.write_bytes(original)
                self.assertEqual(source_digest(root),baseline)
