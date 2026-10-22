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

"""对齐容量的独立枚举校验、巨大空间边界与追加事务回归。"""
import random, tempfile, unittest
from pathlib import Path
from ipaddress import IPv6Address, IPv6Network
from unittest.mock import patch
from time import monotonic
from PyQt6.QtCore import QSettings,QCoreApplication,QEvent
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from app import create_application
from core.subnet_planning import free_space
from core.subnet_allocation import suggest_subnets
from core.ipv6_core import InputError
from ui.main_window import MainWindow
from ui.standard_dialogs import QMessageBox
from services.language_service import display


class AllocationCoreTests(unittest.TestCase):
    def test_empty_parent_capacity_and_order(self):
        free=free_space('', '2026:1015:abcd::/48')
        result=suggest_subnets(free,'/64','3')
        self.assertEqual(result.capacity,65536)
        self.assertEqual(list(map(str,result.cidrs)),['2026:1015:abcd::/64','2026:1015:abcd:1::/64','2026:1015:abcd:2::/64'])
        self.assertEqual(free.input_count,0)

    def test_full_ipv6_space_exact_integer_capacity(self):
        result=suggest_subnets(free_space('','::/0'),128,5000)
        self.assertEqual(result.capacity,2**128)
        self.assertEqual(len(result.cidrs),5000)
        self.assertEqual(str(result.cidrs[-1]),'::1387/128')

    def test_prefix_zero_and_last_ipv6_address(self):
        self.assertEqual(suggest_subnets(free_space('','::/0'),0,1).cidrs,(IPv6Network('::/0'),))
        free=free_space('','ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128')
        self.assertEqual(suggest_subnets(free,128,1).cidrs,(free.parent,))

    def test_fragmentation_not_total_address_division(self):
        free=free_space('::1/128\n::5/128\n::9/128\n::d/128','::/124')
        self.assertEqual(free.free_addresses,12)
        result=suggest_subnets(free,126,1)
        self.assertEqual(result.capacity,0)
        self.assertEqual(result.cidrs,())
        self.assertFalse(result.sufficient)

    def test_insufficient_capacity_has_no_partial_suggestions(self):
        result=suggest_subnets(free_space('::/127','::/126'),127,2)
        self.assertEqual((result.capacity,result.cidrs),(1,()))
        self.assertEqual(suggest_subnets(result.free,127,1).cidrs,(IPv6Network('::2/127'),))

    def test_full_occupancy_and_duplicates(self):
        free=free_space('::/126\n::/126\n::1/128','::/126')
        self.assertEqual(suggest_subnets(free,128,1).capacity,0)

    def test_invalid_prefix_and_count(self):
        free=free_space('','::/64')
        for value in ['63','129','-1','64.0','/','64/','六四','9'*1000]:
            with self.subTest(value=value),self.assertRaises(InputError):suggest_subnets(free,value,1)
        for value in ['0','5001','-1','1.5','+1','一','9'*1000]:
            with self.subTest(value=value),self.assertRaises(InputError):suggest_subnets(free,64,value)

    def test_truncated_free_cidrs_still_use_all_ranges(self):
        text='\n'.join(f'{IPv6Address((i<<112)+1)}/128' for i in range(100))
        free=free_space(text,'::/0')
        self.assertFalse(free.complete)
        result=suggest_subnets(free,128,3)
        self.assertEqual(result.capacity,2**128-100)
        self.assertEqual(list(map(str,result.cidrs)),['::/128','::2/128','::3/128'])

    def test_seeded_capacity_matches_independent_address_enumeration(self):
        randomizer=random.Random(110)
        for case in range(40):
            occupied=set(randomizer.sample(range(256),randomizer.randrange(50)))
            text='\n'.join(f'{IPv6Address(x)}/128' for x in occupied)
            free=free_space(text,'::/120')
            for prefix in range(120,129):
                block=2**(128-prefix)
                starts=[start for start in range(0,256,block) if set(range(start,start+block)).isdisjoint(occupied)]
                result=suggest_subnets(free,prefix,min(5,len(starts)) or 1)
                self.assertEqual(result.capacity,len(starts),(case,prefix))
                self.assertEqual([int(x.network_address) for x in result.cidrs],starts[:min(5,len(starts))])


class AllocationUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.app=create_application([],QSettings(str(Path(cls.temp.name)/'prefs.ini'),QSettings.Format.IniFormat))
        cls.app.setQuitOnLastWindowClosed(False)

    @classmethod
    def tearDownClass(cls):
        cls.app.language_manager.apply('zh_CN',persist=False);cls.temp.cleanup()

    def setUp(self):
        self.app.language_manager.apply('zh_CN',persist=False)
        self.w=MainWindow();self.w.show();self.w.calculate()
        self.page=self.w.subnet_list_page;self.p=self.page.planning;self.v=self.p.allocation
        self.page.editor.setPlainText('# 保留用户备注\n2026:1015:abcd::/64\n')
        self.p.completed('free',('ok',free_space(self.page.editor.toPlainText(),self.p.parent_input.text())))
        self.p.refresh_buttons()
        self.v.count_input.setText('2');self.v.generate()

    def tearDown(self):
        self.w.subnet_list_page.project_controller.saved = self.w.subnet_list_page.project_controller.snapshot()
        self.wait_idle()
        self.app.language_manager.apply('zh_CN',persist=False)
        self.w.plan_controller.path=None;self.w.close();self.w.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);QApplication.processEvents()

    def wait_idle(self):
        deadline=monotonic()+8
        while self.page.service.busy:
            QApplication.processEvents();QTest.qWait(3)
            if monotonic()>deadline:self.fail('Qt timeout')

    def test_minimum_layout_keeps_status_and_candidate_row_visible(self):
        self.w.resize(900,620)
        self.w.tabs.setCurrentWidget(self.page)
        self.page.result_tabs.setCurrentWidget(self.v)
        for language in ('zh_CN','en_US'):
            for theme in ('light','dark'):
                self.app.language_manager.apply(language,persist=False)
                self.app.theme_manager.apply(theme,persist=False)
                QApplication.processEvents()
                self.assertFalse(self.page.editor.isVisible())
                self.assertTrue(self.v.append_button.isVisible())
                self.assertGreater(self.v.table.viewport().height(),35)
                self.assertGreaterEqual(self.v.status.height(),self.v.status.heightForWidth(self.v.status.width()))
        self.page.result_tabs.setCurrentWidget(self.p.free_page)
        self.assertTrue(self.page.editor.isVisible())

    def test_live_language_switch_preserves_result_and_user_content(self):
        result=self.v.result;original=self.page.editor.toPlainText()
        for language in ('en_US','zh_CN','en_US'):
            self.app.language_manager.apply(language,persist=False)
            self.assertIs(self.v.result,result)
            self.assertEqual(self.page.editor.toPlainText(),original)
        self.assertNotRegex(self.v.status.text(),r'[\u4e00-\u9fff：，。；、（）]')
        self.assertNotRegex(display(result.as_text()),r'[\u4e00-\u9fff]')
        self.assertIn('65,535',self.v.status.text())

    def test_cancel_remains_accessible_when_switching_to_allocation_during_work(self):
        self.w.tabs.setCurrentWidget(self.page)
        self.page.start_planning('free')
        self.page.result_tabs.setCurrentWidget(self.v)
        self.assertTrue(self.page.cancel_button.isVisible())
        self.page.cancel();self.wait_idle()
        self.assertFalse(self.page.action_bar.isVisible())

    def test_request_edit_invalidates_suggestions(self):
        self.v.prefix_input.setText('65')
        self.assertIsNone(self.v.result);self.assertEqual(self.v.model.rowCount(),0)
        self.assertFalse(self.v.append_button.isEnabled())
        self.assertIsNotNone(self.p.free_result)

    def test_parent_and_occupancy_edits_invalidate_capacity(self):
        self.p.parent_input.setText('::/0')
        self.assertIsNone(self.v.result);self.assertIsNone(self.p.free_result)
        self.assertFalse(self.v.generate_button.isEnabled())
        self.page.editor.setPlainText('::/128')
        self.assertFalse(self.v.copy_button.isEnabled())

    def test_insufficient_capacity_disables_cidr_and_append_but_keeps_report(self):
        self.v.prefix_input.setText('48');self.v.generate()
        self.assertEqual(self.v.result.capacity,0)
        self.assertFalse(self.v.append_button.isEnabled());self.assertFalse(self.v.copy_button.isEnabled())
        self.assertTrue(self.v.copy_report_button.isEnabled())

    def test_append_declined_preserves_all_state(self):
        before=self.page.editor.toPlainText();result=self.v.result
        with patch('ui.allocation_view.QMessageBox.question',return_value=QMessageBox.StandardButton.No):self.v.append()
        self.assertEqual(self.page.editor.toPlainText(),before);self.assertIs(self.v.result,result)

    def test_append_confirmed_retains_comments_and_recalculates(self):
        before=self.page.editor.toPlainText();calculation=self.w.result
        with patch('ui.allocation_view.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes):self.v.append()
        self.wait_idle()
        self.assertTrue(self.page.editor.toPlainText().startswith(before))
        self.assertIn('2026:1015:abcd:1::/64',self.page.editor.toPlainText())
        self.assertEqual(self.p.free_result.occupied_addresses,3*2**64)
        self.assertIs(self.w.result,calculation);self.assertIsNone(self.v.result)

    def test_append_rechecks_snapshot_after_confirmation(self):
        before=self.page.editor.toPlainText()
        def changed(*args):
            self.v.count_input.setText('3');return QMessageBox.StandardButton.Yes
        with patch('ui.allocation_view.QMessageBox.question',side_effect=changed):self.v.append()
        self.assertEqual(self.page.editor.toPlainText(),before)

    def test_combined_record_limit_blocks_append_without_mutation(self):
        text='\n'.join(['2026:1015:abcd::/64']*5000)
        self.page.editor.setPlainText(text)
        self.p.completed('free',('ok',free_space(text,self.p.parent_input.text())))
        self.p.refresh_buttons();self.v.generate()
        with patch('ui.allocation_view.QMessageBox.question') as question:self.v.append()
        question.assert_not_called();self.assertEqual(self.page.editor.toPlainText(),text)

    def test_busy_task_blocks_generation_and_append(self):
        result=self.v.result;text=self.page.editor.toPlainText()
        with patch('services.subnet_list_service.SubnetListService.busy',new_callable=__import__('unittest.mock',fromlist=['PropertyMock']).PropertyMock,return_value=True):
            self.v.refresh();self.v.generate();self.v.append()
            self.assertFalse(self.v.generate_button.isEnabled())
            self.assertIs(self.v.result,result);self.assertEqual(self.page.editor.toPlainText(),text)

    def test_report_save_uses_language_at_save_time(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'report.txt'
            def choose(*args,**kwargs):
                self.app.language_manager.apply('en_US',persist=False)
                return str(path),''
            with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=choose):self.page.output_controller.save_allocation(report=True)
            self.assertIn('Total available subnets: 65,535',path.read_text())
            self.assertNotRegex(path.read_text(),r'[\u4e00-\u9fff]')

    def test_save_rejects_changed_result(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'out.txt'
            def choose(*args,**kwargs):
                self.v.count_input.setText('3');return str(path),''
            with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=choose):self.page.output_controller.save_allocation()
            self.assertFalse(path.exists())
