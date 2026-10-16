"""独立结果窗口与当前页统计的专项测试。"""
import unittest
from pathlib import Path
from subnet_tools import visible_selection_counts


class TestV05(unittest.TestCase):
    def test_no_selection(self):
        self.assertEqual(visible_selection_counts([], range(1, 101)), (0, 0))

    def test_selected_vs_range(self):
        self.assertEqual(visible_selection_counts([30, 31, 900], range(1, 101), (25, 40)),
                         (2, 16))

    def test_out_of_page_range(self):
        self.assertEqual(visible_selection_counts([2], range(101, 201), (1, 100)), (0, 0))

    def test_huge_range_constant_page(self):
        self.assertEqual(visible_selection_counts([], range(201, 301), (1, 10**30)), (0, 100))

    def test_one_matching_row(self):
        self.assertEqual(visible_selection_counts([5], range(1, 26), (5, 5)), (1, 1))

    def test_two_tabs_wiring(self):
        code = (Path(__file__).resolve().parents[1] / 'main.py').read_text(encoding='utf-8')
        for expected in ('ttk.Notebook(base)', "text='子网计算'", "text='子网结果'",
                         'self.notebook.select(self.results_tab)',
                         'self.selection_status', 'self.results_tab'):
            self.assertIn(expected, code)
        self.assertNotIn('self.preview_table', code)
        self.assertNotIn('self.result_window', code)
        self.assertNotIn('open_results_window', code)


if __name__ == '__main__':
    unittest.main()
