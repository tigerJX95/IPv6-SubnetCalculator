"""导出窗口定位专项测试。"""
import unittest
from main import centered_dialog_position


class DialogPositionTests(unittest.TestCase):
    def test_center_on_main_window(self):
        self.assertEqual(centered_dialog_position((100, 100, 1080, 910), (470, 230), (1920, 1080)), (405, 440))

    def test_clamp_to_visible_screen(self):
        self.assertEqual(centered_dialog_position((1850, 900, 600, 500), (470, 230), (1920, 1080)), (1450, 850))

    def test_small_screen(self):
        self.assertEqual(centered_dialog_position((0, 0, 600, 400), (470, 230), (800, 600)), (65, 85))
