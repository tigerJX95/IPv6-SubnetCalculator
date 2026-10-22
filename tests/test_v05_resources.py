"""Verify resources actually used by the current Qt interface."""
import unittest
from pathlib import Path
from app import create_application
from ui.main_window import MainWindow
from ui.widgets import IconButton

ROOT = Path(__file__).resolve().parents[1]


class IconResourcesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_application([])

    def setUp(self):
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def test_all_active_icons_have_three_states(self):
        buttons = self.window.findChildren(IconButton)
        self.assertGreater(len(buttons), 10)
        for button in buttons:
            for state in ('normal', 'hover', 'disabled'):
                with self.subTest(name=button.asset_name, state=state):
                    self.assertTrue((ROOT/'assets'/f'{button.asset_name}_{state}.png').is_file())
                    self.assertFalse(button._icons[state].isNull())

    def test_tabs_use_current_qt_pages(self):
        for page in (self.window.calculation_page, self.window.results_page,
                     self.window.address_tools_page, self.window.subnet_list_page):
            self.assertGreaterEqual(self.window.tabs.indexOf(page), 0)
        self.assertEqual(self.window.tabs.count(), 4)
