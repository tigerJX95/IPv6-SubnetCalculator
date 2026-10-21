# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Planning persistence: bounded JSON, conflict preservation and UI transactions."""
import json
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
from PyQt6.QtCore import QSettings, QCoreApplication, QEvent
from PyQt6.QtWidgets import QApplication
from app import create_application
from core.ipv6_core import InputError
from core.file_commit import capture_file, SaveConflict
from core.planning_project import PlanningProject, project_to_payload, project_from_payload
from services.project_storage import load_project, save_project, MAX_PROJECT_BYTES
from services.plan_storage import load_plan, save_plan
from core.calculation_plan import CalculationPlan
from ui.main_window import MainWindow
from ui.standard_dialogs import QMessageBox

class ProjectStorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'planning.json'
        self.draft=PlanningProject('# 部门 A\n::1/128\ninvalid draft\n','unfinished parent','/64','2',4)

    def test_roundtrip_preserves_draft_comments_and_unicode(self):
        save_project(self.path,self.draft)
        self.assertEqual(load_project(self.path),self.draft)

    def test_schema_and_types_are_strict(self):
        base=project_to_payload(self.draft)
        for key,value in [('version',True),('version',2),('format','other'),('tab',True),('tab',5),('parent',None),('count',1),('prefix','1'*6),('text','\x00'),('parent','\ud800')]:
            with self.subTest(key=key,value=repr(value)),self.assertRaises(InputError):
                project_from_payload(dict(base,**{key:value}))
        with self.assertRaises(InputError):project_from_payload(dict(base,unknown='x'))

    def test_limits_apply_to_decoded_text(self):
        for text in ['x'*(1048576+1),'\n'*20001,'::/128\n'*5001]:
            with self.assertRaises(InputError):project_to_payload(replace(self.draft,text=text))

    def test_empty_list_and_full_limit_comments_are_supported(self):
        for text in ['', '#'+('a'*1048575)]:
            p=replace(self.draft,text=text);save_project(self.path,p)
            self.assertEqual(load_project(self.path),p)

    def test_duplicate_keys_nonfinite_and_malformed_json(self):
        for content in ['{"format":1,"format":2}', '{"x":NaN}', '[', '[]', '{"x":'+ '['*1100]:
            self.path.write_text(content)
            with self.subTest(content=content[:30]),self.assertRaises(InputError):load_project(self.path)

    def test_oversized_file_is_rejected(self):
        self.path.write_bytes(b' '*(MAX_PROJECT_BYTES+1))
        with self.assertRaises(InputError):load_project(self.path)

    def test_conflicting_new_file_is_preserved_with_recovery(self):
        expected=capture_file(self.path);self.path.write_text('external')
        with self.assertRaises(SaveConflict) as caught:save_project(self.path,self.draft,expected=expected)
        self.assertEqual(self.path.read_text(),'external')
        self.assertEqual(load_project(caught.exception.recovery),self.draft)

    def test_invalid_save_leaves_existing_file_untouched(self):
        self.path.write_text('original')
        with self.assertRaises(InputError):save_project(self.path,replace(self.draft,tab=6))
        self.assertEqual(self.path.read_text(),'original')

    def test_calculation_and_planning_formats_cannot_be_confused(self):
        save_plan(self.path,CalculationPlan('::/0',64))
        with self.assertRaises(InputError):load_project(self.path)
        save_project(self.path,self.draft)
        with self.assertRaises(InputError):load_plan(self.path)

class ProjectUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.app=create_application([],QSettings(str(Path(cls.tmp.name)/'ui.ini'),QSettings.Format.IniFormat))
        cls.app.setQuitOnLastWindowClosed(False)

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def setUp(self):
        self.w=MainWindow();self.w.show();self.page=self.w.subnet_list_page
        self.c=self.page.project_controller
        self.path=Path(self.tmp.name)/'ui.json'
        self.page.editor.setPlainText('# source\n::1/128')
        self.w.tabs.setCurrentWidget(self.page)
        QApplication.processEvents()

    def tearDown(self):
        self.app.language_manager.apply('zh_CN',persist=False)
        self.w.close();self.w.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);QApplication.processEvents()

    def test_restore_inputs_and_clear_derived_results(self):
        p=PlanningProject('# 保留\n::/128','::/0','128','2',4)
        save_project(self.path,p)
        with patch('ui.project_controller.QFileDialog.getOpenFileName',return_value=(str(self.path),'')),patch('ui.project_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes):
            self.assertTrue(self.c.open())
        self.assertEqual(self.c.snapshot(),p)
        self.assertIsNone(self.page.planning.free_result)
        self.assertIsNone(self.page.planning.allocation.result)
        self.assertIsNone(self.page.analysis)

    def test_cancel_restore_preserves_current_work(self):
        save_project(self.path,PlanningProject('','::/0','64','1'))
        before=self.c.snapshot()
        with patch('ui.project_controller.QFileDialog.getOpenFileName',return_value=(str(self.path),'')),patch('ui.project_controller.QMessageBox.question',return_value=QMessageBox.StandardButton.No):
            self.assertFalse(self.c.open())
        self.assertEqual(self.c.snapshot(),before)

    def test_corrupt_project_never_prompts_or_changes_inputs(self):
        self.path.write_text('broken');before=self.c.snapshot()
        with patch('ui.project_controller.QFileDialog.getOpenFileName',return_value=(str(self.path),'')),patch('ui.project_controller.QMessageBox.question') as ask:
            self.assertFalse(self.c.open());ask.assert_not_called()
        self.assertEqual(self.c.snapshot(),before)

    def test_save_dialog_input_change_is_rejected(self):
        def selected(*a,**kw):
            self.page.editor.setPlainText('::2/128');return str(self.path),''
        self.path.unlink(missing_ok=True)
        with patch('ui.project_controller.QFileDialog.getSaveFileName',side_effect=selected):
            self.assertFalse(self.c.save())
        self.assertFalse(self.path.exists())

    def test_nested_restore_callback_change_is_rejected(self):
        save_project(self.path,PlanningProject('','::/0','64','1'))
        def answer(*a,**kw):
            self.page.editor.setPlainText('::3/128');return QMessageBox.StandardButton.Yes
        with patch('ui.project_controller.QFileDialog.getOpenFileName',return_value=(str(self.path),'')),patch('ui.project_controller.QMessageBox.question',side_effect=answer):
            self.assertFalse(self.c.open())
        self.assertEqual(self.page.editor.toPlainText(),'::3/128')

    def test_save_restore_status_and_live_language(self):
        self.path.unlink(missing_ok=True)
        with patch('ui.project_controller.QFileDialog.getSaveFileName',return_value=(str(self.path),'')):
            self.assertTrue(self.c.save())
        before=self.c.snapshot()
        for language in ('en_US','zh_CN','en_US'):
            self.app.language_manager.apply(language,persist=False)
            self.assertEqual(self.c.snapshot(),before)
        for widget in (self.c.open_button,self.c.save_button):
            self.assertNotRegex(widget.toolTip(),r'[\u4e00-\u9fff]')
        self.page.editor.setPlainText('::2/128')
        self.assertIn('unsaved',self.c.label.text().lower())

    def test_controls_available_in_allocation_at_minimum_size(self):
        self.w.resize(900,620);self.page.result_tabs.setCurrentIndex(4)
        for language in ('en_US','zh_CN'):
            for theme in ('light','dark'):
                self.app.language_manager.apply(language,persist=False)
                self.app.theme_manager.apply(theme,persist=False)
                QApplication.processEvents()
                self.assertTrue(self.c.open_button.isVisible());self.assertTrue(self.c.save_button.isVisible())
                self.assertGreater(self.page.planning.allocation.table.viewport().height(),35)

    def test_busy_save_and_load_do_not_show_dialog(self):
        with patch.object(type(self.page.service),'busy',new_callable=__import__('unittest.mock',fromlist=['PropertyMock']).PropertyMock,return_value=True),patch('ui.project_controller.QFileDialog.getSaveFileName') as save,patch('ui.project_controller.QFileDialog.getOpenFileName') as load:
            self.assertFalse(self.c.save());self.assertFalse(self.c.open());save.assert_not_called();load.assert_not_called()
