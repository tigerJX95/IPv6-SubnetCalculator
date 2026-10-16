"""V0.7 的导出精度、分页位置及失败重试回归。"""
import tempfile
import tkinter as tk
import unittest
import zipfile
from ipaddress import IPv6Network
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from main import App
from subnet_export import export_all


class ExcelPrecisionTests(unittest.TestCase):
    def exported_cells(self, start, end):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'indices.xlsx'
            report = export_all(path, IPv6Network('::/0'), 128, 'xlsx', start=start, end=end)
            self.assertEqual(report.rows, end - start + 1)
            with zipfile.ZipFile(path) as archive:
                sheet = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
        ns = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        rows = sheet.findall('x:sheetData/x:row', ns)[1:]
        return [row.find('x:c', ns) for row in rows], ns

    def test_fifteen_digit_indices_remain_numeric(self):
        cells, ns = self.exported_cells(10**15 - 2, 10**15 - 1)
        self.assertTrue(all(cell.get('t') is None for cell in cells))
        self.assertEqual([cell.find('x:v', ns).text for cell in cells],
                         [str(10**15 - 2), str(10**15 - 1)])

    def test_sixteen_digit_indices_are_exact_text(self):
        cells, ns = self.exported_cells(10**15 + 1, 10**15 + 2)
        self.assertTrue(all(cell.get('t') == 'inlineStr' for cell in cells))
        self.assertEqual([cell.find('x:is/x:t', ns).text for cell in cells],
                         [str(10**15 + 1), str(10**15 + 2)])

    def test_crossing_precision_boundary_uses_one_column_type(self):
        cells, ns = self.exported_cells(10**15 - 1, 10**15 + 1)
        self.assertTrue(all(cell.get('t') == 'inlineStr' for cell in cells))
        self.assertEqual([cell.find('x:is/x:t', ns).text for cell in cells],
                         [str(n) for n in range(10**15 - 1, 10**15 + 2)])

    def test_final_ipv6_indices_are_preserved(self):
        cells, ns = self.exported_cells(2**128 - 1, 2**128)
        self.assertEqual([cell.find('x:is/x:t', ns).text for cell in cells],
                         [str(2**128 - 1), str(2**128)])


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.app = App()
        except tk.TclError as exc:
            if 'no display name' in str(exc) or "couldn't connect to display" in str(exc):
                raise unittest.SkipTest(f'Tk 显示服务器不可用：{exc}')
            raise
        cls.app.update()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def setUp(self):
        self.app = type(self).app
        self.app.net.set('2026:1015:abcd::/48')
        self.app.target.set('64')
        self.app.size.set('100')
        self.app.calculate()
        self.app.update()

    def assert_status_style(self, expected):
        self.assertEqual(str(self.app.status_label['style']), expected)
        self.assertEqual(str(self.app.result_status_label['style']), expected)

    def test_page_size_preserves_original_page_start(self):
        self.app.show_page(8)
        self.app.size.set('25')
        self.app.change_size()
        self.app.update()
        self.assertEqual(self.app.page, 29)
        self.assertEqual(self.app.table.item(self.app.table.get_children()[0], 'values')[0], '701')
        self.assertEqual(self.app.table.selection(), ())

    def test_larger_page_size_contains_original_page_start(self):
        self.app.size.set('25')
        self.app.show_page(6)  # 原页首序号 126。
        self.app.size.set('200')
        self.app.change_size()
        self.app.update()
        self.assertEqual(self.app.page, 1)
        self.assertEqual(self.app.table.item(self.app.table.focus(), 'values')[0], '126')
        self.assertEqual(self.app.table.selection(), ())

    def test_page_size_preserves_last_page_of_full_ipv6_space(self):
        self.app.net.set('::/0')
        self.app.target.set('128')
        self.app.calculate()
        self.app.show_last()
        original_first = int(self.app.table.item(self.app.table.get_children()[0], 'values')[0])
        self.app.size.set('25')
        self.app.change_size()
        self.assertEqual(self.app.page, (original_first - 1) // 25 + 1)
        self.assertEqual(self.app.table.item(self.app.table.focus(), 'values')[0], str(original_first))

    def test_status_colors_match_for_error_and_recovery(self):
        self.app.net.set('invalid')
        self.app.calculate()
        self.assert_status_style('Warn.TLabel')
        self.assertEqual(str(self.app.jump_input['state']), 'disabled')
        self.app.net.set('2026:1015:abcd::/48')
        self.app.calculate()
        self.assert_status_style('Success.TLabel')
        self.assertEqual(str(self.app.jump_input['state']), 'normal')

    def test_clipboard_unavailable_preserves_selection_and_can_retry(self):
        self.app._key_select_all()
        selected = self.app.table.selection()
        with patch.object(self.app, 'clipboard_clear', side_effect=tk.TclError('clipboard busy')), \
                patch('main.messagebox.showwarning') as warning:
            self.app.copy_selected()
        warning.assert_called_once()
        self.assertEqual(self.app.table.selection(), selected)
        self.assertIn('复制失败', self.app.status.get())
        self.assert_status_style('Warn.TLabel')
        self.app.copy_selected()
        self.assertEqual(len(self.app.clipboard_get().splitlines()), 100)
        self.assert_status_style('Success.TLabel')

    def test_clipboard_append_error_is_also_handled(self):
        with patch.object(self.app, 'clipboard_append', side_effect=tk.TclError('clipboard busy')), \
                patch('main.messagebox.showwarning'):
            self.assertFalse(self.app._copy_to_clipboard('content', 'copied'))
        self.assert_status_style('Warn.TLabel')

    def test_range_copy_failure_keeps_dialog_open_for_retry(self):
        self.app.locator_range = (90, 91)
        clipboard_calls = []
        dialog_retained = []
        def prepare(dialog, fixed_size=None):
            buttons = []
            def visit(widget):
                for child in widget.winfo_children():
                    if child.winfo_class() == 'TButton' and child.cget('text') == '复制':
                        buttons.append(child)
                    visit(child)
            visit(dialog)
            def attempt():
                with patch.object(self.app, 'clipboard_clear', side_effect=tk.TclError('busy')), \
                        patch('main.messagebox.showwarning'):
                    buttons[0].invoke()
                dialog_retained.append(bool(dialog.winfo_exists()))
                if dialog.winfo_exists():
                    try:
                        buttons[0].invoke()
                        clipboard_calls.extend(self.app.clipboard_get().splitlines())
                    finally:
                        if dialog.winfo_exists():
                            dialog.destroy()
            self.app.after_idle(attempt)
        with patch.object(self.app, '_show_centered_dialog', side_effect=prepare):
            self.app.copy_index_range()
        self.assertEqual(dialog_retained, [True])
        self.assertEqual(len(clipboard_calls), 2)
        self.assertTrue(clipboard_calls[0].startswith('90\t'))

    def test_invalid_locator_preserves_previous_highlight(self):
        self.app.locator_mode.set('按子网序号范围')
        self.app.locator_value.set('90-210')
        self.app.locate_selected()
        self.app.locator_value.set('invalid')
        with patch('main.messagebox.showwarning'):
            self.app.locate_selected()
        self.assertEqual(self.app.locator_range, (90, 210))
        self.assertIn('定位失败', self.app.status.get())
        self.assert_status_style('Warn.TLabel')

    def test_locator_icons_follow_enabled_state(self):
        self.assertEqual(str(self.app.locator_button['state']), 'normal')
        self.assertEqual(str(self.app.clear_range_button['state']), 'disabled')
        self.app.locator_mode.set('按子网序号')
        self.app.locator_value.set('2')
        self.app.locate_selected()
        self.assertEqual(str(self.app.clear_range_button['state']), 'normal')
        self.app.clear_locator_range()
        self.assertEqual(str(self.app.clear_range_button['state']), 'disabled')


if __name__ == '__main__':
    unittest.main()
