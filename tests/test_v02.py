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

"""V0.2 范围导出与 IPv6 地址定位专项测试。"""
import tempfile
import unittest
import zipfile
from pathlib import Path
from ipaddress import IPv6Network
from threading import Event
from core.ipv6_core import InputError, locate_subnet
from core.subnet_export import export_all, ExportCancelled, XLSX_MAX_RECORDS
from core.export_estimate import estimate_export_range


class Version02Tests(unittest.TestCase):
    def setUp(self):
        self.net = IPv6Network('2026:1015:abcd::/48')

    def test_locate_first_middle_last(self):
        self.assertEqual(locate_subnet(self.net, 64, '2026:1015:abcd::1'), 1)
        self.assertEqual(locate_subnet(self.net, 64, '2026:1015:abcd:19::abcd'), 26)
        self.assertEqual(locate_subnet(self.net, 64, '2026:1015:abcd:ffff:ffff:ffff:ffff:ffff'), 65536)

    def test_locate_invalid_or_outside(self):
        for address in ('', 'not-an-ipv6', '2026:1015:abce::1', '2026:1015:abcd::/64'):
            with self.subTest(address=address), self.assertRaises(InputError):
                locate_subnet(self.net, 64, address)

    def test_locate_huge_network_constant_time(self):
        self.assertEqual(locate_subnet(IPv6Network('::/0'), 128, 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff'), 1 << 128)

    def test_range_txt_content(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'range.txt'
            report = export_all(path, self.net, 64, 'txt', start=25, end=27)
            self.assertEqual(report.rows, 3)
            self.assertEqual(path.read_text(encoding='utf-8').splitlines(), [
                '2026:1015:abcd:18::/64',
                '2026:1015:abcd:19::/64',
                '2026:1015:abcd:1a::/64',
            ])

    def test_range_xlsx_original_indices(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'range.xlsx'
            report = export_all(path, self.net, 64, 'xlsx', start=25, end=27)
            self.assertEqual(report.rows, 3)
            with zipfile.ZipFile(path) as z:
                xml = z.read('xl/worksheets/sheet1.xml').decode()
                self.assertIn('<v>25</v>', xml)
                self.assertIn('<v>27</v>', xml)
                self.assertIn('2026:1015:abcd:1a::/64', xml)
                self.assertNotIn('<v>24</v>', xml)

    def test_invalid_ranges_leave_no_files(self):
        with tempfile.TemporaryDirectory() as d:
            for i, (start, end) in enumerate([(0,1), (2,1), (1,65537), (True,2), (1,False), (1,1.5)]):
                path = Path(d) / f'{i}.txt'
                with self.subTest(start=start,end=end), self.assertRaises(ValueError):
                    export_all(path, self.net, 64, 'txt', start=start, end=end)
                self.assertFalse(path.exists())

    def test_range_limited_excel_allowed_for_large_network(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'small.xlsx'
            report = export_all(path, self.net, 80, 'xlsx', start=500000, end=500002)
            self.assertEqual(report.rows, 3)
            with zipfile.ZipFile(path) as z:
                self.assertIn('<v>500000</v>', z.read('xl/worksheets/sheet1.xml').decode())

    def test_range_cancel_retains_previous_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'range.txt'
            path.write_text('此前内容', encoding='utf-8')
            stop = Event()
            def progress(done, total): stop.set()
            with self.assertRaises(ExportCancelled):
                export_all(path, self.net, 64, 'txt', start=1000, end=4000, stop=stop, progress=progress)
            self.assertEqual(path.read_text(encoding='utf-8'), '此前内容')
            self.assertEqual([f.name for f in Path(d).iterdir()], ['range.txt'])

    def test_estimate_respects_start(self):
        low, high = estimate_export_range(self.net, 64, 'txt', 1, start_index=65535)
        self.assertGreater(low, 0)
        self.assertGreaterEqual(high, low)


if __name__ == '__main__':
    unittest.main()
