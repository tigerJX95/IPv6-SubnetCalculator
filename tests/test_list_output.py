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

"""实际 TXT 内容、对话框事务保护和规划回流回归。"""
import errno,tempfile,unittest
from dataclasses import replace
from pathlib import Path
from time import monotonic
from unittest.mock import patch,PropertyMock
from PyQt6.QtCore import QSettings,QCoreApplication,QEvent
from PyQt6.QtWidgets import QApplication,QToolButton
from PyQt6.QtTest import QTest
from app import create_application
from services.text_output import save_text_atomic
from services.subnet_list_service import load_subnet_list
from core.subnet_list import analyze_subnet_list
from core.subnet_planning import free_space,aggregate_cidrs
from ui.main_window import MainWindow
from ui.standard_dialogs import QMessageBox


class AtomicTextTests(unittest.TestCase):
    def test_utf8_original_comments_bom_and_newlines_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'清单.txt';text='\ufeff# 用户备注\n::/127\n\n'
            save_text_atomic(path,text);self.assertEqual(path.read_bytes(),text.encode('utf-8'))
            self.assertEqual(list(Path(td).iterdir()),[path])

    def test_success_replaces_existing_file(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'out.txt';path.write_bytes(b'original')
            save_text_atomic(path,'new\n');self.assertEqual(path.read_bytes(),b'new\n')

    def test_failed_replace_preserves_existing_and_removes_temporary(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'out.txt';path.write_bytes(b'original')
            with patch('services.text_output.os.replace',side_effect=PermissionError(errno.EACCES,'denied')):
                with self.assertRaises(PermissionError):save_text_atomic(path,'replacement')
            self.assertEqual(path.read_bytes(),b'original');self.assertEqual(list(Path(td).iterdir()),[path])

    def test_invalid_unicode_does_not_create_or_replace_files(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'out.txt';path.write_bytes(b'original')
            with self.assertRaises(UnicodeEncodeError):save_text_atomic(path,'\ud800')
            self.assertEqual(path.read_bytes(),b'original');self.assertEqual(list(Path(td).iterdir()),[path])

    def test_missing_directory_has_no_output(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'missing/out.txt'
            with self.assertRaises(OSError):save_text_atomic(path,'data')
            self.assertEqual(list(Path(td).iterdir()),[])


class ListOutputUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.app=create_application([],QSettings(str(Path(cls.temp.name)/'prefs.ini'),QSettings.Format.IniFormat));cls.app.setQuitOnLastWindowClosed(False)

    @classmethod
    def tearDownClass(cls):
        cls.app.language_manager.apply('zh_CN',persist=False);cls.temp.cleanup()

    def setUp(self):
        self.app.language_manager.apply('zh_CN',persist=False)
        self.w=MainWindow();self.w.show();self.w.calculate();self.page=self.w.subnet_list_page
        self.c=self.page.output_controller;self.p=self.page.planning
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'输出.txt'

    def tearDown(self):
        if self.page.service.busy:self.page.cancel();self.wait(lambda:not self.page.service.busy)
        self.app.language_manager.apply('zh_CN',persist=False)
        self.w.plan_controller.path=None;self.w.close();self.w.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);QApplication.processEvents();self.tmp.cleanup()

    def wait(self,condition):
        deadline=monotonic()+5
        while monotonic()<deadline:
            QApplication.processEvents()
            if condition():return
            QTest.qWait(3)
        self.fail('Qt timeout')

    def analysis(self,text='# 用户注释\n::/127\n::/127\n::2/127\nbad'):
        self.page.editor.setPlainText(text);self.page.set_analysis(analyze_subnet_list(text))
        return self.page.analysis

    def planning(self,task='free'):
        text='::/127\n::2/127';self.page.editor.setPlainText(text)
        self.p.parent_input.setText('::/124')
        result=free_space(text,'::/124') if task=='free' else aggregate_cidrs(text)
        self.p.completed(task,('ok',result));self.p.refresh_buttons();return result

    def save(self,callback,path=None):
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(path or self.path),'文本文件 (*.txt)')):callback()

    def test_menus_translate_and_enable_only_available_outputs(self):
        self.assertFalse(self.page.save_button.isEnabled())
        self.page.editor.setPlainText('# Note')
        self.assertTrue(self.c.actions['input'].isEnabled());self.assertFalse(self.c.actions['networks'].isEnabled())
        self.analysis();self.assertTrue(self.c.actions['networks'].isEnabled());self.assertTrue(self.c.actions['list_report'].isEnabled())
        self.app.language_manager.apply('en_US',persist=False)
        self.assertEqual(self.c.actions['input'].text(),'Save Original Input as TXT')
        self.assertNotRegex(self.page.save_button.toolTip(),r'[\u4e00-\u9fff]')
        self.assertEqual(self.page.save_button.popupMode(),QToolButton.ToolButtonPopupMode.InstantPopup)

    def test_raw_save_without_analysis_preserves_user_text_in_english_ui(self):
        text='# 父网段：::/0\nnot valid\n\n';self.page.editor.setPlainText(text)
        self.app.language_manager.apply('en_US',persist=False);self.save(self.c.save_input)
        self.assertEqual(self.path.read_bytes(),text.encode());self.assertIn('Text saved',self.w.feedback.text())

    def test_normalized_save_skips_errors_and_reimports_with_same_cidrs(self):
        result=self.analysis();self.save(self.c.save_networks)
        self.assertEqual(self.path.read_text(),'::/127\n::2/127\n')
        imported=analyze_subnet_list(load_subnet_list(self.path))
        self.assertEqual(imported.error_count,0);self.assertEqual(imported.unique_networks,result.unique_networks)

    def test_all_error_list_can_save_report_but_not_valid_cidrs(self):
        self.analysis('bad\ninvalid')
        self.assertFalse(self.c.actions['networks'].isEnabled());self.assertTrue(self.c.actions['list_report'].isEnabled())
        self.save(self.c.save_list_report);self.assertIn('bad',self.path.read_text())

    def test_report_language_selected_during_picker_and_user_text_preserved(self):
        self.analysis('::/127\n用户内容')
        def select(*args,**kwargs):self.app.language_manager.apply('en_US',persist=False);return str(self.path),'Text Files (*.txt)'
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=select):self.c.save_list_report()
        text=self.path.read_text();self.assertIn('IPv6 Subnet List Check Report',text);self.assertIn('用户内容',text);self.assertNotIn('有效网段',text)

    def test_planning_cidrs_and_reports_both_languages(self):
        for task in ('free','aggregate'):
            for language in ('zh_CN','en_US'):
                result=self.planning(task);self.app.language_manager.apply(language,persist=False)
                path=Path(self.tmp.name)/(task+language+'.txt')
                self.save(lambda:self.c.save_planning(task),path)
                self.assertEqual(analyze_subnet_list(load_subnet_list(path)).unique_networks,result.cidrs)
                report=Path(self.tmp.name)/(task+language+'_report.txt')
                self.save(lambda:self.c.save_planning(task,report=True),report)
                if language=='en_US':self.assertNotRegex(report.read_text(),r'[\u4e00-\u9fff]')
                self.assertIn(str(result.cidrs[0]),report.read_text())

    def test_truncated_free_result_blocks_cidr_save_and_transfer_but_allows_report(self):
        result=self.planning();partial=replace(result,cidr_count=len(result.cidrs)+1)
        self.p.free_result=partial;self.p.refresh_buttons()
        self.assertFalse(self.c.actions['free_cidrs'].isEnabled());self.assertFalse(self.p.send_free_button.isEnabled())
        self.assertTrue(self.c.actions['free_report'].isEnabled())
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName') as picker:self.c.save_planning('free')
        picker.assert_not_called()
        self.save(lambda:self.c.save_planning('free',report=True))
        self.assertIn('全部空闲地址范围',self.path.read_text());self.assertIn('截断',self.path.read_text())

    def test_zero_free_result_saves_report_only(self):
        self.page.editor.setPlainText('::/124');self.p.free_result=free_space('::/124','::/124');self.p.refresh_buttons()
        self.assertFalse(self.c.actions['free_cidrs'].isEnabled());self.assertFalse(self.p.send_free_button.isEnabled())
        self.assertTrue(self.c.actions['free_report'].isEnabled())
        self.save(lambda:self.c.save_planning('free',report=True));self.assertIn('空闲地址数：0',self.path.read_text())

    def test_extension_completion_uppercase_and_wrong_extension(self):
        self.page.editor.setPlainText('::/127')
        path=Path(self.tmp.name)/'无扩展名';self.save(self.c.save_input,path);self.assertTrue(path.with_suffix('.txt').is_file())
        path=Path(self.tmp.name)/'upper.TXT';self.save(self.c.save_input,path);self.assertTrue(path.is_file())
        path=Path(self.tmp.name)/'wrong.csv';self.save(self.c.save_input,path);self.assertFalse(path.exists())

    def test_cancel_picker_and_overwrite_keep_existing(self):
        self.page.editor.setPlainText('::/127')
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=('','')):self.c.save_input()
        self.assertFalse(self.path.exists())
        self.path.write_bytes(b'original')
        with patch('ui.list_output_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.No) as question:self.save(self.c.save_input)
        self.assertEqual(self.path.read_bytes(),b'original');self.assertEqual(question.call_args.args[-1],QMessageBox.StandardButton.No)

    def test_input_change_while_picker_open_rejects_stale_save(self):
        self.page.editor.setPlainText('::/127')
        def select(*args,**kwargs):self.page.editor.setPlainText('::2/127');return str(self.path),'Text Files (*.txt)'
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',side_effect=select):self.c.save_input()
        self.assertFalse(self.path.exists());self.assertIn('已变化',self.w.feedback.text())

    def test_parent_change_during_overwrite_keeps_existing_file(self):
        self.planning();self.path.write_bytes(b'original')
        def changed(*args):self.p.parent_input.setText('::/123');return QMessageBox.StandardButton.Yes
        with patch('ui.list_output_controller.QMessageBox.question',side_effect=changed):self.save(lambda:self.c.save_planning('free'))
        self.assertEqual(self.path.read_bytes(),b'original')

    def test_failed_write_does_not_change_state_or_existing_file(self):
        result=self.analysis();self.path.write_bytes(b'original')
        with patch('ui.list_output_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes),patch('ui.list_output_controller.save_text_atomic',side_effect=PermissionError(errno.EACCES,'denied')):self.save(self.c.save_list_report)
        self.assertIs(self.page.analysis,result);self.assertEqual(self.path.read_bytes(),b'original');self.assertEqual(self.w.feedback.property('severity'),'error')

    def test_busy_state_disables_all_output_and_transfer_actions(self):
        self.analysis()
        with patch.object(type(self.page.service),'busy',new_callable=PropertyMock,return_value=True):
            self.c.refresh();self.assertTrue(all(not a.isEnabled() for a in self.c.actions.values()))
            with patch('ui.list_output_controller.QFileDialog.getSaveFileName') as picker:self.c.save_input()
            picker.assert_not_called()

    def test_planning_transfer_confirm_runs_relations_and_preserves_calculation(self):
        for task in ('free','aggregate'):
            result=self.planning(task);calculation=self.w.result
            with patch('ui.range_transfer_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes):self.c.send_planning(task)
            self.wait(lambda:not self.page.service.busy)
            self.assertEqual(self.page.editor.toPlainText(),result.cidr_text());self.assertEqual(self.page.analysis.error_count,0)
            self.assertIs(self.w.result,calculation);self.assertIsNone(getattr(self.p,task+'_result'))

    def test_transfer_decline_preserves_input_and_result(self):
        result=self.planning('aggregate');before=self.page.editor.toPlainText()
        with patch('ui.range_transfer_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.No):self.c.send_planning('aggregate')
        self.assertEqual(self.page.editor.toPlainText(),before);self.assertIs(self.p.aggregate_result,result)

    def test_parent_change_during_transfer_confirmation_rejects_stale_result(self):
        self.planning();before=self.page.editor.toPlainText()
        def changed(*args):self.p.parent_input.setText('::/123');return QMessageBox.StandardButton.Yes
        with patch('ui.range_transfer_controller.QMessageBox.question',side_effect=changed):self.c.send_planning('free')
        self.assertEqual(self.page.editor.toPlainText(),before);self.assertFalse(self.page.service.busy)

    def test_new_actions_fit_minimum_window_in_both_languages_and_themes(self):
        self.w.resize(900,620);self.w.tabs.setCurrentWidget(self.page)
        for language in ('zh_CN','en_US'):
            self.app.language_manager.apply(language,persist=False)
            for theme in ('light','dark'):
                self.app.theme_manager.apply(theme,persist=False)
                for index in (0,2,3):
                    self.page.result_tabs.setCurrentIndex(index);QApplication.processEvents()
                    buttons=[self.page.save_button] if index==0 else [self.p.save_free_button,self.p.send_free_button] if index==2 else [self.p.save_aggregate_button,self.p.send_aggregate_button]
                    for button in buttons:
                        pos=button.mapTo(self.w,button.rect().bottomRight());self.assertLess(pos.x(),self.w.width());self.assertLess(pos.y(),self.w.height())


if __name__=='__main__':unittest.main()
