import tempfile
import unittest
import zipfile
from pathlib import Path
from threading import Event
from ipaddress import IPv6Network
from xml.etree import ElementTree as ET
from subnet_export import page_subnets, subnet_at, export_all, ExportCancelled, XLSX_MAX_RECORDS

class ExportTests(unittest.TestCase):
    def setUp(self):
        self.net = IPv6Network('2026:1015:abcd::/48')

    def test_pagination(self):
        self.assertEqual(page_subnets(self.net, 64, 1, 25)[0], (1, '2026:1015:abcd::/64'))
        self.assertEqual(page_subnets(self.net, 64, 2, 25)[0], (26, '2026:1015:abcd:19::/64'))
        self.assertEqual(page_subnets(self.net, 64, 2622, 25)[-1], (65536, '2026:1015:abcd:ffff::/64'))
        with self.assertRaises(ValueError): page_subnets(self.net, 64, 2623, 25)

    def test_huge_random_access(self):
        whole = IPv6Network('::/0')
        index = (1 << 128) - 1
        self.assertEqual(str(subnet_at(whole,128,index)), 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128')
        page = ((1 << 128) - 1) // 100 + 1
        self.assertEqual(page_subnets(whole, 128, page, 100)[-1][0], 1 << 128)

    def test_txt_export(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'out.txt'
            report=export_all(path, IPv6Network('2026:1015:abcd::/126'), 128,'txt')
            self.assertEqual(report.rows,4)
            self.assertEqual(path.read_text().splitlines(),
                ['2026:1015:abcd::/128','2026:1015:abcd::1/128','2026:1015:abcd::2/128','2026:1015:abcd::3/128'])

    def test_xlsx_export_valid_xml(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'out.xlsx'
            export_all(path, IPv6Network('2026:1015:abcd::/126'), 128,'xlsx')
            with zipfile.ZipFile(path) as z:
                self.assertIsNone(z.testzip())
                xml=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
                ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                rows=xml.findall('.//x:sheetData/x:row',ns)
                self.assertEqual(len(rows),5)
                self.assertIn('2026:1015:abcd::3/128',z.read('xl/worksheets/sheet1.xml').decode())

    def test_cancel_preserves_existing(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'out.txt'
            path.write_text('original')
            event=Event()
            def cancel(done,total): event.set()
            with self.assertRaises(ExportCancelled):
                export_all(path,self.net,64,'txt',stop=event,progress=cancel)
            self.assertEqual(path.read_text(),'original')
            self.assertEqual(sorted(p.name for p in Path(d).iterdir()), ['out.txt'])

    def test_excel_limit(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                export_all(Path(d)/'out.xlsx',IPv6Network('2026:1015:abcd::/48'),80,'xlsx')
            self.assertFalse((Path(d)/'out.xlsx').exists())
            self.assertEqual(XLSX_MAX_RECORDS,1048575)

    def test_invalid_page_size(self):
        with self.assertRaises(ValueError): page_subnets(self.net,64,1,1000000)

if __name__=='__main__': unittest.main()
