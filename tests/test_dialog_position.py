"""Qt dialogs stay centered on their parent and inside the available screen."""
import unittest
from PyQt6.QtCore import QPoint, QRect
from PyQt6.QtWidgets import QWidget
from app import create_application
from ui.dialogs import AppDialog


class DialogPositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_application([])

    def check_position(self, parent_position):
        parent = QWidget()
        parent.resize(600, 400)
        parent.move(parent_position)
        parent.show()
        dialog = AppDialog('Position', parent)
        dialog.resize(470, 230)
        try:
            dialog.show()
            self.app.processEvents()
            area = dialog.screen().availableGeometry()
            center = parent.frameGeometry().center()
            expected = QPoint(max(area.left(), min(center.x()-dialog.width()//2, area.right()-dialog.width()+1)),
                              max(area.top(), min(center.y()-dialog.height()//2, area.bottom()-dialog.height()+1)))
            self.assertEqual(dialog.pos(), expected)
            self.assertTrue(area.contains(QRect(dialog.pos(), dialog.size())))
        finally:
            dialog.close()
            parent.close()
            dialog.deleteLater()
            parent.deleteLater()

    def test_center_on_main_window(self):
        self.check_position(QPoint(40, 40))

    def test_clamp_to_visible_screen(self):
        self.check_position(self.app.primaryScreen().availableGeometry().bottomRight())

    def test_parent_near_top_left(self):
        self.check_position(self.app.primaryScreen().availableGeometry().topLeft())
