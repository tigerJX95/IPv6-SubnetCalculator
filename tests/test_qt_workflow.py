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

"""Qt 迁移后的关键交互与线程生命周期回归。"""
import tempfile
import unittest
from pathlib import Path
from time import monotonic
from unittest.mock import patch

from PyQt6.QtCore import Qt, QItemSelectionModel, QTimer, QCoreApplication, QEvent, QSettings, QMimeData
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QDialog, QScrollArea, QMessageBox
from app import create_application
from core.ipv6_core import calculate
from services.clipboard_service import ClipboardService
from services.export_service import ExportService, _ExportThread
from ui.main_window import MainWindow
from ui.dialogs import RangeCopyDialog, ExportRangeDialog, SubnetDetailDialog, ExportProgressDialog
from ui.theme import ThemeManager, THEMES


def wait_until(condition, timeout=4):
    deadline = monotonic()+timeout
    while monotonic() < deadline:
        QApplication.processEvents()
        if condition():
            return
        QTest.qWait(5)
    raise AssertionError('Qt operation did not finish within the test timeout')


class QtWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings_dir = tempfile.TemporaryDirectory()
        cls.settings = QSettings(str(Path(cls.settings_dir.name)/'preferences.ini'), QSettings.Format.IniFormat)
        cls.application = create_application([], settings=cls.settings)
        # QApplication 为进程单例；其他 Qt 测试可能已经创建过它。
        cls.application.theme_manager.settings = cls.settings
        cls.application.setQuitOnLastWindowClosed(False)
        cls.saved_clipboard = QMimeData()
        original = QApplication.clipboard().mimeData()
        if original is not None:
            for mime_type in original.formats():
                cls.saved_clipboard.setData(mime_type, original.data(mime_type))

    @classmethod
    def tearDownClass(cls):
        if cls.saved_clipboard.formats():
            QApplication.clipboard().setMimeData(cls.saved_clipboard)
        else:
            QApplication.clipboard().clear()
        QApplication.processEvents()
        cls.settings_dir.cleanup()

    def setUp(self):
        self.application.theme_manager.apply('light', persist=False)
        self.window = MainWindow()
        self.window.show()
        self.window.calculate()
        self.page = self.window.results_page
        QApplication.processEvents()

    def tearDown(self):
        self.window.subnet_list_page.project_controller.saved = self.window.subnet_list_page.project_controller.snapshot()
        if self.window.subnet_list_page.service.busy:
            self.window.subnet_list_page.cancel()
            wait_until(lambda: not self.window.subnet_list_page.service.busy)
        if self.window.export_service.busy:
            self.window.export_controller.cancel()
            wait_until(lambda: not self.window.export_service.busy)
        self.window.plan_controller.path = None
        self.window.calculation_page.plan_name_input.clear()
        self.window.calculation_page.plan_notes_input.clear()
        self.window.close()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QApplication.processEvents()

    def test_about_icon_f1_and_single_window_preserve_work(self):
        from app_info import APP_VERSION
        self.page.show_page(2)
        self.page.table.selectRow(3)
        before = self.window.plan_controller.snapshot()
        self.assertIn('F1', self.window.about_button.toolTip())
        self.window.about_button.click()
        QApplication.processEvents()
        dialog = self.window.about_dialog
        self.assertTrue(dialog.isVisible())
        self.assertEqual(dialog.tabs.count(), 4)
        self.assertIn('V'+APP_VERSION, dialog.information.toPlainText())
        self.assertFalse(dialog.isModal())
        dialog.tabs.setCurrentIndex(1)
        dialog.usage.verticalScrollBar().setValue(100)
        scroll = dialog.usage.verticalScrollBar().value()
        dialog.close()
        self.window.activateWindow()
        self.window.setFocus()
        QApplication.processEvents()
        QTest.keyClick(self.window, Qt.Key.Key_F1)
        QApplication.processEvents()
        self.assertIs(self.window.about_dialog, dialog)
        self.assertTrue(dialog.isVisible())
        self.assertEqual(dialog.tabs.currentIndex(), 1)
        self.assertEqual(dialog.usage.verticalScrollBar().value(), scroll)
        self.assertEqual(before, self.window.plan_controller.snapshot())
        QTest.keyClick(dialog, Qt.Key.Key_Escape)
        self.assertFalse(dialog.isVisible())

    def test_closing_main_window_also_closes_about(self):
        self.window.show_about()
        self.assertTrue(self.window.about_dialog.isVisible())
        self.window.close()
        QApplication.processEvents()
        self.assertFalse(self.window.about_dialog.isVisible())
        self.assertFalse(self.window.isVisible())

    def test_about_offline_license_texts_match_bundled_originals(self):
        from app_info import resource_path
        from services.about_content import LICENSE_DOCUMENTS
        self.window.show_about()
        dialog = self.window.about_dialog
        self.assertIn('2026:1015:abcd::/48', dialog.usage.toPlainText())
        self.assertIn('Ctrl+Shift+S', dialog.usage.toPlainText())
        self.assertIn('第 15～17 条', dialog.legal.toPlainText())
        self.assertIn('不增加许可限制', dialog.legal.toPlainText())
        for index, (_, path) in enumerate(LICENSE_DOCUMENTS):
            dialog.license_selector.setCurrentIndex(index)
            text = dialog.licenses.toPlainText()
            with self.subTest(path=path):
                self.assertNotIn('无法读取', text)
                if not path.endswith('.md'):
                    self.assertEqual(text.strip(), resource_path(path).read_text(encoding='utf-8').strip())
                else:
                    self.assertIn('PyQt6', text)
        dialog.close()

    def test_about_minimum_size_and_live_themes(self):
        self.window.resize(900, 620)
        self.window.show_about()
        dialog = self.window.about_dialog
        dialog.resize(680, 440)
        for theme in ('dark', 'light'):
            self.application.theme_manager.apply(theme, persist=False)
            for index in range(4):
                dialog.tabs.setCurrentIndex(index)
                QApplication.processEvents()
                self.assertLessEqual(dialog.tabs.geometry().right(), dialog.width())
                self.assertLessEqual(dialog.close_button.geometry().bottom(), dialog.height())
                self.assertGreater(dialog.tabs.currentWidget().height(), 200)
            self.assertEqual(self.application.property('themeName'), theme)
            self.assertFalse(self.window.about_button.icon().isNull())
            self.assertEqual(dialog.licenses.palette().color(QPalette.ColorRole.Link).name(), THEMES[theme]['accent'])
        dialog.close()

    def test_about_document_failure_is_visible_and_recoverable(self):
        self.window.show_about()
        dialog = self.window.about_dialog
        with patch('ui.about_dialog.read_document', side_effect=RuntimeError('无法读取内置文档：许可文件缺失')):
            dialog.license_selector.setCurrentIndex(1)
        self.assertIn('无法读取内置文档', dialog.licenses.toPlainText())
        dialog.license_selector.setCurrentIndex(0)
        self.assertIn('PyQt6', dialog.licenses.toPlainText())
        self.assertNotIn('无法读取', dialog.licenses.toPlainText())
        dialog.close()

    def test_about_links_require_user_action_and_https(self):
        from PyQt6.QtCore import QUrl
        with patch('ui.about_dialog.QDesktopServices.openUrl', return_value=True) as opened:
            self.window.show_about()
            dialog = self.window.about_dialog
            self.assertFalse(dialog.licenses.openExternalLinks())
            self.assertFalse(dialog.licenses.openLinks())
            opened.assert_not_called()
            for url in ('file:///C:/Windows/test', 'javascript:alert(1)', '../LICENSE', 'http://example.com'):
                dialog.licenses.open_link(QUrl(url))
            opened.assert_not_called()
            url = QUrl('https://www.gnu.org/licenses/gpl-3.0.html')
            dialog.licenses.anchorClicked.emit(url)
            opened.assert_called_once_with(url)
        dialog.close()

    def check_list(self, text):
        page=self.window.subnet_list_page
        page.editor.setPlainText(text)
        page.analyze()
        wait_until(lambda: not page.service.busy)
        return page

    def test_subnet_list_ui_counts_copy_and_input_invalidation(self):
        page=self.check_list('::/0\n::1/128\n::1/128\nbad')
        self.assertEqual(page.record_model.rowCount(),4)
        self.assertEqual(page.analysis.duplicate_pairs,1)
        self.assertEqual(page.analysis.containment_pairs,2)
        self.assertTrue(page.copy_report_button.isEnabled())
        self.assertIn('已检查',page.source_label.text())
        with patch.object(page.clipboard,'copy_text',return_value=True) as copied:
            page.copy_networks()
            self.assertEqual(copied.call_args.args[0],'::/0\n::1/128')
            page.copy_report()
            self.assertIn('错误行：1',copied.call_args.args[0])
        page.editor.insertPlainText('changed')
        self.assertIsNone(page.analysis)
        self.assertEqual(page.record_model.rowCount(),0)
        self.assertFalse(page.copy_networks_button.isEnabled())
        self.assertFalse(page.copy_report_button.isEnabled())

    def test_subnet_list_import_bom_cancel_and_failed_file_preserve_input(self):
        page=self.window.subnet_list_page
        page.editor.setPlainText('::/0')
        with patch('ui.subnet_list_page.QFileDialog.getOpenFileName',return_value=('','')):
            page.import_file()
        self.assertEqual(page.editor.toPlainText(),'::/0')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'清单.txt';path.write_bytes(b'\xef\xbb\xbf::1/128\r\n::2/128')
            with patch('ui.subnet_list_page.QFileDialog.getOpenFileName',return_value=(str(path),'')):
                page.import_file()
            wait_until(lambda: not page.service.busy)
            self.assertEqual(page.analysis.valid_count,2)
            self.assertIn('清单.txt',page.source_label.text())
            snapshot=page.editor.toPlainText();result=page.analysis
            path.write_bytes(b'\xff')
            with patch('ui.subnet_list_page.QFileDialog.getOpenFileName',return_value=(str(path),'')):
                page.import_file()
            self.assertEqual(page.editor.toPlainText(),snapshot)
            self.assertIs(page.analysis,result)
            self.assertIn('导入失败',self.window.feedback.text())

    def test_subnet_list_themes_and_minimum_window(self):
        page=self.check_list('::/128\nbad')
        self.window.tabs.setCurrentWidget(page)
        self.window.resize(900,620)
        for theme in ('dark','light'):
            self.application.theme_manager.apply(theme,persist=False)
            QApplication.processEvents()
            self.assertEqual(page.record_model.data(page.record_model.index(1,3),Qt.ItemDataRole.ForegroundRole),QColor(THEMES[theme]['error']))
            self.assertLessEqual(page.result_tabs.geometry().bottom(),page.height())
            self.assertFalse(page.analyze_button.icon().isNull())
        self.assertEqual(page.analysis.error_count,1)

    def test_subnet_list_worker_error_then_retry(self):
        page=self.window.subnet_list_page
        with patch('services.subnet_list_service.analyze_subnet_list',side_effect=RuntimeError('模拟失败')):
            self.check_list('::/0')
        self.assertIn('模拟失败',page.summary.text())
        self.assertFalse(page.editor.isReadOnly())
        self.check_list('::/128')
        self.assertEqual(page.analysis.valid_count,1)

    def test_subnet_list_cancel_and_close_wait_for_worker(self):
        from core.subnet_list import ListCheckCancelled
        def blocked(text,stop):
            stop.wait(2)
            raise ListCheckCancelled()
        page=self.window.subnet_list_page
        page.editor.setPlainText('::/0')
        with patch('services.subnet_list_service.analyze_subnet_list',side_effect=blocked), patch('ui.project_controller.QMessageBox.question', return_value=QMessageBox.StandardButton.Discard):
            page.analyze()
            self.assertTrue(page.service.busy)
            self.assertTrue(page.editor.isReadOnly())
            self.window.close()
            wait_until(lambda: not page.service.busy and not self.window.isVisible())
        self.assertIsNone(page.analysis)
        self.assertEqual(page.editor.toPlainText(),'::/0')

    def test_subnet_list_thread_creation_failure_is_recoverable(self):
        page=self.window.subnet_list_page
        page.editor.setPlainText('::/0')
        with patch('services.subnet_list_service._ListThread.start',side_effect=RuntimeError('无法创建线程')):
            page.analyze()
        self.assertFalse(page.service.busy)
        self.assertFalse(page.editor.isReadOnly())
        self.assertIn('无法创建线程',self.window.feedback.text())

    def test_subnet_list_keeps_calculation_plan_format_compatible(self):
        before=self.window.plan_controller.snapshot()
        page=self.check_list('::/0\n::1/128')
        self.window.tabs.setCurrentWidget(page)
        after=self.window.plan_controller.snapshot()
        self.assertEqual(after.tab,0)
        self.assertEqual(after.network,before.network)
        self.assertEqual(after.target_prefix,before.target_prefix)
        from core.calculation_plan import plan_to_payload,plan_from_payload
        self.assertEqual(plan_from_payload(plan_to_payload(after)),after)

    def test_subnet_list_all_invalid_keeps_report_and_disables_cidr_copy(self):
        page=self.check_list('bad\n192.0.2.0/24')
        self.assertEqual(page.analysis.error_count,2)
        self.assertFalse(page.copy_networks_button.isEnabled())
        self.assertTrue(page.copy_report_button.isEnabled())
        self.assertIn('不代表整份清单通过',page.summary.text())

    def plan_list(self, task, text='::/127\n::2/127', parent='::/124'):
        page=self.window.subnet_list_page
        page.editor.setPlainText(text)
        page.planning.parent_input.setText(parent)
        page.start_planning(task)
        wait_until(lambda:not page.service.busy)
        return page

    def test_free_planning_counts_copy_and_parent_invalidation(self):
        page=self.plan_list('free')
        views=page.planning
        self.assertEqual(views.free_result.free_addresses,12)
        self.assertTrue(views.copy_free_button.isEnabled())
        with patch.object(page.clipboard,'copy_text',return_value=True) as copied:
            views.copy_free()
            self.assertEqual(copied.call_args.args[0],'::4/126\n::8/125')
            views.copy_report('free')
            self.assertIn('全部空闲地址范围',copied.call_args.args[0])
        views.parent_input.setText('::/123')
        self.assertIsNone(views.free_result)
        self.assertFalse(views.copy_free_button.isEnabled())

    def test_aggregate_planning_copy_preserves_original_and_calculator(self):
        before=self.window.result
        page=self.plan_list('aggregate')
        views=page.planning
        self.assertEqual(views.aggregate_result.cidr_text(),'::/126')
        self.assertEqual(page.editor.toPlainText(),'::/127\n::2/127')
        self.assertIs(self.window.result,before)
        with patch.object(page.clipboard,'copy_text',return_value=True) as copied:
            views.copy_aggregate()
            self.assertEqual(copied.call_args.args[0],'::/126')
        page.editor.insertPlainText('bad')
        self.assertIsNone(views.aggregate_result)
        self.assertFalse(views.copy_aggregate_button.isEnabled())

    def test_planning_error_strictness_and_recovery(self):
        page=self.plan_list('free','::/0','::/64')
        self.assertIsNone(page.planning.free_result)
        self.assertIn('不完全位于',page.planning.free_status.text())
        page=self.plan_list('aggregate','::/0\nbad')
        self.assertIsNone(page.planning.aggregate_result)
        self.assertIn('第 2 行',page.planning.aggregate_status.text())
        page=self.plan_list('free','','::/0')
        self.assertEqual(page.planning.free_result.free_addresses,2**128)

    def test_free_truncated_results_disable_partial_cidr_copy(self):
        from core.subnet_planning import free_space
        from ipaddress import IPv6Address
        text='\n'.join(f'{IPv6Address((index<<112)+1)}/128' for index in range(100))
        page=self.plan_list('free',text,'::/0')
        views=page.planning
        self.assertFalse(views.free_result.complete)
        self.assertFalse(views.copy_free_button.isEnabled())
        self.assertTrue(views.copy_free_report_button.isEnabled())
        self.assertEqual(views.free_model.rowCount(),5000)

    def test_planning_cancel_and_window_close_wait_for_worker(self):
        from core.subnet_list import ListCheckCancelled
        def blocked(text,parent_text,stop):
            stop.wait(2)
            raise ListCheckCancelled()
        page=self.window.subnet_list_page
        page.editor.setPlainText('::/128')
        with patch('services.subnet_list_service.free_space',side_effect=blocked), patch('ui.project_controller.QMessageBox.question', return_value=QMessageBox.StandardButton.Discard):
            page.start_planning('free')
            self.assertTrue(page.service.busy)
            self.assertTrue(page.planning.parent_input.isReadOnly())
            self.window.close()
            wait_until(lambda:not page.service.busy and not self.window.isVisible())
        self.assertIsNone(page.planning.free_result)
        self.assertIn('取消',page.planning.free_status.text())

    def test_planning_both_themes_and_minimum_window(self):
        page=self.plan_list('free')
        page.start_planning('aggregate')
        wait_until(lambda:not page.service.busy)
        self.window.tabs.setCurrentWidget(page)
        self.window.resize(900,620)
        for theme in ('light','dark'):
            self.application.theme_manager.apply(theme,persist=False)
            for index in (2,3):
                page.result_tabs.setCurrentIndex(index)
                QApplication.processEvents()
                self.assertLessEqual(page.result_tabs.geometry().bottom(),page.height())
                self.assertTrue(page.result_tabs.currentWidget().isVisible())
        self.assertIsNotNone(page.planning.free_result)
        self.assertIsNotNone(page.planning.aggregate_result)

    def test_about_icon_is_transparent_and_theme_aware(self):
        for theme in ('light','dark'):
            self.application.theme_manager.apply(theme,persist=False)
            icon=self.window.about_button.icon().pixmap(52,52).toImage()
            self.assertEqual(icon.pixelColor(5,5).alpha(),0)
            self.assertEqual(icon.pixelColor(0,0).alpha(),0)
        self.assertIn('F1',self.window.about_button.toolTip())
        self.window.about_button.setFocus()
        QTest.keyClick(self.window.about_button,Qt.Key.Key_Return)
        self.assertTrue(self.window.about_dialog.isVisible())
        self.window.about_dialog.close()

    def locate(self, text='90-210'):
        self.page.locator_mode_combo.setCurrentIndex(3)
        self.page.locator_input.setText(text)
        self.page.locate()
        QApplication.processEvents()

    def click_row(self, row, modifier=Qt.KeyboardModifier.NoModifier):
        index = self.page.model.index(row-1, 1)
        self.page.table.scrollTo(index)
        QApplication.processEvents()
        QTest.mouseClick(self.page.table.viewport(), Qt.MouseButton.LeftButton, modifier,
                         self.page.table.visualRect(index).center())
        QApplication.processEvents()

    def test_plan_roundtrip_restores_metadata_paging_range_and_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'办公方案.json'
            calculation=self.window.calculation_page
            calculation.plan_name_input.setText('办公网络')
            calculation.plan_notes_input.setPlainText('办公楼 VLAN 规划')
            self.locate('190-210')
            self.window.tabs.setCurrentIndex(1)
            snapshot=self.window.plan_controller.snapshot()
            with patch('ui.plan_controller.QFileDialog.getSaveFileName',return_value=(str(path),'')):
                self.assertTrue(self.window.plan_controller.save())
            calculation.network_input.setText('::1/128');calculation.target_input.setText('128');self.window.calculate()
            with patch('ui.plan_controller.QFileDialog.getOpenFileName',return_value=(str(path),'')), \
                 patch('ui.plan_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.Discard):
                self.assertTrue(self.window.plan_controller.open())
            self.assertEqual(self.window.plan_controller.snapshot(),snapshot)
            self.assertIn(path.name,calculation.plan_file_label.text())

    def test_plan_open_with_unsaved_changes_can_cancel_without_replacing_work(self):
        from services.plan_storage import save_plan
        from core.calculation_plan import CalculationPlan
        self.window.calculation_page.plan_name_input.setText('未保存名称')
        before=self.window.plan_controller.snapshot()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'other.json';save_plan(path,CalculationPlan('::1/128',128))
            with patch('ui.plan_controller.QFileDialog.getOpenFileName',return_value=(str(path),'')), \
                 patch('ui.plan_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.Cancel):
                self.assertFalse(self.window.plan_controller.open())
            self.assertEqual(self.window.plan_controller.snapshot(),before)
            self.assertIsNone(self.window.plan_controller.path)

    def test_plan_existing_save_is_direct_and_save_as_cancel_preserves_path(self):
        from services.plan_storage import load_plan
        controller=self.window.plan_controller
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'new'
            with patch('ui.plan_controller.QFileDialog.getSaveFileName',return_value=(str(path),'')):
                self.assertTrue(controller.save())
            path=path.with_suffix('.json')
            self.window.calculation_page.plan_notes_input.setPlainText('更新备注')
            with patch('ui.plan_controller.QFileDialog.getSaveFileName') as dialog:
                self.assertTrue(controller.save());dialog.assert_not_called()
            self.assertEqual(load_plan(path).notes,'更新备注')
            with patch('ui.plan_controller.QFileDialog.getSaveFileName',return_value=('','')):
                self.assertFalse(controller.save(save_as=True))
            self.assertEqual(controller.path,path)

    def test_plan_corruption_and_cancel_preserve_current_work(self):
        self.locate('90-210')
        before=self.window.plan_controller.snapshot()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bad.json';path.write_bytes(b'bad')
            with patch('ui.plan_controller.QFileDialog.getOpenFileName',return_value=(str(path),'')), \
                 patch('ui.plan_controller.QMessageBox.warning'):
                self.assertFalse(self.window.plan_controller.open())
            self.assertEqual(self.window.plan_controller.snapshot(),before)
        with patch('ui.plan_controller.QFileDialog.getOpenFileName',return_value=('','')):
            self.assertFalse(self.window.plan_controller.open())
        self.assertEqual(self.window.plan_controller.snapshot(),before)

    def test_plan_unsaved_close_can_cancel_or_discard(self):
        self.window.calculation_page.plan_name_input.setText('未保存方案')
        with patch('ui.plan_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.Cancel):
            self.window.close()
        self.assertTrue(self.window.isVisible())
        with patch('ui.plan_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.Discard):
            self.window.close()
        self.assertFalse(self.window.isVisible())
        self.window.calculation_page.plan_name_input.clear()

    def test_plan_save_rejects_uncalculated_changes_and_retains_previous_file_on_failure(self):
        controller=self.window.plan_controller
        self.window.calculation_page.target_input.setText('128')
        with patch('ui.plan_controller.QMessageBox.warning'),patch('ui.plan_controller.QFileDialog.getSaveFileName') as dialog:
            self.assertFalse(controller.save());dialog.assert_not_called()
        self.window.calculation_page.target_input.setText('64')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'old.json';path.write_bytes(b'original')
            with patch('ui.plan_controller.QFileDialog.getSaveFileName',return_value=(str(path),'')), \
                 patch('ui.plan_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes), \
                 patch('ui.plan_controller.save_plan',side_effect=OSError('locked')), \
                 patch('ui.plan_controller.QMessageBox.warning'):
                self.assertFalse(controller.save())
            self.assertEqual(path.read_bytes(),b'original')
            self.assertIsNone(controller.path)

    def test_plan_maximum_space_restore_in_both_themes(self):
        from core.calculation_plan import CalculationPlan
        plan=CalculationPlan('::/0',128,page_size=200,page=(2**128+199)//200,
                             locator_range=(2**128-10,2**128),selected_indices=(2**128,),tab=1)
        for theme in ('dark','light'):
            self.application.theme_manager.apply(theme,persist=False)
            self.window.plan_controller.apply(plan)
            self.assertEqual(self.window.plan_controller.snapshot(),plan)
            self.assertEqual(self.page.model.records[-1][0],2**128)
            self.assertEqual(self.page.selected_indices(),[2**128])

    def test_default_calculation_and_tabs(self):
        self.assertEqual(self.window.tabs.count(), 4)
        self.assertEqual(self.window.tabs.currentWidget(), self.page)
        self.assertEqual(self.page.model.rowCount(), 100)
        self.assertEqual(self.page.model.records[0], (1, '2026:1015:abcd::/64'))
        self.assertEqual(self.window.calculation_page.fields['count'].text(), '65,536')

    def test_summary_copy_in_both_themes_preserves_snapshot_and_result_state(self):
        self.locate('190-210')
        calculation = self.window.calculation_page
        expected = calculation.summary_text()
        records = list(self.page.model.records)
        calculation.network_input.setText('::/0')
        calculation.target_input.setText('128')
        self.window.tabs.setCurrentIndex(0)
        for theme in ('light', 'dark'):
            with self.subTest(theme=theme):
                self.application.theme_manager.apply(theme, persist=False)
                button = calculation.copy_summary_button
                self.assertTrue(button.isEnabled())
                self.assertFalse(button.icon().isNull())
                self.assertIn('修改输入后需重新计算', button.toolTip())
                self.assertEqual(button.accessibleName(), '复制计算摘要')
                QTest.mouseClick(button, Qt.MouseButton.LeftButton)
                self.assertEqual(QApplication.clipboard().text(), expected)
                self.assertIn('可划分子网数：65,536', expected)
                self.assertEqual(self.window.feedback.property('severity'), 'success')
                self.assertEqual(self.page.selected_indices(), [190])
                self.assertEqual(self.page.locator_range, (190, 210))
                self.assertEqual(self.page.model.records, records)
                self.assertEqual(self.window.tabs.currentIndex(), 0)

    def test_summary_invalid_recalculation_clears_copy_and_valid_retry_restores_it(self):
        calculation = self.window.calculation_page
        calculation.network_input.setText('bad-network')
        self.window.calculate()
        self.assertFalse(calculation.copy_summary_button.isEnabled())
        self.assertEqual(calculation.summary_text(), '')
        with patch.object(self.window.clipboard, 'copy_text') as copy:
            calculation.copy_summary()
            copy.assert_not_called()
        calculation.network_input.setText('::/0')
        calculation.target_input.setText('128')
        self.window.calculate()
        self.window.tabs.setCurrentIndex(0)
        calculation.copy_summary_button.click()
        self.assertTrue(calculation.copy_summary_button.isEnabled())
        self.assertIn(f'可划分子网数：{2**128:,}', QApplication.clipboard().text())

    def test_summary_clipboard_failure_preserves_result_and_allows_retry(self):
        calculation = self.window.calculation_page
        self.window.tabs.setCurrentIndex(0)
        snapshot = calculation.summary_text()
        result = self.window.result
        with patch('services.clipboard_service.QApplication.clipboard', side_effect=RuntimeError('busy')), \
                patch('services.clipboard_service.QMessageBox.warning'):
            calculation.copy_summary_button.click()
        self.assertEqual(self.window.feedback.property('severity'), 'error')
        self.assertIs(self.window.result, result)
        self.assertEqual(calculation.summary_text(), snapshot)
        self.assertTrue(calculation.copy_summary_button.isEnabled())
        calculation.copy_summary_button.click()
        self.assertEqual(QApplication.clipboard().text(), snapshot)
        self.assertEqual(self.window.feedback.property('severity'), 'success')

    def test_summary_copy_starts_disabled_without_a_calculation(self):
        from ui.calculation_page import CalculationPage
        page = CalculationPage()
        try:
            self.assertFalse(page.copy_summary_button.isEnabled())
            self.assertEqual(page.summary_text(), '')
            with patch.object(page, 'summary_copy_requested') as signal:
                page.copy_summary()
                signal.emit.assert_not_called()
        finally:
            page.deleteLater()

    def test_address_tools_start_disabled_and_enter_converts_and_copies(self):
        tools = self.window.address_tools_page
        self.window.tabs.setCurrentIndex(2)
        self.assertFalse(tools.copy_formats_button.isEnabled())
        self.assertFalse(tools.copy_relation_button.isEnabled())
        tools.address_input.setText('2026:1015:ABCD::1')
        QTest.keyClick(tools.address_input, Qt.Key.Key_Return)
        self.assertEqual(tools.format_fields['compressed'].text(), '2026:1015:abcd::1')
        for key, button in tools.format_copy_buttons.items():
            button.click()
            self.assertEqual(QApplication.clipboard().text(), getattr(tools.formats, key))
        self.assertEqual(len(tools.formats.binary), 128)
        tools.copy_formats_button.click()
        self.assertEqual(QApplication.clipboard().text(), tools.formats.as_text())

    def test_address_tools_edits_and_invalid_conversion_clear_only_conversion(self):
        tools = self.window.address_tools_page
        tools.convert()
        tools.analyze()
        relation = tools.relation
        tools.address_input.setText('bad')
        self.assertFalse(tools.copy_formats_button.isEnabled())
        self.assertTrue(all(not button.isEnabled() for button in tools.format_copy_buttons.values()))
        tools.convert()
        self.assertEqual(self.window.feedback.property('severity'), 'error')
        self.assertIsNone(tools.formats)
        self.assertIs(tools.relation, relation)
        self.assertTrue(tools.copy_relation_button.isEnabled())

    def test_network_relation_direction_normalization_copy_and_invalid_retry(self):
        tools = self.window.address_tools_page
        tools.network_a_input.setText('2026:1015:abcd::1234/64')
        tools.network_b_input.setText('2026:1015:abcd::/48')
        QTest.keyClick(tools.network_b_input, Qt.Key.Key_Return)
        self.assertEqual(tools.relation.kind, 'b_contains_a')
        self.assertIn('主机位已规范化：A', self.window.feedback.text())
        tools.copy_relation_button.click()
        self.assertEqual(QApplication.clipboard().text(), tools.relation.as_text())
        self.assertIn('关系：B 包含 A', QApplication.clipboard().text())
        tools.network_b_input.setText('invalid')
        self.assertFalse(tools.copy_relation_button.isEnabled())
        tools.analyze()
        self.assertIn('网段 B：', self.window.feedback.text())
        self.assertTrue(all(field.text()=='—' for field in tools.relation_fields.values()))
        tools.network_b_input.setText('2026:1015:abcd::/64')
        tools.analyze()
        self.assertEqual(tools.relation.kind, 'same')
        self.assertTrue(tools.copy_relation_button.isEnabled())

    def test_tools_preserve_calculator_selection_and_results_across_tabs_and_themes(self):
        self.locate('190-210')
        records = list(self.page.model.records)
        result = self.window.result
        tools = self.window.address_tools_page
        tools.convert()
        tools.analyze()
        formats, relation = tools.formats, tools.relation
        for theme in ('light', 'dark'):
            self.application.theme_manager.apply(theme, persist=False)
            self.window.tabs.setCurrentIndex(2)
            tools.copy_formats_button.click()
            tools.copy_relation_button.click()
            self.window.tabs.setCurrentIndex(1)
            self.assertIs(self.window.result, result)
            self.assertEqual(self.page.model.records, records)
            self.assertEqual(self.page.selected_indices(), [190])
            self.assertEqual(self.page.locator_range, (190,210))
            self.assertIs(tools.formats, formats)
            self.assertIs(tools.relation, relation)

    def test_tools_clipboard_failure_retains_both_results_and_can_retry(self):
        tools = self.window.address_tools_page
        tools.convert()
        tools.analyze()
        formats, relation = tools.formats, tools.relation
        with patch('services.clipboard_service.QApplication.clipboard', side_effect=RuntimeError('busy')), \
                patch('services.clipboard_service.QMessageBox.warning'):
            tools.copy_formats_button.click()
            tools.copy_relation_button.click()
        self.assertEqual(self.window.feedback.property('severity'), 'error')
        self.assertIs(tools.formats, formats)
        self.assertIs(tools.relation, relation)
        tools.copy_relation_button.click()
        self.assertEqual(QApplication.clipboard().text(), relation.as_text())

    def test_tools_minimum_window_scroll_and_background_in_both_themes(self):
        tools = self.window.address_tools_page
        self.window.tabs.setCurrentIndex(2)
        tools.address_input.setText('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff')
        tools.convert()
        tools.network_a_input.setText('::/0')
        tools.network_b_input.setText('::/0')
        tools.analyze()
        scroll = tools.findChild(QScrollArea)
        for theme in ('light', 'dark'):
            self.application.theme_manager.apply(theme, persist=False)
            self.window.resize(900,620)
            QApplication.processEvents()
            self.assertEqual(scroll.horizontalScrollBar().maximum(),0)
            for widget in (scroll.viewport(),scroll.widget()):
                rendered = widget.grab().toImage()
                self.assertEqual(rendered.pixelColor(1,1).name(), THEMES[theme]['surface'])
            self.assertIn(f'{2**128:,}', tools.relation_fields['counts'].text())
            scroll.ensureWidgetVisible(tools.copy_relation_button)
            QApplication.processEvents()
            self.assertTrue(scroll.viewport().rect().intersects(tools.copy_relation_button.geometry().translated(
                tools.copy_relation_button.parentWidget().mapTo(scroll.viewport(),tools.copy_relation_button.parentWidget().rect().topLeft()))))

    def test_calculation_background_uses_theme_with_dark_system_palette(self):
        original_palette = self.application.palette()
        try:
            palette = QPalette(original_palette)
            for role in (QPalette.ColorRole.Window, QPalette.ColorRole.Base,
                         QPalette.ColorRole.Button):
                palette.setColor(role, QColor('#202020'))
            self.application.setPalette(palette)
            self.window.tabs.setCurrentIndex(0)
            scroll = self.window.calculation_page.findChild(QScrollArea)
            for theme in ('light', 'dark'):
                self.application.theme_manager.apply(theme, persist=False)
                for width, height in ((1080, 800), (900, 620)):
                    with self.subTest(theme=theme, size=(width, height)):
                        self.window.resize(width, height)
                        QApplication.processEvents()
                        scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
                        QApplication.processEvents()
                        for widget in (scroll.viewport(), scroll.widget()):
                            rendered = widget.grab().toImage()
                            for y in (1, rendered.height() - 2):
                                self.assertEqual(rendered.pixelColor(1, y).name(), THEMES[theme]['surface'])
        finally:
            self.application.setPalette(original_palette)
            self.application.theme_manager.apply('light', persist=False)
            QApplication.processEvents()

    def test_theme_button_preserves_results_selection_and_location(self):
        self.locate('190-210')
        model_records = list(self.page.model.records)
        self.page.page_input.setText('3')
        for expected in ('dark', 'light'):
            QTest.mouseClick(self.window.theme_button, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            self.assertEqual(self.application.theme_manager.name, expected)
            self.assertEqual(self.page.page, 2)
            self.assertEqual(self.page.page_input.text(), '3')
            self.assertEqual(self.page.selected_indices(), [190])
            self.assertEqual(self.page.locator_range, (190, 210))
            self.assertEqual(self.page.model.records, model_records)
            self.assertIn('当前：'+('深色' if expected == 'dark' else '浅色'), self.window.theme_button.toolTip())
            self.assertTrue(self.window.theme_button.accessibleName())

    def test_theme_keyboard_shortcut_and_enter(self):
        self.window.activateWindow()
        self.page.locator_input.setFocus()
        QApplication.processEvents()
        QTest.keyClick(self.page.locator_input, Qt.Key.Key_T,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
        wait_until(lambda: self.application.theme_manager.name == 'dark')
        self.assertEqual(self.application.theme_manager.name, 'dark')
        self.window.theme_button.setFocus()
        QTest.keyClick(self.window.theme_button, Qt.Key.Key_Return)
        self.assertEqual(self.application.theme_manager.name, 'light')

    def test_theme_preference_is_loaded_by_a_new_manager(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory)/'settings.ini')
            first = ThemeManager(self.application, QSettings(path, QSettings.Format.IniFormat))
            try:
                self.assertTrue(first.apply('dark'))
                second = ThemeManager(self.application, QSettings(path, QSettings.Format.IniFormat))
                try:
                    self.assertEqual(second.name, 'dark')
                    self.assertEqual(self.application.property('themeName'), 'dark')
                finally:
                    second.deleteLater()
            finally:
                first.deleteLater()
                self.application.theme_manager.apply('light', persist=False)

    def test_invalid_saved_theme_falls_back_to_light(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = QSettings(str(Path(directory)/'settings.ini'), QSettings.Format.IniFormat)
            settings.setValue('appearance/theme', 'unknown')
            manager = ThemeManager(self.application, settings)
            self.assertEqual(manager.name, 'light')
            with self.assertRaises(ValueError):
                manager.apply('unknown')
            manager.deleteLater()

    def test_theme_save_failure_reports_unsaved_preference(self):
        with patch.object(self.settings, 'status', return_value=QSettings.Status.AccessError):
            self.window.theme_button.click()
        self.assertEqual(self.application.theme_manager.name, 'dark')
        self.assertIn('无法保存偏好', self.window.feedback.text())
        self.assertEqual(self.window.feedback.property('severity'), 'error')

    def test_theme_updates_existing_dialogs_and_highlight(self):
        self.locate()
        dialog = ExportRangeDialog(65536, self.window)
        dialog.show()
        try:
            for theme in ('dark', 'light'):
                self.application.theme_manager.apply(theme, persist=False)
                QApplication.processEvents()
                self.assertEqual(dialog.grab().toImage().pixelColor(1, 1).name(), THEMES[theme]['window'])
                self.assertEqual(dialog.start_input.palette().color(QPalette.ColorRole.Base).name(), THEMES[theme]['disabled'])
                color = self.page.model.data(self.page.model.index(89, 1), Qt.ItemDataRole.BackgroundRole)
                self.assertEqual(color.name(), THEMES[theme]['highlight'])
        finally:
            dialog.close()

    def test_theme_updates_icon_normal_hover_and_disabled_states(self):
        button = self.page.copy_page_button
        self.application.theme_manager.apply('dark', persist=False)
        for enabled, hovered in ((True, False), (True, True), (False, False)):
            button.setEnabled(enabled)
            button._hovered = hovered
            button._refresh_icon()
            state = 'disabled' if not enabled else 'hover' if hovered else 'normal'
            self.assertEqual(button.icon().cacheKey(), button._dark_icons[state].cacheKey())
            self.assertFalse(button.icon().isNull())

    def test_empty_selection_disables_actions(self):
        self.assertFalse(self.page.copy_selected_button.isEnabled())
        self.assertFalse(self.page.clear_selection_button.isEnabled())
        self.assertTrue(self.page.copy_page_button.isEnabled())

    def test_native_ctrl_click_and_shift_click(self):
        self.click_row(2)
        self.click_row(5, Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(self.page.selected_indices(), [2, 5])
        self.assertIn('非连续', self.page.selection_label.text())
        self.click_row(2, Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(self.page.selected_indices(), [5])
        self.click_row(2)
        self.click_row(6, Qt.KeyboardModifier.ShiftModifier)
        self.assertEqual(self.page.selected_indices(), [2, 3, 4, 5, 6])

    def test_native_select_all_copy_and_escape(self):
        self.page.table.setFocus()
        QTest.keyClick(self.page.table, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(len(self.page.selected_indices()), 100)
        QTest.keyClick(self.page.table, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(len(QApplication.clipboard().text().splitlines()), 100)
        QTest.keyClick(self.page.table, Qt.Key.Key_Escape)
        self.assertEqual(self.page.selected_indices(), [])
        self.assertFalse(self.page.copy_selected_button.isEnabled())

    def test_copy_order_does_not_depend_on_selection_order(self):
        for row in (9, 1, 4):
            self.page.table.selectionModel().select(self.page.model.index(row, 0),
                QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)
        self.page.copy_selected()
        self.assertEqual(QApplication.clipboard().text().splitlines(),
                         [self.page.model.records[row][1] for row in (1, 4, 9)])

    def test_locator_highlight_is_independent_of_selection(self):
        self.locate()
        self.assertEqual(self.page.selected_indices(), [90])
        self.assertIn('本页高亮 11 条', self.page.range_label.text())
        self.page.clear_selection()
        self.assertEqual(self.page.locator_range, (90, 210))
        self.page.show_page(2)
        self.assertEqual(self.page.selected_indices(), [])
        self.assertIn('本页高亮 100 条', self.page.range_label.text())
        self.page.show_page(3)
        self.assertIn('本页高亮 10 条', self.page.range_label.text())

    def test_clear_highlight_preserves_selection(self):
        self.locate()
        self.page.clear_locator_range()
        self.assertEqual(self.page.selected_indices(), [90])
        self.assertIsNone(self.page.model.locator_range)
        self.assertFalse(self.page.clear_range_button.isEnabled())

    def test_tabs_preserve_page_selection_and_highlight(self):
        self.locate('190-210')
        self.window.tabs.setCurrentIndex(0)
        self.window.tabs.setCurrentIndex(1)
        self.assertEqual(self.page.page, 2)
        self.assertEqual(self.page.selected_indices(), [190])
        self.assertEqual(self.page.locator_range, (190, 210))

    def test_page_size_preserves_original_anchor(self):
        self.page.show_page(8)
        self.page.page_size_combo.setCurrentText('25')
        self.assertEqual(self.page.page, 29)
        self.assertEqual(self.page.model.records[0][0], 701)
        self.page.page_size_combo.setCurrentText('200')
        self.assertEqual(self.page.page, 4)
        self.assertEqual(self.page.model.records[self.page.table.currentIndex().row()][0], 701)
        self.assertEqual(self.page.selected_indices(), [])

    def test_maximum_ipv6_space_keeps_only_one_page(self):
        self.window.calculation_page.network_input.setText('::/0')
        self.window.calculation_page.target_input.setText('128')
        self.window.calculate()
        self.locate(f'1-{2**128}')
        self.page.show_page(self.page.total_pages)
        self.assertEqual(self.page.model.rowCount(), 56)
        self.assertEqual(self.page.model.records[-1][0], 2**128)
        self.assertEqual(self.page.model.data(self.page.model.index(55, 0)), str(2**128))
        self.assertEqual(self.page.selected_indices(), [])
        self.assertIn('本页高亮 56 条', self.page.range_label.text())

    def test_page_jump_valid_and_invalid(self):
        self.page.page_input.setText('300')
        self.page.jump()
        self.assertEqual(self.page.page, 300)
        with patch('ui.results_page.QMessageBox.warning') as warning:
            self.page.page_input.setText('invalid')
            self.page.jump()
        warning.assert_called_once()
        self.assertEqual(self.page.page_input.text(), '300')

    def test_invalid_locator_retains_previous_range(self):
        self.locate()
        with patch('ui.results_page.QMessageBox.warning'):
            self.page.locator_input.setText('invalid')
            self.page.locate()
        self.assertEqual(self.page.locator_range, (90, 210))
        self.assertEqual(self.window.feedback.property('severity'), 'error')

    def test_invalid_recalculation_clears_old_actions(self):
        self.locate()
        self.window.calculation_page.network_input.setText('invalid')
        self.window.calculate()
        self.assertIsNone(self.window.result)
        self.assertEqual(self.page.model.rowCount(), 0)
        for button in (self.page.copy_selected_button, self.page.copy_page_button,
                       self.page.copy_range_button, self.page.export_button, self.page.locator_button):
            self.assertFalse(button.isEnabled())
        self.assertEqual(self.window.feedback.property('severity'), 'error')

    def test_recalculation_and_common_prefix_shortcut(self):
        self.locate()
        field = self.window.calculation_page
        index = field.prefix_shortcuts.findData(56)
        field.prefix_shortcuts.activated.emit(index)
        self.assertEqual(self.window.result.target_prefix, 56)
        self.assertIsNone(self.page.locator_range)
        self.assertEqual(self.page.selected_indices(), [])
        self.assertEqual(self.window.feedback.property('severity'), 'success')

    def test_statistics_copy_keeps_exact_integers(self):
        self.page.table.selectAll()
        self.page.copy_selection_statistics()
        self.assertIn(f'{100*2**64:,}', QApplication.clipboard().text())
        self.page.copy_page_statistics()
        self.assertIn('65,536', QApplication.clipboard().text())

    def test_clipboard_failure_preserves_selection_then_retry(self):
        self.page.table.selectAll()
        selected = self.page.selected_indices()
        with patch('services.clipboard_service.QApplication.clipboard', side_effect=RuntimeError('busy')), \
                patch('services.clipboard_service.QMessageBox.warning'):
            self.page.copy_selected()
        self.assertEqual(self.page.selected_indices(), selected)
        self.assertEqual(self.window.feedback.property('severity'), 'error')
        self.page.copy_selected()
        self.assertEqual(len(QApplication.clipboard().text().splitlines()), 100)
        self.assertEqual(self.window.feedback.property('severity'), 'success')

    def test_range_copy_dialog_prefill_validation_and_retry(self):
        dialog = RangeCopyDialog(self.window.result, self.window.clipboard, (90, 91), self.window)
        self.assertEqual(dialog.start_input.text(), '90')
        with patch.object(self.window.clipboard, 'copy_text', return_value=False):
            dialog.perform()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Rejected)
        dialog.perform()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
        self.assertEqual(len(QApplication.clipboard().text().splitlines()), 2)
        self.assertTrue(QApplication.clipboard().text().startswith('90\t'))

    def test_detail_navigation_and_copy(self):
        dialog = SubnetDetailDialog(self.window.result, 1, self.window.clipboard, self.window)
        dialog.index_changed.connect(self.page.select_index)
        self.assertFalse(dialog.previous_button.isEnabled())
        dialog.step(1)
        self.assertEqual(self.page.selected_indices(), [2])
        dialog.copy_details()
        self.assertIn('2026:1015:abcd:1::/64', QApplication.clipboard().text())
        self.assertIn(f'{2**64:,}', QApplication.clipboard().text())

    def test_export_range_all_and_huge_indices(self):
        dialog = ExportRangeDialog(2**128, self.window)
        dialog.confirm()
        self.assertEqual(dialog.span, (1, 2**128))
        dialog = ExportRangeDialog(2**128, self.window)
        dialog.range_radio.setChecked(True)
        dialog.start_input.setText(str(2**128-1))
        dialog.end_input.setText(str(2**128))
        dialog.confirm()
        self.assertEqual(dialog.span, (2**128-1, 2**128))

    def test_export_range_rejects_invalid_order(self):
        dialog = ExportRangeDialog(100, self.window)
        dialog.range_radio.setChecked(True)
        dialog.start_input.setText('90')
        dialog.end_input.setText('10')
        with patch('ui.dialogs.QMessageBox.warning') as warning:
            dialog.confirm()
        warning.assert_called_once()
        self.assertIsNone(dialog.span)

    def test_cancelling_progress_message_is_not_overwritten(self):
        dialog = ExportProgressDialog('out.txt', 2**128, self.window)
        dialog.request_cancel()
        dialog.set_progress(1024, 2**128)
        self.assertIn('正在取消', dialog.count_label.text())
        self.assertFalse(dialog.cancel_button.isEnabled())
        self.assertFalse(dialog.close())
        dialog.finish()

    def test_background_export_success_and_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('ui.export_controller.QMessageBox.information'):
                for filename in ('one.txt', 'two.xlsx'):
                    path = Path(directory)/filename
                    self.window.export_controller.start_export(path, path.suffix[1:], self.window.result, 90, 92)
                    self.assertTrue(self.window.export_service.busy)
                    self.assertFalse(self.page.export_button.isEnabled())
                    wait_until(lambda: not self.window.export_service.busy)
                    self.assertTrue(path.is_file())
                    self.assertIsNone(self.window.export_controller.progress_dialog)
                    self.assertTrue(self.page.export_button.isEnabled())
                    self.assertEqual(self.window.feedback.property('severity'), 'success')

    def test_export_cancel_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'existing.txt'
            path.write_text('original', encoding='utf-8')
            full = calculate('::/0', '128', preview_limit=0)
            self.window.export_controller.start_export(path, 'txt', full, 1, full.subnet_count)
            self.window.export_controller.cancel()
            wait_until(lambda: not self.window.export_service.busy)
            self.assertEqual(path.read_text(encoding='utf-8'), 'original')
            self.assertEqual([file.name for file in Path(directory).iterdir()], ['existing.txt'])

    def test_export_failure_releases_service_and_actions(self):
        with tempfile.TemporaryDirectory() as directory, patch('ui.export_controller.QMessageBox.warning'):
            path = Path(directory)/'missing'/'out.txt'
            self.window.export_controller.start_export(path, 'txt', self.window.result, 1, 10)
            wait_until(lambda: not self.window.export_service.busy)
            self.assertTrue(self.page.export_button.isEnabled())
            self.assertEqual(self.window.feedback.property('severity'), 'error')

    def test_thread_start_exception_restores_actions_and_allows_retry(self):
        with tempfile.TemporaryDirectory() as directory, patch('ui.export_controller.QMessageBox.warning') as warning:
            path = Path(directory)/'retry.txt'
            with patch.object(_ExportThread, 'start', side_effect=RuntimeError('cannot start thread')):
                self.window.export_controller.start_export(path, 'txt', self.window.result, 1, 3)
            warning.assert_called_once()
            self.assertFalse(self.window.export_service.busy)
            self.assertIsNone(self.window.export_controller.progress_dialog)
            self.assertTrue(self.page.export_button.isEnabled())
            self.assertTrue(self.window.calculation_page.calculate_button.isEnabled())
            self.assertFalse(path.exists())
            with patch('ui.export_controller.QMessageBox.information'):
                self.window.export_controller.start_export(path, 'txt', self.window.result, 1, 3)
                wait_until(lambda: not self.window.export_service.busy)
            self.assertEqual(len(path.read_text(encoding='utf-8').splitlines()), 3)

    def test_thread_start_without_running_is_reported_and_released(self):
        with patch.object(_ExportThread, 'start', return_value=None), \
                patch('ui.export_controller.QMessageBox.warning') as warning:
            self.window.export_controller.start_export('unused.txt', 'txt', self.window.result, 1, 3)
        warning.assert_called_once()
        self.assertFalse(self.window.export_service.busy)
        self.assertIsNone(self.window.export_controller.progress_dialog)
        self.assertTrue(self.page.export_button.isEnabled())

    def test_thread_without_outcome_has_recoverable_error(self):
        service = self.window.export_service
        service._thread = _ExportThread('unused.txt', self.window.result, 'txt', 1, 3, service)
        received = []
        service.completed.connect(received.append)
        with patch('ui.export_controller.QMessageBox.warning'):
            service._finish()
        self.assertEqual(received[0][0], 'error')
        self.assertFalse(service.busy)

    def test_repeated_navigation_selection_theme_and_resize(self):
        for step in range(150):
            self.page.page_size_combo.setCurrentIndex(step % 4)
            first = 1 + (step * 313) % 65000
            self.locate(f'{first}-{first+300}')
            self.assertEqual(self.page.selected_indices(), [first])
            self.assertLessEqual(self.page.model.rowCount(), 200)
            self.application.theme_manager.apply('dark' if step % 2 else 'light', persist=False)
            self.window.tabs.setCurrentIndex(0)
            self.window.resize(900 if step % 2 else 1080, 620 if step % 2 else 800)
            self.window.tabs.setCurrentIndex(1)
            QApplication.processEvents()
            self.assertEqual(self.page.selected_indices(), [first])
            self.assertEqual(self.page.locator_range, (first, first+300))
            self.page.clear_selection()
            self.assertEqual(self.page.selected_indices(), [])
            self.assertEqual(self.page.locator_range, (first, first+300))
            self.page.show_page(self.page.total_pages)
            self.assertEqual(self.page.model.records[-1][0], 65536)

    def test_minimize_restore_preserves_scroll_selection_and_range(self):
        self.locate('80-100')
        self.page.table.scrollToBottom()
        QApplication.processEvents()
        position = self.page.table.verticalScrollBar().value()
        self.window.showMinimized()
        QApplication.processEvents()
        self.window.showNormal()
        QApplication.processEvents()
        self.assertEqual(self.page.table.verticalScrollBar().value(), position)
        self.assertEqual(self.page.selected_indices(), [80])
        self.assertEqual(self.page.locator_range, (80, 100))

    def test_close_waits_for_cancel_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'out.txt'
            result = calculate('::/0', '128', preview_limit=0)
            self.window.export_controller.start_export(path, 'txt', result, 1, result.subnet_count)
            self.window.close()
            self.assertTrue(self.window.closing_after_export)
            wait_until(lambda: not self.window.export_service.busy and not self.window.isVisible())
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_main_window_controls_fit_minimum_size(self):
        self.window.resize(900, 620)
        QApplication.processEvents()
        self.assertGreaterEqual(self.page.table.height(), 150)
        for widget in (self.page.locator_input, self.page.clear_range_button,
                       self.page.export_button, self.page.page_size_combo):
            position = widget.mapTo(self.window, widget.rect().bottomRight())
            self.assertLess(position.x(), self.window.width())
            self.assertLess(position.y(), self.window.height())

    def test_export_request_respects_selected_text_filter_without_extension(self):
        controller = self.window.export_controller
        with tempfile.TemporaryDirectory() as directory, \
                patch('ui.export_controller.ExportRangeDialog') as selector, \
                patch('ui.export_controller.QFileDialog.getSaveFileName',
                      return_value=(str(Path(directory)/'subnets'), '文本文件 (*.txt)')), \
                patch('ui.export_controller.QMessageBox.information'), \
                patch.object(controller, '_confirm', return_value=True):
            selector.return_value.exec.return_value = QDialog.DialogCode.Accepted
            selector.return_value.span = (90, 92)
            controller.request_export(self.window.result)
            wait_until(lambda: not self.window.export_service.busy)
            path = Path(directory)/'subnets.txt'
            self.assertEqual(path.read_text(encoding='utf-8').splitlines()[0], '2026:1015:abcd:59::/64')
            self.assertEqual(len(path.read_text(encoding='utf-8').splitlines()), 3)

    def test_export_request_rejects_unsupported_extension(self):
        with patch('ui.export_controller.ExportRangeDialog') as selector, \
                patch('ui.export_controller.QFileDialog.getSaveFileName', return_value=('out.csv', '文本文件 (*.txt)')), \
                patch('ui.export_controller.QMessageBox.warning') as warning:
            selector.return_value.exec.return_value = QDialog.DialogCode.Accepted
            selector.return_value.span = (1, 3)
            self.window.export_controller.request_export(self.window.result)
        warning.assert_called_once()
        self.assertFalse(self.window.export_service.busy)

    def test_cancelled_file_selection_does_not_start_export(self):
        with patch('ui.export_controller.ExportRangeDialog') as selector, \
                patch('ui.export_controller.QFileDialog.getSaveFileName', return_value=('', '')):
            selector.return_value.exec.return_value = QDialog.DialogCode.Accepted
            selector.return_value.span = (1, 3)
            self.window.export_controller.request_export(self.window.result)
        self.assertFalse(self.window.export_service.busy)

    def test_oversized_export_confirmation_can_cancel_before_file_selection(self):
        result = calculate('::/0', '128', preview_limit=0)
        with patch('ui.export_controller.ExportRangeDialog') as selector, \
                patch('ui.export_controller.QFileDialog.getSaveFileName') as save, \
                patch.object(self.window.export_controller, '_confirm', return_value=False):
            selector.return_value.exec.return_value = QDialog.DialogCode.Accepted
            selector.return_value.span = (1, result.subnet_count)
            self.window.export_controller.request_export(result)
        save.assert_not_called()
        self.assertFalse(self.window.export_service.busy)

    def test_background_service_rejects_concurrent_start(self):
        with tempfile.TemporaryDirectory() as directory:
            result = calculate('::/0', '128', preview_limit=0)
            self.window.export_service.start(Path(directory)/'out.txt', result, 'txt', 1, result.subnet_count)
            with self.assertRaises(RuntimeError):
                self.window.export_service.start(Path(directory)/'other.txt', result, 'txt', 1, 3)
            self.window.export_service.cancel()
            wait_until(lambda: not self.window.export_service.busy)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_progress_signals_preserve_arbitrary_precision_counters(self):
        worker = _ExportThread('unused.txt', self.window.result, 'txt', 1, 2**128)
        received = []
        worker.progress.connect(lambda done, total: received.append((done, total)))
        worker.report_progress(2**80+1, 2**128)
        self.assertEqual(received, [(2**80+1, 2**128)])

    def test_icon_resources_are_available_in_all_states(self):
        from ui.widgets import IconButton
        from app_info import resource_path
        buttons = self.window.findChildren(IconButton)
        buttons += [IconButton(name, name) for name in ('close_small', 'confirm_small', 'stop_small')]
        for button in buttons:
            for state, icon in button._icons.items():
                self.assertFalse(icon.isNull(), (button.objectName(), state))
                self.assertTrue(resource_path(f'assets/{button.asset_name}_{state}.png').is_file())

    def test_enter_shortcut_opens_detail_for_current_row(self):
        self.page.select_index(5)
        with patch('ui.results_page.SubnetDetailDialog') as dialog:
            QTest.keyClick(self.page.table, Qt.Key.Key_Return)
            QApplication.processEvents()
        self.assertEqual(dialog.call_args.args[1], 5)
        dialog.return_value.exec.assert_called_once()


if __name__ == '__main__':
    unittest.main()
