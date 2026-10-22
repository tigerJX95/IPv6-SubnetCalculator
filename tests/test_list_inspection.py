# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
import random
import tempfile
import unittest
from pathlib import Path
from ipaddress import IPv6Address, summarize_address_range
from unittest.mock import patch
from PyQt6.QtCore import QSettings, QCoreApplication, QEvent
from PyQt6.QtWidgets import QApplication
from app import create_application
from core.ipv6_core import InputError
from core.list_inspection import lookup_address, compare_coverage, size
from core.planning_project import PlanningProject
from services.project_storage import save_project
from ui.main_window import MainWindow
from ui.list_inspection_dialog import ListInspectionDialog
from ui.standard_dialogs import QMessageBox


class InspectionCoreTests(unittest.TestCase):
    def test_lookup_longest_prefix_and_original_line_numbers(self):
        result = lookup_address('# comment\n\n::/0\n::/64\n::1/128\n::1/128', '::1')
        self.assertEqual([r.line for r in result.matches], [5, 6, 4, 3])

    def test_lookup_inclusive_endpoints(self):
        for query in ['2001:db8::', '2001:db8::ffff:ffff:ffff:ffff']:
            self.assertEqual(len(lookup_address('2001:db8::/64', query).matches), 1)
        self.assertFalse(lookup_address('2001:db8::/64', '2001:db8:0:1::').matches)

    def test_lookup_full_ipv6_endpoints(self):
        for query in ['::', 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff']:
            self.assertEqual(len(lookup_address('::/0', query).matches), 1)

    def test_lookup_rejects_invalid_addresses(self):
        for query in ['1.2.3.4', '::/64', 'bad', 'fe80::1%eth0', '']:
            with self.subTest(query=query), self.assertRaises(InputError):
                lookup_address('::/0', query)

    def test_invalid_list_never_silently_returns_partial_result(self):
        with self.assertRaises(InputError): lookup_address('::/0\nbad', '::1')
        with self.assertRaises(InputError): compare_coverage('::/0', 'bad')
        with self.assertRaises(InputError): compare_coverage('bad', '::/0')

    def test_empty_lists(self):
        result = compare_coverage('', '# empty')
        self.assertEqual((result.added, result.removed, result.common), ((), (), ()))
        self.assertFalse(lookup_address('', '::1').matches)

    def test_equivalent_split_duplicates_and_host_bits(self):
        result = compare_coverage('::1/126\n::/127', '::/127\n::2/127\n::2/128')
        self.assertFalse(result.added or result.removed)
        self.assertEqual(size(result.common), 4)

    def test_added_removed_direction(self):
        result = compare_coverage('::/127', '::1/128\n::2/128')
        self.assertEqual(result.added, ((2, 2),))
        self.assertEqual(result.removed, ((0, 0),))
        self.assertEqual(result.common, ((1, 1),))

    def test_full_space_exact_counts(self):
        result = compare_coverage('::/0', '::/128')
        self.assertEqual(size(result.removed), 2**128 - 1)
        self.assertEqual(size(result.common), 1)
        self.assertEqual(size(compare_coverage('', '::/0').added), 2**128)

    def test_randomized_against_independent_sets(self):
        rng = random.Random(812)
        for _ in range(300):
            sets = [{i for i in range(128) if rng.randrange(3) == 0} for _ in range(2)]
            inputs = ['\n'.join(str(IPv6Address(i))+'/128' for i in values) for values in sets]
            result = compare_coverage(*inputs)
            for actual, expected in [(result.added, sets[1]-sets[0]),
                                     (result.removed, sets[0]-sets[1]),
                                     (result.common, sets[0]&sets[1])]:
                self.assertEqual({i for start, end in actual for i in range(start, end+1)}, expected)

    def test_maximum_records(self):
        text = '\n'.join(f'{IPv6Address(i)}/128' for i in range(5000))
        self.assertEqual(size(compare_coverage('', text).added), 5000)
        self.assertEqual(len(lookup_address('::/0\n'*5000, '::').matches), 5000)
        with self.assertRaises(InputError): compare_coverage('', text+'\n::/128')


class InspectionUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.app = create_application([], QSettings(str(Path(cls.tmp.name)/'inspection.ini'), QSettings.Format.IniFormat))
        cls.app.setQuitOnLastWindowClosed(False)

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def setUp(self):
        self.w = MainWindow()
        self.page = self.w.subnet_list_page
        self.page.editor.setPlainText('# baseline\n::/127')
        self.d = ListInspectionDialog(self.page)
        self.p = self.d.comparison
        self.path = Path(self.tmp.name)/'comparison.txt'
        self.path.unlink(missing_ok=True)

    def tearDown(self):
        self.d.deleteLater()
        self.page.project_controller.saved = self.page.project_controller.snapshot()
        self.app.language_manager.apply('zh_CN', persist=False)
        self.w.close(); self.w.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QApplication.processEvents()

    def test_lookup_and_comparison_do_not_modify_project(self):
        before = self.page.project_controller.snapshot()
        self.d.lookup.input.setText('::1'); self.assertTrue(self.d.lookup.run())
        self.p.input.setPlainText('::2/128'); self.assertTrue(self.p.run())
        self.assertEqual(before, self.page.project_controller.snapshot())

    def test_edits_invalidate_results_and_output(self):
        self.p.run(); self.assertTrue(self.p.save_button.isEnabled())
        self.p.input.setPlainText('::2/128')
        self.assertIsNone(self.p.result)
        self.assertFalse(self.p.save_button.isEnabled())
        self.assertEqual(self.p.report.toPlainText(), '')
        self.app.language_manager.apply('en_US', persist=False)
        self.assertEqual(self.p.report.toPlainText(), '')

    def test_invalid_query_disables_copy_and_save(self):
        self.d.lookup.input.setText('bad')
        self.assertFalse(self.d.lookup.run())
        self.assertFalse(self.d.lookup.copy_button.isEnabled())

    def test_bilingual_result_and_input_preservation(self):
        self.p.input.setPlainText('# keep comment\n::2/128'); self.p.run()
        self.app.language_manager.apply('en_US', persist=False)
        self.assertIn('Added addresses: 1', self.p.report.toPlainText())
        self.assertIn('List Lookup', self.d.windowTitle())
        self.assertEqual(self.p.value(), '# keep comment\n::2/128')
        self.app.language_manager.apply('zh_CN', persist=False)
        self.assertIn('新增地址数：1', self.p.report.toPlainText())

    def test_import_project_only_uses_list_without_restoring_parameters(self):
        path = Path(self.tmp.name)/'candidate.json'
        save_project(path, PlanningProject('::2/128', 'draft', '64', '9'))
        before = self.page.project_controller.snapshot()
        with patch('ui.list_inspection_dialog.QFileDialog.getOpenFileName', return_value=(str(path), '')):
            self.assertTrue(self.p.import_file())
        self.assertEqual(self.p.value(), '::2/128')
        self.assertEqual(before, self.page.project_controller.snapshot())

    def test_damaged_import_clears_old_result_preserves_input(self):
        path = Path(self.tmp.name)/'broken.json'; path.write_text('{')
        self.p.input.setPlainText('::1/128'); self.p.run()
        with patch('ui.list_inspection_dialog.QFileDialog.getOpenFileName', return_value=(str(path), '')):
            self.assertFalse(self.p.import_file())
        self.assertEqual(self.p.value(), '::1/128')
        self.assertIsNone(self.p.result)
        self.assertFalse(self.p.save_button.isEnabled())

    def test_save_report_and_cancel_overwrite(self):
        self.p.run()
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName', return_value=(str(self.path), '')):
            self.p.save()
        self.assertIn('移除地址数：2', self.path.read_text())
        self.path.write_text('external')
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName', return_value=(str(self.path), '')), patch('ui.list_output_controller.QMessageBox.question', return_value=QMessageBox.StandardButton.No):
            self.p.save()
        self.assertEqual(self.path.read_text(), 'external')

    def test_save_dialog_edits_abort_stale_report(self):
        self.p.run()
        def changed(*args, **kwargs):
            self.p.input.setPlainText('::/0')
            return str(self.path), ''
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName', side_effect=changed): self.p.save()
        self.assertFalse(self.path.exists())

    def test_save_conflict_preserves_external_output(self):
        self.path.write_text('original'); self.p.run()
        before = self.path.stat()
        def changed(*args, **kwargs):
            import os
            self.path.write_text('external')
            # Filesystem timestamp granularity must not make this race timing-dependent.
            os.utime(self.path, ns=(before.st_atime_ns, before.st_mtime_ns + 2_000_000_000))
            return QMessageBox.StandardButton.Yes
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName', return_value=(str(self.path), '')), patch('ui.list_output_controller.QMessageBox.question', side_effect=changed): self.p.save()
        self.assertEqual(self.path.read_text(), 'external')

    def test_copy_uses_existing_clipboard_service(self):
        self.p.run()
        with patch.object(self.page.clipboard, 'copy_text', return_value=True) as copied:
            self.p.copy()
        self.assertIn('IPv6 清单覆盖差异报告', str(copied.call_args.args[0]))
