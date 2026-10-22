# SPDX-License-Identifier: GPL-3.0-or-later
"""Planning drafts survive cancelled closing, replacement and failed saves."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PyQt6.QtCore import QSettings, QCoreApplication, QEvent
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QApplication
from app import create_application
from core.planning_project import PlanningProject
from services.project_storage import save_project, load_project
from ui.main_window import MainWindow
from ui.standard_dialogs import QMessageBox

B=QMessageBox.StandardButton
class ProjectProtectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.app=create_application([],QSettings(str(Path(cls.tmp.name)/'protect.ini'),QSettings.Format.IniFormat))
        cls.app.setQuitOnLastWindowClosed(False)
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def setUp(self):
        self.w=MainWindow();self.p=self.w.subnet_list_page;self.c=self.p.project_controller
        self.path=Path(self.tmp.name)/'draft.json';self.path.unlink(missing_ok=True)
    def tearDown(self):
        self.app.language_manager.apply('zh_CN',persist=False)
        self.w.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);QApplication.processEvents()
    def edit(self): self.p.editor.setPlainText('# draft\n::/128')
    def decide(self,answer): return patch('ui.project_controller.QMessageBox.question',return_value=answer)
    def test_clean_and_tab_only_close_without_prompt(self):
        for tab in range(5):
            self.p.result_tabs.setCurrentIndex(tab)
            with patch('ui.project_controller.QMessageBox.question') as ask:
                self.assertTrue(self.c.confirm_discard());ask.assert_not_called()
    def test_each_input_marks_new_draft_dirty_and_reverting_clears_it(self):
        for field in (self.p.editor,self.p.planning.parent_input,self.p.planning.allocation.prefix_input,self.p.planning.allocation.count_input):
            initial=field.toPlainText() if field is self.p.editor else field.text()
            setter=field.setPlainText if field is self.p.editor else field.setText
            setter('2' if initial != '2' else '3');self.assertTrue(self.c.dirty());setter(initial);self.assertFalse(self.c.dirty())
    def test_cancel_preserves_draft(self):
        self.edit();before=self.c.snapshot()
        with self.decide(B.Cancel):self.assertFalse(self.c.confirm_discard())
        self.assertEqual(self.c.snapshot(),before);self.assertTrue(self.c.dirty())
    def test_discard_allows_exit_without_marking_saved(self):
        self.edit()
        with self.decide(B.Discard):self.assertTrue(self.c.confirm_discard())
        self.assertTrue(self.c.dirty())
    def test_save_before_exit_writes_complete_draft(self):
        self.edit();before=self.c.snapshot()
        with self.decide(B.Save),patch('ui.project_controller.QFileDialog.getSaveFileName',return_value=(str(self.path),'')):
            self.assertTrue(self.c.confirm_discard())
        self.assertEqual(load_project(self.path),before);self.assertFalse(self.c.dirty())
    def test_cancelled_save_prevents_exit(self):
        self.edit()
        with self.decide(B.Save),patch('ui.project_controller.QFileDialog.getSaveFileName',return_value=('','')):
            self.assertFalse(self.c.confirm_discard())
        self.assertTrue(self.c.dirty())
    def test_write_failure_prevents_exit(self):
        self.edit()
        with self.decide(B.Save),patch('ui.project_controller.QFileDialog.getSaveFileName',return_value=(str(self.path),'')),patch('ui.project_controller.save_project',side_effect=OSError('denied')):
            self.assertFalse(self.c.confirm_discard())
        self.assertTrue(self.c.dirty());self.assertFalse(self.path.exists())
    def test_changes_during_confirmation_abort_discard(self):
        self.edit()
        def change(*a,**kw):self.p.editor.setPlainText('::2/128');return B.Discard
        with patch('ui.project_controller.QMessageBox.question',side_effect=change):self.assertFalse(self.c.confirm_discard())
        self.assertEqual(self.p.editor.toPlainText(),'::2/128')
    def test_nested_confirmation_is_rejected(self):
        self.edit()
        def nested(*a,**kw):self.assertFalse(self.c.confirm_discard());return B.Cancel
        with patch('ui.project_controller.QMessageBox.question',side_effect=nested):self.assertFalse(self.c.confirm_discard())
        self.assertFalse(self.c.confirming)
    def test_close_cancel_and_discard_are_respected(self):
        self.edit()
        for choice,accepted in ((B.Cancel,False),(B.Discard,True)):
            event=QCloseEvent()
            with self.decide(choice):self.w.closeEvent(event)
            self.assertEqual(event.isAccepted(),accepted)
    def test_open_cancel_retains_current_project(self):
        self.edit();before=self.c.snapshot();save_project(self.path,PlanningProject('::1/128','','64','1'))
        with self.decide(B.Cancel),patch('ui.project_controller.QFileDialog.getOpenFileName',return_value=(str(self.path),'')):
            self.assertFalse(self.c.open())
        self.assertEqual(self.c.snapshot(),before)
    def test_open_saves_current_draft_before_replacing(self):
        self.edit();before=self.c.snapshot();other=self.path.with_name('other.json')
        target=PlanningProject('::1/128','','64','1');save_project(other,target)
        with patch('ui.project_controller.QMessageBox.question',side_effect=[B.Save,B.Yes]),patch('ui.project_controller.QFileDialog.getOpenFileName',return_value=(str(other),'')),patch('ui.project_controller.QFileDialog.getSaveFileName',return_value=(str(self.path),'')):
            self.assertTrue(self.c.open())
        self.assertEqual(load_project(self.path),before);self.assertEqual(self.c.snapshot(),target);self.assertFalse(self.c.dirty())
    def test_dirty_label_is_bilingual_for_new_draft(self):
        self.edit()
        for lang,marker in [('en_US','unsaved'),('zh_CN','未保存')]:
            self.app.language_manager.apply(lang,persist=False)
            self.assertIn(marker,self.c.label.text().lower())
            if lang=='en_US':self.assertNotRegex(self.c.label.text(),r'[\u4e00-\u9fff]')
    def test_confirmation_translation(self):
        from services.language_service import display
        from core.localized_text import text
        self.app.language_manager.apply('en_US',persist=False)
        for source in ('未保存的规划项目','当前规划项目有未保存的更改，是否先保存？'):
            self.assertNotRegex(display(text(source)),r'[\u4e00-\u9fff]')
