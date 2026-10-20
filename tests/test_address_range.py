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

"""范围最简覆盖、整数边界、交互与安全清单衔接回归。"""
import random,tempfile,unittest
from dataclasses import replace
from pathlib import Path
from ipaddress import IPv6Address,IPv6Network
from time import monotonic
from unittest.mock import patch,PropertyMock
from PyQt6.QtCore import QSettings,QCoreApplication,QEvent
from PyQt6.QtWidgets import QApplication,QScrollArea
from PyQt6.QtTest import QTest
from app import create_application
from core.address_range import range_to_cidrs
from core.ipv6_core import InputError
from core.subnet_list import analyze_subnet_list
from core.subnet_planning import free_space,aggregate_cidrs
from services.plan_storage import load_plan
from ui.main_window import MainWindow
from ui.standard_dialogs import QMessageBox


class AddressRangeCoreTests(unittest.TestCase):
    def test_entire_ipv6_space_without_enumeration(self):
        r=range_to_cidrs('::','ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff')
        self.assertEqual(r.cidrs,(IPv6Network('::/0'),));self.assertEqual(r.address_count,2**128)

    def test_single_and_aligned_ranges(self):
        for start,end,want in [('::','::',['::/128']),('::1','::1',['::1/128']),('::','::ff',['::/120'])]:
            self.assertEqual(range_to_cidrs(start,end).cidr_text().splitlines(),want)

    def test_unaligned_extreme_has_exact_254_blocks(self):
        r=range_to_cidrs('::1',str(IPv6Address(2**128-2)))
        self.assertEqual(len(r.cidrs),254);self.assertEqual(r.address_count,2**128-2)
        self.assertEqual(sum(n.num_addresses for n in r.cidrs),r.address_count)

    def test_random_ranges_exact_nonoverlapping_and_unmergeable(self):
        rng=random.Random(18)
        for _ in range(80):
            start=rng.randrange(2**128);end=rng.randrange(start,2**128)
            r=range_to_cidrs(str(IPv6Address(start)),str(IPv6Address(end)))
            self.assertEqual(int(r.cidrs[0].network_address),start)
            self.assertEqual(int(r.cidrs[-1].broadcast_address),end)
            self.assertEqual(sum(n.num_addresses for n in r.cidrs),end-start+1)
            self.assertLessEqual(len(r.cidrs),254)
            for a,b in zip(r.cidrs,r.cidrs[1:]):
                self.assertEqual(int(a.broadcast_address)+1,int(b.network_address))
                self.assertFalse(a.prefixlen==b.prefixlen and a.prefixlen>0 and a.supernet()==b.supernet())

    def test_invalid_inputs_locate_the_responsible_field(self):
        for start,end,field in [('', '::','start'),('::','bad','end'),('::/64','::1','start'),('::','fe80::1%3','end'),('::2','::1','end'),('192.0.2.1','::1','start')]:
            with self.subTest(start=start,end=end):
                with self.assertRaises(InputError) as exc:range_to_cidrs(start,end)
                self.assertEqual(exc.exception.field,field)

    def test_whitespace_mapped_and_expanded_inputs(self):
        r=range_to_cidrs(' ::ffff:192.0.2.0 ','0000:0000:0000:0000:0000:ffff:c000:0203')
        self.assertEqual(r.cidrs,(IPv6Network('::ffff:c000:200/126'),))

    def test_english_examples_preserve_records_and_planning_results(self):
        root=Path(__file__).resolve().parents[1]/'examples'
        for name in ('SubnetList','PlanningNetworks'):
            cn=(root/(name+'.txt')).read_text();en=(root/(name+'_EN.txt')).read_text()
            self.assertNotRegex(en,r'[\u4e00-\u9fff]')
            self.assertEqual(analyze_subnet_list(cn),analyze_subnet_list(en))
            if name=='PlanningNetworks':
                self.assertTrue(en.startswith('# Parent network: 2026:1015:abcd::/48'))
                self.assertEqual(free_space(cn,'2026:1015:abcd::/48'),free_space(en,'2026:1015:abcd::/48'))
                self.assertEqual(aggregate_cidrs(cn),aggregate_cidrs(en))
        a=load_plan(root/'OfficeNetwork.json');b=load_plan(root/'OfficeNetwork_EN.json')
        self.assertEqual(a.network,b.network);self.assertEqual(a.target_prefix,b.target_prefix);self.assertEqual(replace(a,name=b.name,notes=b.notes),b)


class AddressRangeUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.app=create_application([],QSettings(str(Path(cls.tmp.name)/'prefs.ini'),QSettings.Format.IniFormat));cls.app.setQuitOnLastWindowClosed(False)

    @classmethod
    def tearDownClass(cls):
        cls.app.language_manager.apply('zh_CN',persist=False);cls.tmp.cleanup()

    def setUp(self):
        self.app.language_manager.apply('zh_CN',persist=False)
        self.w=MainWindow();self.w.show();self.w.calculate();self.p=self.w.address_tools_page.range_panel

    def tearDown(self):
        if self.w.subnet_list_page.service.busy:self.w.subnet_list_page.cancel();self.wait(lambda:not self.w.subnet_list_page.service.busy)
        self.app.language_manager.apply('zh_CN',persist=False)
        self.w.plan_controller.path=None;self.w.close();self.w.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);QApplication.processEvents()

    def wait(self,condition):
        deadline=monotonic()+5
        while monotonic()<deadline:
            QApplication.processEvents()
            if condition():return
            QTest.qWait(3)
        self.fail('Qt timeout')

    def test_buttons_initially_disabled_and_edits_clear_only_range_result(self):
        self.assertFalse(self.p.copy_button.isEnabled());self.assertFalse(self.p.transfer_button.isEnabled())
        self.w.address_tools_page.convert();formats=self.w.address_tools_page.formats
        self.p.convert();self.assertTrue(self.p.copy_button.isEnabled())
        self.p.end_input.setText('::1');self.assertIsNone(self.p.result);self.assertEqual(self.p.output.toPlainText(),'')
        self.assertIs(self.w.address_tools_page.formats,formats)

    def test_validation_and_edit_recovery(self):
        self.p.start_input.setText('::2');self.p.end_input.setText('::1');self.p.convert()
        self.assertTrue(self.p.end_input.property('invalid'));self.assertFalse(self.p.copy_button.isEnabled())
        self.p.end_input.setText('::3');self.assertFalse(self.p.end_input.property('invalid'))
        self.p.convert();self.assertEqual(self.p.result.address_count,2)

    def test_language_switch_preserves_result_and_translates_summary_and_error(self):
        self.p.convert();result=self.p.result;output=self.p.output.toPlainText()
        self.app.language_manager.apply('en_US',persist=False)
        self.assertIs(self.p.result,result);self.assertEqual(self.p.output.toPlainText(),output)
        self.assertIn('CIDRs:',self.p.summary.text())
        self.p.end_input.setText('bad');self.p.convert()
        self.assertNotRegex(self.w.feedback.text(),r'[\u4e00-\u9fff]')
        self.assertIn('Last address',self.w.feedback.text())

    def test_copy_cidrs_and_localized_report(self):
        self.p.convert()
        with patch.object(self.w.clipboard,'copy_text') as copy:
            self.p.copy_cidrs();self.assertEqual(copy.call_args.args[0],self.p.result.cidr_text())
        self.app.language_manager.apply('en_US',persist=False)
        self.p.copy_report();self.assertIn('IPv6 Address Range to CIDR',QApplication.clipboard().text())
        self.assertNotRegex(QApplication.clipboard().text(),r'[\u4e00-\u9fff]')

    def test_transfer_to_empty_list_runs_check_and_preserves_calculation(self):
        result=self.w.result;before=self.w.plan_controller.snapshot();self.p.convert();self.p.send_to_list()
        page=self.w.subnet_list_page;self.wait(lambda:not page.service.busy)
        self.assertIs(self.w.tabs.currentWidget(),page);self.assertEqual(page.editor.toPlainText(),self.p.result.cidr_text())
        self.assertEqual(page.analysis.error_count,0);self.assertIs(self.w.result,result)
        # Only the currently viewed tab changes; calculation and result paging stay intact.
        after=self.w.plan_controller.snapshot();self.assertEqual(before.network,after.network);self.assertEqual(before.target_prefix,after.target_prefix)

    def test_transfer_cancel_keeps_existing_input_and_planning(self):
        page=self.w.subnet_list_page;page.editor.setPlainText('# My allocation\n::/127')
        self.p.convert();current=self.w.tabs.currentIndex()
        with patch('ui.range_transfer_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.No) as question:self.p.send_to_list()
        self.assertEqual(page.editor.toPlainText(),'# My allocation\n::/127');self.assertEqual(self.w.tabs.currentIndex(),current)
        self.assertEqual(question.call_args.args[-1],QMessageBox.StandardButton.No)

    def test_transfer_confirm_replaces_and_rechecks(self):
        page=self.w.subnet_list_page;page.editor.setPlainText('::/128');self.p.convert()
        with patch('ui.range_transfer_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes):self.p.send_to_list()
        self.wait(lambda:not page.service.busy)
        self.assertEqual(page.editor.toPlainText(),self.p.result.cidr_text());self.assertEqual(page.analysis.error_count,0)

    def test_busy_or_changed_list_is_not_overwritten(self):
        page=self.w.subnet_list_page;page.editor.setPlainText('::/128');self.p.convert()
        with patch.object(type(page.service),'busy',new_callable=PropertyMock,return_value=True):self.p.send_to_list()
        self.assertEqual(page.editor.toPlainText(),'::/128')
        def changed(*args):page.editor.setPlainText('::2/128');return QMessageBox.StandardButton.Yes
        with patch('ui.range_transfer_controller.QMessageBox.question',side_effect=changed):self.p.send_to_list()
        self.assertEqual(page.editor.toPlainText(),'::2/128');self.assertFalse(page.service.busy)

    def test_range_panel_is_accessible_at_minimum_size_both_languages_and_themes(self):
        self.w.resize(900,620);self.w.tabs.setCurrentWidget(self.w.address_tools_page)
        for language in ('zh_CN','en_US'):
            self.app.language_manager.apply(language,persist=False)
            for theme in ('light','dark'):
                self.app.theme_manager.apply(theme,persist=False)
                self.w.address_tools_page.findChild(QScrollArea).ensureWidgetVisible(self.p)
                QApplication.processEvents()
                for widget in (self.p.start_input,self.p.end_input,self.p.transfer_button):
                    self.assertLessEqual(widget.mapTo(self.w,widget.rect().bottomRight()).x(),self.w.width())
                self.assertGreater(self.p.start_input.width(),100)


if __name__=='__main__':unittest.main()
