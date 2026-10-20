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

"""导出文件与界面语言的端到端回归；直接检查实际 OOXML 内容。"""
import ast
import json
import re
import tempfile
import unittest
import zipfile
from dataclasses import FrozenInstanceError
from ipaddress import IPv6Network
from pathlib import Path
from threading import Event
from time import monotonic
from unittest.mock import patch
import xml.etree.ElementTree as ET
from PyQt6.QtCore import QSettings, QCoreApplication, QEvent
from PyQt6.QtWidgets import QApplication, QLabel, QToolButton, QComboBox, QTabWidget, QDialog
from PyQt6.QtTest import QTest
from app import create_application
from core.subnet_export import export_all, ExportLabels, ExportCancelled
from core.ipv6_core import calculate
from core.export_estimate import format_size_range
from services.language_service import export_labels, display
from services.export_service import ExportService
from ui.main_window import MainWindow

NS = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
EN = ExportLabels('IPv6 Subnets', 'No.', 'IPv6 Subnet')


def workbook(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        sheet = ET.fromstring(z.read('xl/workbook.xml')).find('x:sheets/x:sheet', NS).get('name')
        root = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        rows = []
        for row in root.findall('x:sheetData/x:row', NS):
            rows.append([c.findtext('x:is/x:t', default='', namespaces=NS) if c.get('t')=='inlineStr'
                         else c.findtext('x:v', namespaces=NS) for c in row])
        return sheet, rows


class ExportFileLanguageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.directory=Path(self.tmp.name)
        self.net=IPv6Network('2026:1015:abcd::/126')

    def tearDown(self):
        self.tmp.cleanup()

    def test_default_api_keeps_chinese_workbook(self):
        p=self.directory/'中文.xlsx';export_all(p,self.net,128,'xlsx')
        sheet,rows=workbook(p)
        self.assertEqual(sheet,'IPv6子网');self.assertEqual(rows[0],['序号','IPv6 子网'])
        self.assertEqual(rows[-1],['4','2026:1015:abcd::3/128'])

    def test_english_headers_sheet_and_data(self):
        p=self.directory/'English.xlsx';export_all(p,self.net,128,'xlsx',labels=EN)
        sheet,rows=workbook(p)
        self.assertEqual(sheet,'IPv6 Subnets');self.assertEqual(rows[0],['No.','IPv6 Subnet'])
        self.assertEqual(rows[1:],[[str(i+1),str(n)] for i,n in enumerate(self.net.subnets(new_prefix=128))])
        with zipfile.ZipFile(p) as z:
            for name in z.namelist():
                if name.endswith('.xml'):self.assertNotRegex(z.read(name).decode(),r'[\u4e00-\u9fff]')

    def test_txt_remains_identical_and_directly_reimportable(self):
        a=self.directory/'cn.txt';b=self.directory/'en.txt'
        export_all(a,self.net,128,'txt');export_all(b,self.net,128,'txt',labels=EN)
        self.assertEqual(a.read_bytes(),b.read_bytes())
        self.assertEqual(len(b.read_text().splitlines()),4)
        for line in b.read_text().splitlines():IPv6Network(line)

    def test_english_huge_range_retains_exact_text_indices(self):
        p=self.directory/'huge.xlsx';end=2**128
        export_all(p,IPv6Network('::/0'),128,'xlsx',start=end-1,end=end,labels=EN)
        _,rows=workbook(p)
        self.assertEqual(rows[1][0],str(end-1));self.assertEqual(rows[2][0],str(end))
        self.assertEqual(rows[-1][1],'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128')
        with zipfile.ZipFile(p) as z:
            root=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
            self.assertEqual(root.find(".//x:c[@r='A3']",NS).get('t'),'inlineStr')

    def test_translated_labels_are_xml_escaped(self):
        labels=ExportLabels('A & "B"', 'No. <&>', 'Subnet & address')
        p=self.directory/'escape.xlsx';export_all(p,self.net,128,'xlsx',labels=labels)
        sheet,rows=workbook(p)
        self.assertEqual(sheet,labels.sheet_name)
        self.assertEqual(rows[0],[labels.index_header,labels.subnet_header])

    def test_english_cancellation_preserves_existing_and_cleans_temp(self):
        p=self.directory/'keep.xlsx';p.write_bytes(b'original');stop=Event()
        with self.assertRaises(ExportCancelled):
            export_all(p,self.net,128,'xlsx',labels=EN,stop=stop,progress=lambda *_:stop.set())
        self.assertEqual(p.read_bytes(),b'original');self.assertEqual(list(self.directory.iterdir()),[p])

    def test_label_snapshot_is_immutable(self):
        with self.assertRaises(FrozenInstanceError):EN.index_header='Changed'


class ExportLanguageUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.settings=QSettings(str(Path(cls.tmp.name)/'prefs.ini'),QSettings.Format.IniFormat)
        cls.app=create_application([],cls.settings);cls.app.setQuitOnLastWindowClosed(False)

    @classmethod
    def tearDownClass(cls):
        cls.app.language_manager.apply('zh_CN',persist=False);cls.tmp.cleanup()

    def setUp(self):
        self.app.language_manager.apply('zh_CN',persist=False)
        self.window=MainWindow();self.window.calculate();self.window.show()
        self.service=self.window.export_service

    def tearDown(self):
        if self.service.busy:self.service.cancel();self.wait(lambda:not self.service.busy)
        self.app.language_manager.apply('zh_CN',persist=False)
        self.window.plan_controller.path=None
        self.window.close();self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);QApplication.processEvents()

    def wait(self,condition):
        deadline=monotonic()+5
        while monotonic()<deadline:
            QApplication.processEvents()
            if condition():return
            QTest.qWait(3)
        self.fail('Qt export timeout')

    def switch(self,language):
        self.app.language_manager.apply(language,persist=False);QApplication.processEvents()

    def test_translator_context_keeps_ui_index_and_export_number_distinct(self):
        self.switch('en_US')
        self.assertEqual(export_labels(),EN)
        self.assertEqual(QCoreApplication.translate('App','序号'),'Index')
        self.assertEqual(QCoreApplication.translate('Export','序号'),'No.')
        self.switch('zh_CN');self.assertEqual(export_labels(),ExportLabels())

    def test_service_freezes_file_language_while_completion_uses_current_ui(self):
        from services.export_service import export_all as actual_export
        with tempfile.TemporaryDirectory() as td:
            for initial,switched,expected in [('en_US','zh_CN',EN),('zh_CN','en_US',ExportLabels())]:
                with self.subTest(initial=initial):
                    self.switch(initial);gate=Event();entered=Event()
                    def blocked(*args,**kwargs):
                        entered.set()
                        if not gate.wait(5):raise RuntimeError('Gate timeout')
                        return actual_export(*args,**kwargs)
                    path=Path(td)/(initial+'.xlsx')
                    with patch('services.export_service.export_all',side_effect=blocked),patch('ui.export_controller.QMessageBox.information'):
                        try:
                            self.window.export_controller.start_export(path,'xlsx',self.window.result,100,103)
                            self.wait(entered.is_set)
                            self.assertEqual(self.service._thread.labels,expected)
                            self.switch(switched)
                        finally:gate.set()
                        self.wait(lambda:not self.service.busy)
                    sheet,rows=workbook(path)
                    self.assertEqual(sheet,expected.sheet_name)
                    self.assertEqual(rows[0],[expected.index_header,expected.subnet_header])
                    self.assertEqual(rows[1][0],'100')
                    self.assertIn('导出成功' if switched=='zh_CN' else 'Export complete',self.window.feedback.text())

    def test_language_changed_in_picker_is_used_at_actual_export_start(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'测试.xlsx'
            def select(*args,**kwargs):
                self.switch('en_US');return str(path),'Excel Workbook (*.xlsx)'
            with patch('ui.export_controller.ExportRangeDialog') as selector,patch('ui.export_controller.QFileDialog.getSaveFileName',side_effect=select),patch('ui.export_controller.QMessageBox.information'):
                selector.return_value.exec.return_value=QDialog.DialogCode.Accepted
                selector.return_value.span=(1,3)
                self.window.export_controller.request_export(self.window.result)
                self.wait(lambda:not self.service.busy)
            self.assertEqual(workbook(path)[1][0],['No.','IPv6 Subnet'])

    def test_english_request_honors_txt_filter_without_extension(self):
        self.switch('en_US')
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'subnets'
            with patch('ui.export_controller.ExportRangeDialog') as selector,patch('ui.export_controller.QFileDialog.getSaveFileName',return_value=(str(path),'Text Files (*.txt)')),patch('ui.export_controller.QMessageBox.information'):
                selector.return_value.exec.return_value=QDialog.DialogCode.Accepted;selector.return_value.span=(2,4)
                self.window.export_controller.request_export(self.window.result);self.wait(lambda:not self.service.busy)
            self.assertEqual(path.with_suffix('.txt').read_text().splitlines()[0],'2026:1015:abcd:1::/64')

    def test_disk_size_range_has_english_separator(self):
        self.switch('en_US');value=display(format_size_range(1024**2,2*1024**2))
        self.assertEqual(value,'1.00–2.00 MiB')
        self.switch('zh_CN');self.assertIn('～',display(format_size_range(1,2)))

    def test_pages_tooltips_and_dialog_titles_have_no_untranslated_chinese(self):
        from ui.dialogs import ExportRangeDialog, RangeCopyDialog, SubnetDetailDialog
        self.switch('en_US');self.window.address_tools_page.convert();self.window.address_tools_page.analyze()
        dialogs=[ExportRangeDialog(65536,self.window),RangeCopyDialog(self.window.result,self.window.clipboard,parent=self.window),SubnetDetailDialog(self.window.result,1,self.window.clipboard,self.window)]
        try:
            for root in [self.window,*dialogs]:
                self.assertNotRegex(root.windowTitle(),r'[\u4e00-\u9fff]')
                for w in root.findChildren(QLabel)+root.findChildren(QToolButton)+root.findChildren(QComboBox)+root.findChildren(QTabWidget):
                    strings=[w.toolTip(),w.accessibleName()]
                    if isinstance(w,(QLabel,QToolButton)):strings.append(w.text())
                    if isinstance(w,QComboBox):strings.extend(w.itemText(i) for i in range(w.count()))
                    if isinstance(w,QTabWidget):strings.extend(w.tabText(i) for i in range(w.count()))
                    for value in strings:self.assertNotRegex(value.replace('简体中文',''),r'[\u4e00-\u9fff]',f'{w.objectName()} ({w.parent().metaObject().className()}): {value!r}')
        finally:
            for d in dialogs:d.deleteLater()

    def test_tab_scroll_tooltips_follow_both_directions_and_themes(self):
        for theme in ('light','dark'):
            self.app.theme_manager.apply(theme,persist=False)
            for language in ('en_US','zh_CN','en_US'):
                self.switch(language)
                for tabs in self.window.findChildren(QTabWidget):
                    for name,english,chinese in [('ScrollLeftButton','Scroll Left','向左滚动'),('ScrollRightButton','Scroll Right','向右滚动')]:
                        button=tabs.tabBar().findChild(QToolButton,name)
                        self.assertIsNotNone(button)
                        self.assertEqual(button.toolTip(),english if language=='en_US' else chinese)
                        self.assertEqual(button.accessibleName(),button.toolTip())

    def test_all_chinese_message_templates_have_catalog_entries(self):
        root=Path(__file__).resolve().parents[1]
        tree=ET.parse(root/'assets/i18n/app_en.ts').getroot()
        catalog={m.findtext('source') for c in tree.findall('context') if c.findtext('name')=='App' for m in c.findall('message')}
        for folder in ('core','ui','services'):
            for p in (root/folder).glob('*.py'):
                for n in ast.walk(ast.parse(p.read_text())):
                    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='tx' and n.args and isinstance(n.args[0],ast.Constant):
                        source=n.args[0].value
                        if isinstance(source,str) and re.search(r'[\u4e00-\u9fff]',source):self.assertIn(source,catalog,f'{p.name}:{n.lineno}')


if __name__=='__main__':unittest.main()
