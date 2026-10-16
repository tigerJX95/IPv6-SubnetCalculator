"""确保 V0.5 仅打包界面仍在使用的图标资源。"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
STATES = ('normal', 'hover', 'disabled')
ACTIVE = ('calculate', 'copy', 'copy_page', 'copy_range', 'clear_selection', 'export',
          'first_small', 'previous_small', 'next_small', 'last_small', 'jump_small')

class IconResourcesTest(unittest.TestCase):
    def test_all_active_icons_have_three_states(self):
        for name in ACTIVE:
            for state in STATES:
                with self.subTest(name=name, state=state):
                    self.assertTrue((ASSETS / f'{name}_{state}.png').is_file())

    def test_no_obsolete_icons(self):
        expected = {f'{name}_{state}.png' for name in ACTIVE for state in STATES}
        self.assertEqual({p.name for p in ASSETS.glob('*.png')}, expected)

    def test_tabs_not_old_result_popup(self):
        source = (ROOT / 'main.py').read_text(encoding='utf-8')
        self.assertIn("text='子网计算'", source)
        self.assertIn("text='子网结果'", source)
        self.assertNotIn('open_results', source)
        self.assertNotIn('preview_table', source)
        self.assertNotIn('result_window', source)
