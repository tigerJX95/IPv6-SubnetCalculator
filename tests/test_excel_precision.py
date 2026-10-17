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

import unittest
import tempfile
import zipfile
from pathlib import Path
from ipaddress import IPv6Network
from xml.etree import ElementTree as ET
from core.subnet_export import export_all

class ExcelPrecisionTests(unittest.TestCase):

    def exported_cells(self, start, end):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'indices.xlsx'
            report = export_all(path, IPv6Network('::/0'), 128, 'xlsx', start=start, end=end)
            self.assertEqual(report.rows, end - start + 1)
            with zipfile.ZipFile(path) as archive:
                sheet = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
        ns = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        rows = sheet.findall('x:sheetData/x:row', ns)[1:]
        return ([row.find('x:c', ns) for row in rows], ns)

    def test_fifteen_digit_indices_remain_numeric(self):
        cells, ns = self.exported_cells(10 ** 15 - 2, 10 ** 15 - 1)
        self.assertTrue(all((cell.get('t') is None for cell in cells)))
        self.assertEqual([cell.find('x:v', ns).text for cell in cells], [str(10 ** 15 - 2), str(10 ** 15 - 1)])

    def test_sixteen_digit_indices_are_exact_text(self):
        cells, ns = self.exported_cells(10 ** 15 + 1, 10 ** 15 + 2)
        self.assertTrue(all((cell.get('t') == 'inlineStr' for cell in cells)))
        self.assertEqual([cell.find('x:is/x:t', ns).text for cell in cells], [str(10 ** 15 + 1), str(10 ** 15 + 2)])

    def test_crossing_precision_boundary_uses_one_column_type(self):
        cells, ns = self.exported_cells(10 ** 15 - 1, 10 ** 15 + 1)
        self.assertTrue(all((cell.get('t') == 'inlineStr' for cell in cells)))
        self.assertEqual([cell.find('x:is/x:t', ns).text for cell in cells], [str(n) for n in range(10 ** 15 - 1, 10 ** 15 + 2)])

    def test_final_ipv6_indices_are_preserved(self):
        cells, ns = self.exported_cells(2 ** 128 - 1, 2 ** 128)
        self.assertEqual([cell.find('x:is/x:t', ns).text for cell in cells], [str(2 ** 128 - 1), str(2 ** 128)])
