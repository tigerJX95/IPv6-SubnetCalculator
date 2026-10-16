"""选择容量、跨页高亮及真实 Tk 交互回归。图形测试需显示服务器。"""
import tkinter as tk
import unittest

from main import App
from subnet_tools import summarize_selection


class SelectionSummaryTests(unittest.TestCase):
    def test_empty_selection(self):
        stats = summarize_selection([], range(1, 101), 2**64)
        self.assertEqual((stats.count, stats.first, stats.last, stats.address_count),
                         (0, None, None, 0))
        self.assertFalse(stats.contiguous)

    def test_single_subnet(self):
        stats = summarize_selection([5], range(1, 26), 2**64)
        self.assertEqual((stats.count, stats.first, stats.last, stats.address_count),
                         (1, 5, 5, 2**64))
        self.assertTrue(stats.contiguous)

    def test_contiguous_unsorted_duplicates(self):
        stats = summarize_selection([6, 4, 5, 4], range(1, 26), 16)
        self.assertTrue(stats.contiguous)
        self.assertEqual((stats.count, stats.first, stats.last, stats.address_count),
                         (3, 4, 6, 48))

    def test_non_contiguous_capacity_excludes_gaps(self):
        stats = summarize_selection([1, 100], range(1, 101), 2**64)
        self.assertFalse(stats.contiguous)
        self.assertEqual(stats.address_count, 2 * 2**64)

    def test_out_of_page_selection_is_excluded(self):
        stats = summarize_selection([1, 101, 120], range(101, 126), 1)
        self.assertEqual((stats.count, stats.first, stats.last), (2, 101, 120))

    def test_range_total_is_distinct_from_page_matches(self):
        stats = summarize_selection([90], range(1, 101), 1, (90, 210))
        self.assertEqual((stats.count, stats.highlighted_on_page, stats.highlighted_total),
                         (1, 11, 121))

    def test_last_page_partial_range(self):
        stats = summarize_selection([], range(201, 218), 1, (90, 210))
        self.assertEqual((stats.highlighted_on_page, stats.highlighted_total), (10, 121))

    def test_maximum_ipv6_range_uses_bounded_page(self):
        total = 2**128
        stats = summarize_selection([total], range(total - 15, total + 1), 1, (1, total))
        self.assertEqual((stats.highlighted_on_page, stats.highlighted_total), (16, total))
        self.assertEqual((stats.first, stats.address_count), (total, 1))

    def test_entire_space_address_capacity_is_exact(self):
        self.assertEqual(summarize_selection([1], [1], 2**128).address_count, 2**128)


class ResultsInteractionTests(unittest.TestCase):
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
        self.app.geometry('1080x760')
        self.app.calculate()
        self.app.update()
        self.event_time = 1000

    def selected_indices(self):
        return sorted(int(self.app.table.item(item, 'values')[0])
                      for item in self.app.table.selection())

    def locate_range(self, value='90-210'):
        self.app.locator_mode.set('按子网序号范围')
        self.app.locator_value.set(value)
        self.app.locate_selected()
        self.app.update()

    def click_row(self, row, state=0):
        table = self.app.table
        item = table.get_children()[row - 1]
        table.see(item)
        self.app.update()
        x, y, width, height = table.bbox(item)
        # 使用相隔足够远的事件时间，避免测试中快速单击被解释为双击。
        self.event_time += 1000
        for event in ('<ButtonPress-1>', '<ButtonRelease-1>'):
            table.event_generate(event, x=x + width // 2, y=y + height // 2,
                                 state=state, time=self.event_time)
        self.app.update()

    def test_no_selection_disables_copy(self):
        self.assertEqual(str(self.app.copy_selected_button['state']), 'disabled')
        self.assertEqual(str(self.app.clear_selection_button['state']), 'disabled')

    def test_native_ctrl_click_toggles_non_contiguous_rows(self):
        self.click_row(2)
        self.click_row(5, state=4)
        self.assertEqual(self.selected_indices(), [2, 5])
        self.assertIn('非连续', self.app.selection_status.get())
        self.click_row(2, state=4)
        self.assertEqual(self.selected_indices(), [5])

    def test_native_shift_click_selects_interval(self):
        self.click_row(2)
        self.click_row(6, state=1)
        self.assertEqual(self.selected_indices(), [2, 3, 4, 5, 6])
        self.assertNotIn('非连续', self.app.selection_status.get())

    def test_select_all_copy_and_escape_shortcuts(self):
        self.app.table.focus_force()
        self.app.update()
        self.app.table.event_generate('<Control-a>')
        self.app.update()
        self.assertEqual(len(self.selected_indices()), 100)
        self.app.table.event_generate('<Control-c>')
        self.app.update()
        self.assertEqual(len(self.app.clipboard_get().splitlines()), 100)
        self.app.table.event_generate('<Escape>')
        self.app.update()
        self.assertEqual(self.selected_indices(), [])
        self.assertEqual(str(self.app.copy_selected_button['state']), 'disabled')

    def test_copy_is_in_table_order(self):
        items = self.app.table.get_children()
        self.app.table.selection_set([items[9], items[1], items[4]])
        self.app.copy_selected()
        self.assertEqual(self.app.clipboard_get().splitlines(),
                         [self.app.table.item(items[n], 'values')[1] for n in (1, 4, 9)])

    def test_locator_highlight_does_not_select_all_matches(self):
        self.locate_range()
        self.assertEqual(self.selected_indices(), [90])
        self.assertIn('共 121 条 · 本页高亮 11 条', self.app.range_status.get())
        self.app.clear_selection()
        self.assertEqual(self.app.locator_range, (90, 210))
        self.assertEqual(sum('range_match' in self.app.table.item(item, 'tags')
                             for item in self.app.table.get_children()), 11)

    def test_paging_and_page_size_preserve_highlight_without_selection(self):
        self.locate_range()
        self.app.show_page(2)
        self.app.update()
        self.assertEqual(self.selected_indices(), [])
        self.assertIn('共 121 条 · 本页高亮 100 条', self.app.range_status.get())
        self.app.show_page(3)
        self.app.update()
        self.assertIn('本页高亮 10 条', self.app.range_status.get())
        self.app.size.set('25')
        self.app.change_size()
        self.app.update()
        self.assertEqual(self.app.locator_range, (90, 210))
        self.assertIn('本页高亮 0 条', self.app.range_status.get())

    def test_clear_highlight_preserves_selection_and_restores_stripes(self):
        self.locate_range()
        self.app.clear_locator_range()
        self.app.update()
        self.assertEqual(self.selected_indices(), [90])
        self.assertTrue(all('range_match' not in self.app.table.item(item, 'tags')
                            for item in self.app.table.get_children()))
        self.assertIn('未设置', self.app.range_status.get())

    def test_tabs_preserve_selection_page_and_range(self):
        self.locate_range('190-210')
        for tab in (self.app.calculation_tab, self.app.results_tab):
            self.app.notebook.select(tab)
            self.app.update()
        self.assertEqual(self.app.page, 2)
        self.assertEqual(self.selected_indices(), [190])
        self.assertEqual(self.app.locator_range, (190, 210))

    def test_recalculation_clears_selection_range_and_statistics(self):
        self.locate_range()
        self.app.calculate()
        self.app.update()
        self.assertEqual(self.selected_indices(), [])
        self.assertIsNone(self.app.locator_range)
        self.assertIn('本页选中 0 条', self.app.selection_status.get())

    def test_invalid_recalculation_clears_old_result_actions(self):
        self.locate_range()
        self.app.net.set('invalid')
        self.app.calculate()
        self.app.update()
        self.assertIsNone(self.app.result)
        self.assertEqual(self.app.table.get_children(), ())
        self.assertEqual(str(self.app.copy_selected_button['state']), 'disabled')
        self.assertEqual(str(self.app.clear_range_button['state']), 'disabled')

    def test_copied_statistics_preserve_exact_capacity(self):
        self.app._key_select_all()
        self.app._copy_selection_statistics()
        self.assertIn(f'{100 * 2**64:,}', self.app.clipboard_get())

    def test_full_ipv6_space_can_be_located_and_paged(self):
        self.app.net.set('::/0')
        self.app.target.set('128')
        self.app.calculate()
        self.locate_range(f'1-{2**128}')
        self.app.show_last()
        self.app.update()
        self.assertEqual(len(self.app.table.get_children()), 56)
        self.assertEqual(self.selected_indices(), [])
        self.assertIn(f'{2**128:,}', self.app._range_tooltip.text)
        self.assertIn('本页高亮 56 条', self.app.range_status.get())


if __name__ == '__main__':
    unittest.main()
