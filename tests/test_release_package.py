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

"""发布包包含程序及指定许可，失败时不损坏已有 ZIP。"""
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from app_info import APP_VERSION
from tools.package_release import package_release, LICENSE_FILES


class ReleasePackageTests(unittest.TestCase):
    def prepare(self, directory):
        root = Path(directory)
        name = f'IPv6SubnetCalculator_V{APP_VERSION}'
        (root/'dist').mkdir()
        (root/'dist'/f'{name}.exe').write_bytes(b'executable fixture')
        for filename in LICENSE_FILES:
            path = root/filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('fixture '+filename, encoding='utf-8')
        return root, name

    def test_package_contains_only_executable_and_required_licenses(self):
        with tempfile.TemporaryDirectory() as directory:
            root, name = self.prepare(directory)
            (root/'dist/old.log').write_text('not for release', encoding='utf-8')
            path = package_release(root)
            self.assertEqual(path.name, name+'_Windows.zip')
            with zipfile.ZipFile(path) as archive:
                self.assertIsNone(archive.testzip())
                expected = {f'{name}/{name}.exe'} | {f'{name}/{p}' for p in LICENSE_FILES}
                self.assertEqual(set(archive.namelist()), expected)
                self.assertEqual(archive.read(f'{name}/{name}.exe'), b'executable fixture')

    def test_missing_license_preserves_previous_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root, name = self.prepare(directory)
            destination = root/'dist'/f'{name}_Windows.zip'
            destination.write_bytes(b'previous archive')
            (root/'LICENSE').unlink()
            with self.assertRaises(FileNotFoundError):
                package_release(root)
            self.assertEqual(destination.read_bytes(), b'previous archive')
            self.assertFalse(list((root/'dist').glob('.ipv6-release-*')))

    def test_missing_executable_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root, name = self.prepare(directory)
            (root/'dist'/f'{name}.exe').unlink()
            with self.assertRaises(FileNotFoundError):
                package_release(root)
            self.assertFalse((root/'dist'/f'{name}_Windows.zip').exists())

    def test_packaging_failure_preserves_archive_and_cleans_temporary_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root, name = self.prepare(directory)
            destination = root/'dist'/f'{name}_Windows.zip'
            destination.write_bytes(b'previous archive')
            with patch('tools.package_release.zipfile.ZipFile.write', side_effect=OSError('write failed')):
                with self.assertRaises(OSError):
                    package_release(root)
            self.assertEqual(destination.read_bytes(), b'previous archive')
            self.assertFalse(list((root/'dist').glob('.ipv6-release-*')))
