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

"""文件拖放的事务边界、错误恢复与标准对话框中文回归。"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, PropertyMock
from PyQt6.QtCore import Qt, QUrl, QMimeData, QPoint, QPointF, QCoreApplication, QEvent, QTimer, QSettings, QLocale, QMimeDatabase
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import QApplication, QDialog, QLineEdit
from app import create_application
from core.calculation_plan import CalculationPlan
from services.plan_storage import save_plan, load_plan
from ui.main_window import MainWindow
from ui.standard_dialogs import QMessageBox, QFileDialog
from ui.dialogs import RangeCopyDialog, ExportRangeDialog


class ImportFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preferences=tempfile.TemporaryDirectory()
        cls.settings=QSettings(str(Path(cls.preferences.name)/'test.ini'),QSettings.Format.IniFormat)
        cls.app=create_application([],cls.settings)
        cls.previous_settings=cls.app.theme_manager.settings
        cls.app.theme_manager.settings=cls.settings
        cls.app.setQuitOnLastWindowClosed(False)

    @classmethod
    def tearDownClass(cls):
        cls.app.theme_manager.settings=cls.previous_settings
        cls.preferences.cleanup()

    def setUp(self):
        self.app.theme_manager.apply('light',persist=False)
        self.window=MainWindow()
        self.window.show()
        self.window.calculate()
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'中文方案.JSON'
        self.plan=CalculationPlan('::/120',128,'中文方案','验证拖放',100,2,None,(101,102),1)
        save_plan(self.path,self.plan)
        QApplication.processEvents()

    def tearDown(self):
        self.window.plan_controller.path=None
        self.window.calculation_page.plan_name_input.clear()
        self.window.calculation_page.plan_notes_input.clear()
        self.window.close()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        QApplication.processEvents()
        self.tmp.cleanup()

    def urls(self,path=None):
        return [QUrl.fromLocalFile(str(path or self.path))]

    def snapshot(self):
        return self.window.plan_controller.snapshot()

    def test_valid_unicode_drop_restores_once_without_calculate_or_file_write(self):
        original=self.path.read_bytes()
        with patch('ui.plan_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes),patch.object(self.window,'calculate') as calculate:
            self.assertTrue(self.window.plan_drop_controller.import_urls(self.urls()))
        calculate.assert_not_called()
        self.assertEqual(self.snapshot(),self.plan)
        self.assertEqual(self.path.read_bytes(),original)
        self.assertEqual(self.window.plan_controller.path,self.path)

    def test_refused_replacement_keeps_document_result_and_selection(self):
        before=self.snapshot()
        with patch('ui.plan_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.No):
            self.assertFalse(self.window.plan_drop_controller.import_urls(self.urls()))
        self.assertEqual(self.snapshot(),before)
        self.assertIsNone(self.window.plan_controller.path)

    def test_dirty_drop_cancel_and_discard_have_single_confirmation(self):
        page=self.window.calculation_page
        page.plan_name_input.setText('未保存的工作')
        before=self.snapshot()
        with patch('ui.plan_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.Cancel) as ask:
            self.assertFalse(self.window.plan_drop_controller.import_urls(self.urls()))
            self.assertEqual(ask.call_count,1)
        self.assertEqual(self.snapshot(),before)
        with patch('ui.plan_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.Discard) as ask:
            self.assertTrue(self.window.plan_drop_controller.import_urls(self.urls()))
            self.assertEqual(ask.call_count,1)
        self.assertEqual(self.snapshot(),self.plan)

    def test_dirty_save_cancel_aborts_drop(self):
        self.window.calculation_page.plan_name_input.setText('未保存')
        before=self.snapshot()
        with patch('ui.plan_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.Save),patch('ui.plan_controller.QFileDialog.getSaveFileName',return_value=('','')):
            self.assertFalse(self.window.plan_drop_controller.import_urls(self.urls()))
        self.assertEqual(before,self.snapshot())

    def test_save_before_dropping_same_path_restores_updated_saved_content(self):
        controller=self.window.plan_controller
        self.assertTrue(controller.open_path(self.path))
        self.window.calculation_page.plan_name_input.setText('刚保存的新名称')
        with patch('ui.plan_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.Save):
            self.assertTrue(self.window.plan_drop_controller.import_urls(self.urls()))
        self.assertEqual(load_plan(self.path).name,'刚保存的新名称')
        self.assertEqual(self.snapshot().name,'刚保存的新名称')
        self.assertEqual(controller.document(),controller.saved_document)

    def test_file_changed_during_confirmation_is_revalidated_before_apply(self):
        before=self.snapshot()
        def change(*args,**kwargs):
            self.path.write_text('{corrupt')
            return QMessageBox.StandardButton.Yes
        with patch('ui.plan_controller.QMessageBox.question',side_effect=change),patch('ui.plan_controller.QMessageBox.warning'):
            self.assertFalse(self.window.plan_drop_controller.import_urls(self.urls()))
        self.assertEqual(before,self.snapshot())

    def test_invalid_json_validated_before_confirmation_and_keeps_work(self):
        before=self.snapshot()
        for data in ('{broken','{"schema_version":99}', '{"a":1,"a":2}'):
            self.path.write_text(data)
            with patch('ui.plan_controller.QMessageBox.question') as ask,patch('ui.plan_controller.QMessageBox.warning'):
                self.assertFalse(self.window.plan_drop_controller.import_urls(self.urls()))
                ask.assert_not_called()
            self.assertEqual(before,self.snapshot())
            self.assertTrue(self.window.calculation_page.plan_file_label.property('invalid'))
            self.assertEqual(self.window.feedback.property('severity'),'error')

    def test_rejects_multiple_folder_remote_wrong_suffix_and_missing_files(self):
        before=self.snapshot()
        cases=[self.urls()+self.urls(),self.urls(Path(self.tmp.name)),[QUrl('https://example.invalid/plan.json')],self.urls(Path(self.tmp.name)/'missing.json')]
        txt=Path(self.tmp.name)/'list.txt';txt.write_text('::/64');cases.append(self.urls(txt))
        for urls in cases:
            with patch('ui.plan_controller.QMessageBox.warning') as warn,patch('ui.plan_controller.QMessageBox.question') as ask:
                self.assertFalse(self.window.plan_drop_controller.import_urls(urls))
                warn.assert_called_once();ask.assert_not_called()
            self.assertEqual(before,self.snapshot())

    def test_drop_rejected_during_background_task_without_confirmation(self):
        before=self.snapshot()
        for service in (self.window.export_service,self.window.subnet_list_page.service):
            with patch.object(type(service),'busy',new_callable=PropertyMock,return_value=True),patch('ui.plan_controller.QMessageBox.question') as ask:
                self.assertFalse(self.window.plan_drop_controller.import_urls(self.urls()))
                ask.assert_not_called()
        self.assertEqual(before,self.snapshot())

    def test_drag_events_on_text_editor_and_table_do_not_insert_paths(self):
        for widget in (self.window.calculation_page.network_input,self.window.subnet_list_page.editor.viewport(),self.window.results_page.table.viewport()):
            mime=QMimeData();mime.setUrls(self.urls())
            drag=QDragEnterEvent(QPoint(5,5),Qt.DropAction.CopyAction,mime,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier)
            drop=QDropEvent(QPointF(5,5),Qt.DropAction.CopyAction,mime,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier)
            before=self.window.plan_controller.document()
            with patch('ui.plan_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.No):
                QApplication.sendEvent(widget,drag)
                QApplication.sendEvent(widget,drop)
                QApplication.processEvents()
            self.assertTrue(drag.isAccepted())
            self.assertTrue(drop.isAccepted())
            self.assertEqual(drop.dropAction(),Qt.DropAction.CopyAction)
            self.assertEqual(before,self.window.plan_controller.document())

    def test_pending_drop_does_not_import_after_window_closed(self):
        mime=QMimeData();mime.setUrls(self.urls())
        event=QDropEvent(QPointF(5,5),Qt.DropAction.CopyAction,mime,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier)
        with patch.object(self.window.plan_controller,'open_path') as load:
            self.window.plan_drop_controller.eventFilter(self.window,event)
            self.window.close()
            QApplication.processEvents()
            load.assert_not_called()

    def test_move_only_drag_is_not_accepted_as_a_file_move(self):
        mime=QMimeData();mime.setUrls(self.urls())
        event=QDragEnterEvent(QPoint(5,5),Qt.DropAction.MoveAction,mime,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier)
        self.assertTrue(self.window.plan_drop_controller.eventFilter(self.window,event))
        self.assertFalse(event.isAccepted())

    def test_text_drag_and_other_dialog_are_not_intercepted(self):
        field=self.window.calculation_page.network_input
        mime=QMimeData();mime.setText('abcd')
        event=QDragEnterEvent(QPoint(5,5),Qt.DropAction.CopyAction,mime,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier)
        self.assertFalse(self.window.plan_drop_controller.eventFilter(field,event))
        dialog=QDialog(self.window);other=QLineEdit(dialog)
        mime.setUrls(self.urls())
        self.assertFalse(self.window.plan_drop_controller.eventFilter(other,event))
        dialog.deleteLater()

    def test_calculation_error_targets_field_and_clears_when_edited_in_both_themes(self):
        page=self.window.calculation_page
        for theme in ('light','dark'):
            self.app.theme_manager.apply(theme,persist=False)
            for field,value in ((page.network_input,'bad'),(page.target_input,'47')):
                page.network_input.setText('2026:1015:abcd::/48');page.target_input.setText('64')
                field.setText(value);self.window.calculate()
                self.assertTrue(field.property('invalid'))
                self.assertTrue(field._input_error_action.isVisible())
                self.assertTrue(field._input_error_action.toolTip())
                self.assertTrue(self.window.feedback.text().startswith('⚠'))
                self.assertIsNone(self.window.result)
                field.setText('2026:1015:abcd::/48' if field is page.network_input else '64')
                self.assertFalse(field.property('invalid'))
                self.assertFalse(field._input_error_action.isVisible())
                self.window.calculate()
                self.assertIsNotNone(self.window.result)

    def test_tools_error_marks_only_failing_network_and_retries(self):
        page=self.window.address_tools_page
        page.address_input.setText('bad');page.convert()
        self.assertTrue(page.address_input.property('invalid'))
        page.address_input.setText('::1');page.convert()
        self.assertFalse(page.address_input.property('invalid'))
        page.network_b_input.setText('bad');page.analyze()
        self.assertFalse(bool(page.network_a_input.property('invalid')))
        self.assertTrue(page.network_b_input.property('invalid'))
        page.network_b_input.setText('::/0');page.analyze()
        self.assertFalse(page.network_b_input.property('invalid'))

    def test_range_and_locator_errors_show_red_fields_and_recover(self):
        page=self.window.results_page
        with patch('ui.results_page.QMessageBox.warning'):
            page.locator_input.setText('bad');page.locate()
        self.assertTrue(page.locator_input.property('invalid'))
        page.locator_input.setText('2026:1015:abcd::1');page.locate()
        self.assertFalse(page.locator_input.property('invalid'))
        for dialog in (RangeCopyDialog(self.window.result,self.window.clipboard,parent=self.window),ExportRangeDialog(65536,self.window)):
            if isinstance(dialog,ExportRangeDialog):dialog.range_radio.setChecked(True)
            dialog.start_input.setText('bad')
            with patch('ui.dialogs.QMessageBox.warning'):
                dialog.perform() if isinstance(dialog,RangeCopyDialog) else dialog.confirm()
            self.assertTrue(dialog.start_input.property('invalid'))
            self.assertEqual(dialog.input_feedback.property('severity'),'error')
            dialog.start_input.setText('1')
            self.assertFalse(dialog.start_input.property('invalid'))
            dialog.deleteLater()

    def test_chinese_qt_catalog_loaded_independently_of_system_locale(self):
        text=QCoreApplication.translate('QLineEdit','Select All')
        self.assertIn('全选',text)
        self.assertTrue(self.app.qt_chinese_translator is not None)
        self.assertIn('字节',QLocale().formattedDataSize(389))
        self.assertIn('文档',QMimeDatabase().mimeTypeForName('application/json').comment())

    def test_actual_question_buttons_chinese_and_no_is_default(self):
        errors=[]
        def inspect():
            box=QApplication.activeModalWidget()
            try:
                self.assertEqual(box.button(QMessageBox.StandardButton.Yes).text(),'是')
                self.assertEqual(box.button(QMessageBox.StandardButton.No).text(),'否')
                self.assertIs(box.defaultButton(),box.button(QMessageBox.StandardButton.No))
                self.assertEqual(box.textFormat(),Qt.TextFormat.PlainText)
            except Exception as exc:errors.append(exc)
            box.button(QMessageBox.StandardButton.No).click()
        QTimer.singleShot(0,inspect)
        answer=QMessageBox.question(self.window,'替换确认','<b>按原文显示</b>')
        self.assertEqual(answer,QMessageBox.StandardButton.No)
        if errors:raise errors[0]

    def test_actual_save_discard_cancel_buttons_chinese(self):
        errors=[]
        def inspect():
            box=QApplication.activeModalWidget()
            try:
                self.assertEqual([box.button(x).text() for x in (QMessageBox.StandardButton.Save,QMessageBox.StandardButton.Discard,QMessageBox.StandardButton.Cancel)],['保存','不保存','取消'])
            except Exception as exc:errors.append(exc)
            box.button(QMessageBox.StandardButton.Cancel).click()
        QTimer.singleShot(0,inspect)
        answer=QMessageBox.question(self.window,'未保存','保存更改？',QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Discard|QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Cancel)
        self.assertEqual(answer,QMessageBox.StandardButton.Cancel)
        if errors:raise errors[0]

    def test_file_dialogs_force_qt_chinese_browser(self):
        for saving in (False,True):
            def inspect(dialog):
                self.assertTrue(dialog.testOption(QFileDialog.Option.DontUseNativeDialog))
                self.assertEqual(dialog.labelText(QFileDialog.DialogLabel.FileName),'文件名：')
                self.assertEqual(dialog.labelText(QFileDialog.DialogLabel.Reject),'取消')
                self.assertEqual(dialog.labelText(QFileDialog.DialogLabel.Accept),'保存' if saving else '打开')
                return QDialog.DialogCode.Rejected
            with patch.object(QFileDialog,'exec',inspect):
                choose=QFileDialog.getSaveFileName if saving else QFileDialog.getOpenFileName
                self.assertEqual(choose(self.window,'选择文件','','计算方案 (*.json)'),('',''))


if __name__=='__main__':
    unittest.main()
