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

"""导出格式校验回归测试，无需启动图形界面。"""
import ast
import unittest
from pathlib import Path

from core.formatting import determine_export_format as validate

class SaveDialogTests(unittest.TestCase):
    def test_normal_excel(self):
        self.assertEqual(validate(Path('export.xlsx'), False), 'xlsx')
    def test_normal_txt(self):
        self.assertEqual(validate(Path('export.txt'), False), 'txt')
    def test_uppercase_extension(self):
        self.assertEqual(validate(Path('export.TXT'), True), 'txt')
    def test_oversized_txt(self):
        self.assertEqual(validate(Path('export.txt'), True), 'txt')
    def test_oversized_excel_rejected(self):
        with self.assertRaises(ValueError): validate(Path('export.xlsx'), True)
    def test_unknown_extension_rejected(self):
        with self.assertRaises(ValueError): validate(Path('export.csv'), False)
