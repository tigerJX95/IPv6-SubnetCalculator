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

"""双语切换的消息参数、业务状态、资源完整性和偏好回归。"""
import ast,json,re,tempfile,unittest,subprocess,sys,os
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch
from time import monotonic
from PyQt6.QtCore import QSettings,QCoreApplication,QEvent,Qt,QTimer,QLocale
from PyQt6.QtWidgets import QApplication,QLabel,QLineEdit,QDialog
from PyQt6.QtTest import QTest
from app import create_application
from app_info import APP_NAME,APP_VERSION
from core.localized_text import text,join_text,Text
from services.language_service import display
from services.plan_storage import save_plan,load_plan
from services.error_messages import describe_error
from core.ipv6_core import calculate
from core.subnet_list import analyze_subnet_list
from ui.main_window import MainWindow
from ui.dialogs import RangeCopyDialog,ExportRangeDialog
from ui.standard_dialogs import QMessageBox,QFileDialog


class I18nTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.settings=QSettings(str(Path(cls.tmp.name)/'prefs.ini'),QSettings.Format.IniFormat)
        cls.app=create_application([],cls.settings)
        cls.app.setQuitOnLastWindowClosed(False)
        cls.previous_settings=cls.app.language_manager.settings
        cls.app.language_manager.settings=cls.settings

    @classmethod
    def tearDownClass(cls):
        cls.app.language_manager.apply('zh_CN',persist=False)
        cls.app.language_manager.settings=cls.previous_settings
        cls.tmp.cleanup()

    def setUp(self):
        self.app.language_manager.apply('zh_CN',persist=False)
        self.app.theme_manager.apply('light',persist=False)
        self.window=MainWindow();self.window.show();self.window.calculate()
        QApplication.processEvents()

    def tearDown(self):
        page=self.window.subnet_list_page
        if page.service.busy:
            page.cancel();self.wait(lambda:not page.service.busy)
        self.app.language_manager.apply('zh_CN',persist=False)
        self.window.plan_controller.path=None
        self.window.calculation_page.plan_name_input.clear();self.window.calculation_page.plan_notes_input.clear()
        self.window.close();self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);QApplication.processEvents()

    def wait(self,condition,timeout=5):
        limit=monotonic()+timeout
        while monotonic()<limit:
            QApplication.processEvents()
            if condition():return
            QTest.qWait(4)
        self.fail('Qt operation timed out')

    def switch(self,name='en_US'):
        self.window.language_button.choose(name);QApplication.processEvents()

    def test_language_menu_order_native_names_and_checked_state(self):
        buttons=[self.window.language_button,self.window.theme_button,self.window.about_button]
        self.assertLess(buttons[0].mapTo(self.window,buttons[0].rect().topLeft()).x(),buttons[1].mapTo(self.window,buttons[1].rect().topLeft()).x())
        self.assertLess(buttons[1].mapTo(self.window,buttons[1].rect().topLeft()).x(),buttons[2].mapTo(self.window,buttons[2].rect().topLeft()).x())
        self.assertEqual([a.text() for a in self.window.language_button.menu.actions()],['简体中文','English'])
        self.switch();self.assertTrue(self.window.language_button.actions_by_language['en_US'].isChecked())
        self.switch();self.assertTrue(self.window.language_button.actions_by_language['en_US'].isChecked())
        self.assertFalse(self.window.language_button.icon().isNull())

    def test_selection_paging_location_and_calculation_identity_preserved(self):
        page=self.window.results_page
        page.locator_mode_combo.setCurrentIndex(3);page.locator_input.setText('190-210');page.locate()
        page.table.selectRow(3)
        before=self.window.plan_controller.snapshot();result=self.window.result
        selection=list(page.selected_indices());rows=list(page.model.records)
        for lang in ('en_US','zh_CN','en_US'):
            self.switch(lang)
            self.assertEqual(before,self.window.plan_controller.snapshot())
            self.assertIs(result,self.window.result)
            self.assertEqual(selection,page.selected_indices());self.assertEqual(rows,page.model.records)
        self.assertEqual(page.model.headerData(0,Qt.Orientation.Horizontal),'Index')
        self.assertEqual(self.window.tabs.tabText(0),'Calculation')
        self.assertIn('IPv6 Subnet Calculator',self.window.windowTitle())

    def test_user_input_notes_names_and_json_remain_unchanged(self):
        page=self.window.calculation_page
        page.plan_name_input.setText('计算完成。');page.plan_notes_input.setPlainText('子网计算 / 未保存 / User notes')
        plan=self.window.plan_controller.snapshot()
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'计算完成。.json';save_plan(path,plan);before=path.read_bytes()
            self.switch();self.assertEqual(page.plan_name_input.text(),'计算完成。')
            self.assertEqual(page.plan_notes_input.toPlainText(),'子网计算 / 未保存 / User notes')
            save_plan(path,self.window.plan_controller.snapshot())
            self.assertEqual(before,path.read_bytes());self.assertEqual(load_plan(path),plan)

    def test_address_results_and_readonly_browsing_not_recalculated(self):
        page=self.window.address_tools_page;page.convert();page.analyze()
        formats,relation=page.formats,page.relation
        with patch.object(self.window,'calculate') as calc,patch.object(page,'convert') as convert,patch.object(page,'analyze') as analyze:
            self.switch()
        calc.assert_not_called();convert.assert_not_called();analyze.assert_not_called()
        self.assertIs(page.formats,formats);self.assertIs(page.relation,relation)
        self.assertIn('A contains B',page.relation_title.text())
        self.assertIn('All addresses',page.relation_detail.text())

    def test_existing_input_error_and_warning_tooltip_retranslate(self):
        page=self.window.calculation_page;page.target_input.setText('47');self.window.calculate()
        self.assertTrue(page.target_input.property('invalid'));self.switch()
        self.assertIn('target prefix',self.window.feedback.text())
        self.assertIn('target prefix',page.target_input._input_error_action.toolTip())
        self.assertTrue(page.target_input.property('invalid'))
        self.switch('zh_CN');self.assertIn('目标',self.window.feedback.text())

    def test_new_error_after_switch_uses_current_language(self):
        self.switch();page=self.window.address_tools_page
        page.network_b_input.setText('bad');page.analyze()
        self.assertIn('Network B',self.window.feedback.text())
        self.assertNotRegex(self.window.feedback.text(),r'[\u4e00-\u9fff]')

    def test_list_records_free_and_aggregation_survive_switch(self):
        page=self.window.subnet_list_page
        raw='# 用户输入不翻译\n::/127\n::2/127'
        page.editor.setPlainText(raw);page.planning.parent_input.setText('::/124');page.analyze();self.wait(lambda:not page.service.busy)
        page.start_planning('free');self.wait(lambda:not page.service.busy)
        page.start_planning('aggregate');self.wait(lambda:not page.service.busy)
        analysis,free,aggregate=page.analysis,page.planning.free_result,page.planning.aggregate_result
        self.switch()
        self.assertEqual(page.editor.toPlainText(),raw)
        self.assertIs(page.analysis,analysis);self.assertIs(page.planning.free_result,free);self.assertIs(page.planning.aggregate_result,aggregate)
        self.assertEqual(page.record_model.data(page.record_model.index(0,3)),'Valid')
        self.assertIn('Input 2',page.planning.aggregate_status.text())
        self.assertEqual(page.result_tabs.tabText(2),'Free Space')

    def test_worker_finishes_in_language_current_at_completion(self):
        page=self.window.subnet_list_page
        page.editor.setPlainText('::/127\n::2/127');page.analyze();self.switch()
        self.wait(lambda:not page.service.busy)
        self.assertIn('List check complete',self.window.feedback.text())
        self.assertNotRegex(self.window.feedback.text(),r'[\u4e00-\u9fff]')

    def test_about_open_window_tabs_and_original_license_preserved(self):
        self.window.show_about();about=self.window.about_dialog
        about.tabs.setCurrentIndex(2);about.license_selector.setCurrentIndex(1)
        original=about.licenses.toPlainText();index=about.license_selector.currentIndex()
        self.switch()
        self.assertIs(about,self.window.about_dialog);self.assertEqual(about.tabs.currentIndex(),2)
        self.assertEqual(about.license_selector.currentIndex(),index);self.assertEqual(about.licenses.toPlainText(),original)
        self.assertIn('Runtime Components',about.information.toPlainText())
        self.assertIn('User Guide',about.usage.toPlainText());self.assertNotRegex(about.usage.toPlainText().replace('简体中文',''),r'[\u4e00-\u9fff]')
        self.assertIn('Warranty',about.legal.toPlainText())
        self.switch('zh_CN');self.assertIn('使用说明',about.tabs.tabText(1))

    def test_locator_modes_have_language_independent_semantics(self):
        self.switch();page=self.window.results_page
        for mode,value,first in ((0,'2026:1015:abcd::1',1),(1,'200',200),(2,'2026:1015:abcd::1 - 2026:1015:abcd:1::1',1),(3,'1000-1500',1000)):
            page.locator_mode_combo.setCurrentIndex(mode);page.locator_input.setText(value);page.locate()
            self.assertEqual(page.selected_indices(),[first])

    def test_range_dialog_labels_and_errors_english(self):
        self.switch();dialog=RangeCopyDialog(self.window.result,self.window.clipboard,parent=self.window)
        self.assertIn('Copy Subnets',dialog.windowTitle())
        self.assertIn('First index:',[x.text() for x in dialog.findChildren(QLabel)])
        dialog.start_input.setText('bad')
        with patch('ui.dialogs.QMessageBox.warning'):dialog.perform()
        self.assertIn('positive integer',dialog.input_feedback.text())
        dialog.deleteLater()

    def test_actual_english_question_and_safe_default(self):
        self.switch();errors=[]
        def inspect():
            box=QApplication.activeModalWidget()
            try:
                self.assertEqual(box.button(QMessageBox.StandardButton.Yes).text(),'Yes')
                self.assertEqual(box.button(QMessageBox.StandardButton.No).text(),'No')
                self.assertIs(box.defaultButton(),box.button(QMessageBox.StandardButton.No))
                self.assertEqual(box.windowTitle(),'Overwrite Plan')
            except Exception as exc:errors.append(exc)
            box.button(QMessageBox.StandardButton.No).click()
        QTimer.singleShot(0,inspect)
        QMessageBox.question(self.window,text('覆盖方案'),text('目标文件已存在，是否覆盖？'))
        if errors:raise errors[0]

    def test_file_picker_and_standard_qt_controls_english(self):
        self.switch()
        self.assertIn('Select All',QCoreApplication.translate('QLineEdit','Select All'))
        self.assertIn('bytes',QLocale().formattedDataSize(389))
        def inspect(dialog):
            self.assertEqual(dialog.windowTitle(),'Open Calculation Plan')
            self.assertEqual(dialog.labelText(QFileDialog.DialogLabel.FileName),'File name:')
            self.assertEqual(dialog.labelText(QFileDialog.DialogLabel.Reject),'Cancel')
            return QDialog.DialogCode.Rejected
        with patch.object(QFileDialog,'exec',inspect):
            QFileDialog.getOpenFileName(self.window,text('打开计算方案'),'',text('IPv6 计算方案 (*.json)'))

    def test_preference_failure_shows_translated_message(self):
        with patch.object(self.settings,'status',return_value=QSettings.Status.AccessError):self.switch()
        self.assertEqual(self.app.language_manager.name,'en_US')
        self.assertIn('could not be saved',self.window.feedback.text())
        self.assertEqual(self.window.feedback.property('severity'),'error')

    def test_language_preference_roundtrip_and_invalid_choice(self):
        self.switch();self.assertEqual(self.settings.value('appearance/language'),'en_US')
        self.switch('zh_CN');self.assertEqual(self.settings.value('appearance/language'),'zh_CN')
        with self.assertRaises(ValueError):self.app.language_manager.apply('unknown')

    def test_restart_restores_language_and_bad_preference_falls_back(self):
        root=Path(__file__).resolve().parents[1]
        code="import sys;from PyQt6.QtCore import QSettings;from app import create_application;app=create_application([],QSettings(sys.argv[1],QSettings.Format.IniFormat));print(app.language_manager.name)"
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'restart.ini';prefs=QSettings(str(path),QSettings.Format.IniFormat)
            for value,expected in (('en_US','en_US'),('zh_CN','zh_CN'),('unknown','zh_CN')):
                prefs.setValue('appearance/language',value);prefs.sync()
                result=subprocess.run([sys.executable,'-c',code,str(path)],cwd=root,env=os.environ.copy(),capture_output=True,text=True,timeout=15)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(result.stdout.strip(),expected)

    def test_file_picker_live_switch_preserves_entered_filename(self):
        def inspect(dialog):
            editor=dialog.findChild(QLineEdit,'fileNameEdit')
            editor.setText('计算完成。.json')
            self.switch()
            self.assertEqual(dialog.labelText(QFileDialog.DialogLabel.FileName),'File name:')
            self.assertEqual(editor.text(),'计算完成。.json')
            self.switch('zh_CN')
            self.assertEqual(dialog.labelText(QFileDialog.DialogLabel.FileName),'文件名：')
            self.assertEqual(editor.text(),'计算完成。.json')
            return QDialog.DialogCode.Rejected
        with patch.object(QFileDialog,'exec',inspect):
            QFileDialog.getSaveFileName(self.window,text('保存计算方案'),'IPv6Plan.json',text('IPv6 计算方案 (*.json)'))

    def test_open_question_live_language_change_updates_buttons(self):
        errors=[]
        def inspect():
            box=QApplication.activeModalWidget()
            try:
                self.switch()
                self.assertEqual(box.button(QMessageBox.StandardButton.No).text().replace('&',''),'No')
                self.assertEqual(box.windowTitle(),'Overwrite Plan')
                self.switch('zh_CN')
                self.assertIn('否',box.button(QMessageBox.StandardButton.No).text())
            except Exception as exc:errors.append(exc)
            box.button(QMessageBox.StandardButton.No).click()
        QTimer.singleShot(0,inspect)
        QMessageBox.question(self.window,text('覆盖方案'),text('目标文件已存在，是否覆盖？'))
        if errors:raise errors[0]

    def test_message_templates_keep_user_arguments_and_exact_integers(self):
        self.switch();big=2**128;user='计算完成。'
        message=text('父网段：{0}',user)+text('空闲地址数：{0:,}',big)
        rendered=display(message)
        self.assertIn(user,rendered);self.assertIn(f'{big:,}',rendered)
        self.assertIn('Free addresses',rendered)
        self.assertIn('IPv6',display(str(ValueError(text('请输入 IPv6 地址。')))))
        self.assertEqual(str(message),'父网段：计算完成。'+f'空闲地址数：{big:,}')

    def test_reports_translate_without_modifying_raw_records(self):
        report=analyze_subnet_list('::/127\nbad')
        canonical=report.as_text();self.switch();translated=display(canonical)
        self.assertIn('IPv6 Subnet List Check Report',translated)
        self.assertIn('bad',translated);self.assertEqual(report.records[1].original,'bad')
        self.assertNotRegex(translated,r'[\u4e00-\u9fff]')

    def test_all_catalog_entries_finished_and_placeholders_preserved(self):
        path=Path(__file__).resolve().parents[1]/'assets/i18n/app_en.ts'
        tree=ET.parse(path).getroot()
        messages=[m for c in tree.findall('context') for m in c.findall('message')]
        self.assertGreater(len(messages),500)
        contexts={id(m): c.findtext('name') for c in tree.findall('context') for m in c.findall('message')}
        for message in messages:
            context=contexts[id(message)]
            source=message.findtext('source');translated=message.find('translation')
            self.assertTrue(translated.text,source);self.assertNotEqual(translated.get('type'),'unfinished')
            self.assertEqual(self.app.language_manager.english.translate(context,source.encode('utf-8')),translated.text,source)
            self.assertEqual(sorted(re.findall(r'\{[0-9]+[^}]*\}',source)),sorted(re.findall(r'\{[0-9]+[^}]*\}',translated.text)),source)

    def test_minimum_size_themes_and_repeated_switches(self):
        self.window.resize(900,620)
        before=self.window.plan_controller.snapshot()
        for i in range(20):
            self.app.theme_manager.apply('dark' if i%2 else 'light',persist=False)
            self.switch('en_US' if i%2 else 'zh_CN')
            self.assertEqual(before,self.window.plan_controller.snapshot())
            self.assertTrue(self.window.rect().contains(self.window.language_button.mapTo(self.window,self.window.language_button.rect().topLeft())))


if __name__=='__main__':unittest.main()
