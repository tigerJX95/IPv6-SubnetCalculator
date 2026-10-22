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

"""并发文件提交、完整恢复副本、确认期间冲突和保存快照回归。"""
from pathlib import Path
from contextlib import contextmanager
from ipaddress import IPv6Network
from threading import Event
from time import monotonic
import json,multiprocessing,os,tempfile,unittest
from unittest.mock import patch
from core.file_commit import capture_file,SaveConflict
from core.subnet_export import export_all,ExportCancelled
from core.calculation_plan import CalculationPlan
from services.plan_storage import save_plan,load_plan
from services.text_output import save_text_atomic
from core.ipv6_core import InputError


def competing_writer(path,snapshot,barrier,queue,text):
    barrier.wait(timeout=10)
    try:save_text_atomic(path,text,expected=snapshot)
    except SaveConflict as exc:queue.put(('conflict',str(exc.recovery)))
    except Exception as exc:queue.put(('error',repr(exc)))
    else:queue.put(('ok',text))


class SaveConflictCoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'结果.txt'
    def tearDown(self):self.temp.cleanup()
    def test_new_target_appears_while_exporting_preserves_both(self):
        def rival(done,total):self.path.write_text('external')
        with self.assertRaises(SaveConflict) as caught:export_all(self.path,IPv6Network('::/126'),128,'txt',progress=rival)
        self.assertEqual(self.path.read_text(),'external')
        self.assertEqual(caught.exception.recovery.read_text(),'::/128\n::1/128\n::2/128\n::3/128\n')
    def test_existing_target_modified_during_export_is_preserved(self):
        self.path.write_text('approved')
        def rival(done,total):self.path.write_text('new external value')
        with self.assertRaises(SaveConflict) as caught:export_all(self.path,IPv6Network('::/126'),128,'txt',progress=rival)
        self.assertEqual(self.path.read_text(),'new external value');self.assertTrue(caught.exception.recovery.is_file())
    def test_target_replaced_with_same_size_and_mtime_detected_by_identity(self):
        self.path.write_text('aaaa');expected=capture_file(self.path);info=self.path.stat()
        rival=self.path.with_name('rival.txt');rival.write_text('bbbb');os.utime(rival,ns=(info.st_atime_ns,info.st_mtime_ns));os.replace(rival,self.path)
        with self.assertRaises(SaveConflict):save_text_atomic(self.path,'ours',expected=expected)
        self.assertEqual(self.path.read_text(),'bbbb')
    def test_target_removed_after_approval_is_not_recreated_silently(self):
        self.path.write_text('approved');expected=capture_file(self.path);self.path.unlink()
        with self.assertRaises(SaveConflict) as caught:save_text_atomic(self.path,'ours',expected=expected)
        self.assertFalse(self.path.exists());self.assertEqual(caught.exception.recovery.read_text(),'ours')
    def test_excel_conflict_preserves_a_complete_workbook(self):
        import zipfile
        path=self.path.with_suffix('.xlsx')
        def rival(done,total):path.write_text('external')
        with self.assertRaises(SaveConflict) as caught:export_all(path,IPv6Network('::/126'),128,'xlsx',progress=rival)
        self.assertEqual(path.read_text(),'external')
        with zipfile.ZipFile(caught.exception.recovery) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(archive.read('xl/worksheets/sheet1.xml').count(b'<row '),5)

    def test_plan_conflict_preserves_valid_recoverable_json(self):
        path=self.path.with_suffix('.json');expected=capture_file(path);path.write_text('external')
        with self.assertRaises(SaveConflict) as caught:save_plan(path,CalculationPlan('::/0',128,'ours'),expected=expected)
        self.assertEqual(path.read_text(),'external');self.assertEqual(load_plan(caught.exception.recovery).name,'ours')
    def test_new_publication_race_has_no_exists_replace_gap(self):
        import core.file_commit as module
        publish=module._publish_new
        def race(temp,destination):
            if Path(destination)==capture_file(self.path).path:self.path.write_text('rival at publication')
            return publish(temp,destination)
        with patch.object(module,'_publish_new',side_effect=race),self.assertRaises(SaveConflict):save_text_atomic(self.path,'ours')
        self.assertEqual(self.path.read_text(),'rival at publication')
    def test_unsupported_no_overwrite_operation_fails_without_fallback(self):
        if os.name=='nt':self.skipTest('POSIX hard-link path')
        with patch('core.file_commit.os.link',side_effect=OSError('unsupported')),patch('core.file_commit.os.replace') as replace:
            with self.assertRaises(OSError):save_text_atomic(self.path,'ours')
        replace.assert_not_called();self.assertFalse(self.path.exists());self.assertEqual(list(self.path.parent.iterdir()),[])
    def test_cancel_keeps_existing_file_and_leaves_no_recovery(self):
        self.path.write_text('original');stop=Event();stop.set()
        with self.assertRaises(ExportCancelled):export_all(self.path,IPv6Network('::/126'),128,'txt',stop=stop)
        self.assertEqual(self.path.read_text(),'original');self.assertEqual(list(self.path.parent.iterdir()),[self.path])
    def test_busy_commit_keeps_complete_output(self):
        self.path.write_text('original')
        @contextmanager
        def busy(path):raise SaveConflict(path);yield
        with patch('core.file_commit._existing_lock',busy),self.assertRaises(SaveConflict) as caught:save_text_atomic(self.path,'ours')
        self.assertEqual(self.path.read_text(),'original');self.assertEqual(caught.exception.recovery.read_text(),'ours')
    def test_symbolic_link_target_not_followed_or_replaced(self):
        other=self.path.with_name('other.txt');other.write_text('original')
        try:self.path.symlink_to(other)
        except OSError:self.skipTest('Symlinks unavailable')
        with self.assertRaises(InputError):save_text_atomic(self.path,'ours')
        self.assertEqual(other.read_text(),'original');self.assertTrue(self.path.is_symlink())
    def test_directory_target_rejected(self):
        self.path.mkdir()
        with self.assertRaises(InputError):save_text_atomic(self.path,'ours')
        self.assertTrue(self.path.is_dir())
    def _two_writers(self,existing):
        if existing:self.path.write_text('original')
        snapshot=capture_file(self.path);ctx=multiprocessing.get_context('spawn');barrier=ctx.Barrier(2);queue=ctx.Queue()
        workers=[ctx.Process(target=competing_writer,args=(self.path,snapshot,barrier,queue,value)) for value in ('first','second')]
        for worker in workers:worker.start()
        for worker in workers:
            worker.join(15)
            if worker.is_alive():worker.terminate();worker.join();self.fail('writer timeout')
            self.assertEqual(worker.exitcode,0)
        outcomes=[queue.get(timeout=3) for _ in workers];queue.close();queue.join_thread()
        self.assertEqual(sorted(x[0] for x in outcomes),['conflict','ok'])
        saved=next(x[1] for x in outcomes if x[0]=='ok');recovery=Path(next(x[1] for x in outcomes if x[0]=='conflict'))
        self.assertEqual(self.path.read_text(),saved);self.assertNotEqual(recovery.read_text(),saved)
    def test_two_processes_new_target_only_one_commits(self):self._two_writers(False)
    def test_two_processes_same_existing_revision_only_one_commits(self):self._two_writers(True)


from app import create_application
from PyQt6.QtCore import QSettings,QCoreApplication,QEvent
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from ui.main_window import MainWindow
from ui.standard_dialogs import QMessageBox
from services.language_service import display


class SaveConflictUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.app=create_application([],QSettings(str(Path(cls.temp.name)/'prefs.ini'),QSettings.Format.IniFormat));cls.app.setQuitOnLastWindowClosed(False)
    @classmethod
    def tearDownClass(cls):cls.app.language_manager.apply('zh_CN',persist=False);cls.temp.cleanup()
    def setUp(self):
        self.app.language_manager.apply('zh_CN',persist=False);self.w=MainWindow();self.w.calculate();self.page=self.w.subnet_list_page
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'output.txt'
    def tearDown(self):
        self.w.subnet_list_page.project_controller.saved = self.w.subnet_list_page.project_controller.snapshot()
        deadline=monotonic()+6
        while self.w.export_service.busy:
            QApplication.processEvents();QTest.qWait(3)
            if monotonic()>deadline:self.fail('export timeout')
        self.w.plan_controller.path=None;self.w.calculation_page.plan_name_input.clear();self.w.close();self.w.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);QApplication.processEvents();self.temp.cleanup()
    def test_plan_changes_in_picker_are_not_marked_saved(self):
        self.w.calculation_page.plan_name_input.setText('A');path=self.path.with_suffix('.json')
        def choose(*args,**kwargs):self.w.calculation_page.plan_name_input.setText('B');return str(path),''
        with patch('ui.plan_controller.QFileDialog.getSaveFileName',side_effect=choose):self.assertFalse(self.w.plan_controller.save(save_as=True))
        self.assertFalse(path.exists());self.assertIsNone(self.w.plan_controller.saved_document)
    def test_changes_after_snapshot_write_remain_dirty(self):
        from services.plan_storage import save_plan as original
        self.w.calculation_page.plan_name_input.setText('A');path=self.path.with_suffix('.json')
        def writer(*args,**kwargs):
            original(*args,**kwargs);self.w.calculation_page.plan_name_input.setText('B')
        with patch('ui.plan_controller.QFileDialog.getSaveFileName',return_value=(str(path),'')),patch('ui.plan_controller.save_plan',side_effect=writer):self.assertTrue(self.w.plan_controller.save(save_as=True))
        self.assertEqual(load_plan(path).name,'A');self.assertNotEqual(self.w.plan_controller.saved_document,self.w.plan_controller.document())

    def test_plan_target_changed_in_confirmation_is_preserved(self):
        path=self.path.with_suffix('.json');path.write_text('original')
        def confirm(*args,**kwargs):path.write_text('external changes');return QMessageBox.StandardButton.Yes
        with patch('ui.plan_controller.QFileDialog.getSaveFileName',return_value=(str(path),'')),patch('ui.plan_controller.QMessageBox.question',side_effect=confirm),patch('ui.plan_controller.QMessageBox.warning'):
            self.assertFalse(self.w.plan_controller.save(save_as=True))
        self.assertEqual(path.read_text(),'external changes');self.assertEqual(len(list(path.parent.glob('IPv6-Recovered-*.json'))),1)
    def test_list_target_changed_in_confirmation_is_preserved(self):
        self.path.write_text('original');self.page.editor.setPlainText('::/0')
        def confirm(*args,**kwargs):self.path.write_text('external changes');return QMessageBox.StandardButton.Yes
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName',return_value=(str(self.path),'')),patch('ui.list_output_controller.QMessageBox.question',side_effect=confirm):self.page.output_controller.save_input()
        self.assertEqual(self.path.read_text(),'external changes');self.assertEqual(len(list(self.path.parent.glob('IPv6-Recovered-*.txt'))),1)
    def test_english_conflict_explains_recovery_without_chinese(self):
        self.app.language_manager.apply('en_US',persist=False)
        message=display(SaveConflict(self.path,self.path.with_name('recovered.txt')).args[0])
        self.assertIn('recovered.txt',message);self.assertNotRegex(message,r'[\u4e00-\u9fff]')
    def test_export_controller_passes_confirmation_revision_to_worker(self):
        from ui.localized_widgets import QDialog
        self.path.write_text('original')
        def confirm(*args,**kwargs):self.path.write_text('external changes');return True
        with patch('ui.export_controller.ExportRangeDialog') as selector,patch('ui.export_controller.QFileDialog.getSaveFileName',return_value=(str(self.path),'')),patch.object(self.w.export_controller,'_confirm',side_effect=confirm),patch('ui.export_controller.QMessageBox.warning'):
            selector.return_value.exec.return_value=QDialog.DialogCode.Accepted;selector.return_value.span=(1,3)
            self.w.export_controller.request_export(self.w.result)
            deadline=monotonic()+6
            while self.w.export_service.busy:
                QApplication.processEvents();QTest.qWait(3)
                if monotonic()>deadline:self.fail('export timeout')
        self.assertEqual(self.path.read_text(),'external changes');self.assertEqual(len(list(self.path.parent.glob('IPv6-Recovered-*.txt'))),1)
