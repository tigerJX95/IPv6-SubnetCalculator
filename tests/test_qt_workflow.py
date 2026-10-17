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

from PyQt6.QtCore import Qt, QItemSelectionModel, QTimer, QCoreApplication, QEvent, QSettings
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QDialog, QScrollArea
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
        cls.application.setQuitOnLastWindowClosed(False)

    @classmethod
    def tearDownClass(cls):
        cls.settings_dir.cleanup()

    def setUp(self):
        self.application.theme_manager.apply('light', persist=False)
        self.window = MainWindow()
        self.window.show()
        self.window.calculate()
        self.page = self.window.results_page
        QApplication.processEvents()

    def tearDown(self):
        if self.window.export_service.busy:
            self.window.export_controller.cancel()
            wait_until(lambda: not self.window.export_service.busy)
        self.window.close()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QApplication.processEvents()

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

    def test_default_calculation_and_tabs(self):
        self.assertEqual(self.window.tabs.count(), 2)
        self.assertEqual(self.window.tabs.currentWidget(), self.page)
        self.assertEqual(self.page.model.rowCount(), 100)
        self.assertEqual(self.page.model.records[0], (1, '2026:1015:abcd::/64'))
        self.assertEqual(self.window.calculation_page.fields['count'].text(), '65,536')

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
            path.write_text('original')
            full = calculate('::/0', '128', preview_limit=0)
            self.window.export_controller.start_export(path, 'txt', full, 1, full.subnet_count)
            self.window.export_controller.cancel()
            wait_until(lambda: not self.window.export_service.busy)
            self.assertEqual(path.read_text(), 'original')
            self.assertEqual([file.name for file in Path(directory).iterdir()], ['existing.txt'])

    def test_export_failure_releases_service_and_actions(self):
        with tempfile.TemporaryDirectory() as directory, patch('ui.export_controller.QMessageBox.warning'):
            path = Path(directory)/'missing'/'out.txt'
            self.window.export_controller.start_export(path, 'txt', self.window.result, 1, 10)
            wait_until(lambda: not self.window.export_service.busy)
            self.assertTrue(self.page.export_button.isEnabled())
            self.assertEqual(self.window.feedback.property('severity'), 'error')

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
            self.assertEqual(path.read_text().splitlines()[0], '2026:1015:abcd:59::/64')
            self.assertEqual(len(path.read_text().splitlines()), 3)

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
                self.assertTrue(resource_path(f'assets/{button.objectName()}_{state}.png').is_file())

    def test_enter_shortcut_opens_detail_for_current_row(self):
        self.page.select_index(5)
        with patch('ui.results_page.SubnetDetailDialog') as dialog:
            QTest.keyClick(self.page.table, Qt.Key.Key_Return)
            QApplication.processEvents()
        self.assertEqual(dialog.call_args.args[1], 5)
        dialog.return_value.exec.assert_called_once()


if __name__ == '__main__':
    unittest.main()
