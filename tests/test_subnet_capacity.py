# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Independent capacity oracle and snapshot/report integration checks."""
import random
import unittest
from ipaddress import IPv6Address, IPv6Network
from unittest.mock import patch
from core.ipv6_core import InputError
from core.subnet_capacity import capacity_overview
from core.subnet_allocation import suggest_subnets
from tests import test_list_inspection as fixtures


class CapacityCoreTests(unittest.TestCase):
    def test_full_ipv6_exact_integer_capacity(self):
        r = capacity_overview('', '::/0')
        self.assertEqual(len(r.rows), 129)
        self.assertEqual(str(r.largest), '::/0')
        self.assertEqual(r.rows[-1].capacity, 2**128)
        self.assertTrue(all(row.capacity == 2**row.prefix and row.fragmented_addresses == 0 for row in r.rows))

    def test_fully_occupied(self):
        r = capacity_overview('::/0', '::/0')
        self.assertIsNone(r.largest)
        self.assertTrue(all(row.capacity == row.fragmented_addresses == 0 for row in r.rows))

    def test_single_address_parents(self):
        for text, count in [('', 1), ('::1/128', 0)]:
            r = capacity_overview(text, '::1/128')
            self.assertEqual(len(r.rows), 1)
            self.assertEqual(r.rows[0].capacity, count)

    def test_fragmentation_alignment_not_total_division(self):
        r = capacity_overview('::/128\n::3/128', '::/126')
        self.assertEqual(r.rows[1].capacity, 0)
        self.assertEqual(r.rows[1].fragmented_addresses, 2)
        self.assertEqual(str(r.largest), '::1/128')

    def test_duplicates_and_host_bits_do_not_double_count(self):
        a = capacity_overview('::1/127\n::/128\n::/127', '::1/124')
        b = capacity_overview('::/127', '::/124')
        self.assertEqual(a.rows, b.rows)
        self.assertEqual(a.largest, b.largest)
        self.assertTrue(a.free.parent_normalized)

    def test_outside_parent_and_invalid_input_rejected(self):
        for text, parent in [('::/0', '::/64'), ('bad', '::/0'), ('', 'bad'), ('', '1.2.3.0/24')]:
            with self.subTest(text=text, parent=parent), self.assertRaises(InputError):
                capacity_overview(text, parent)

    def test_top_of_ipv6_space(self):
        r = capacity_overview('ffff:ffff:ffff:ffff:ffff:ffff:ffff:fffe/128',
                              'ffff:ffff:ffff:ffff:ffff:ffff:ffff:fffe/127')
        self.assertEqual(str(r.largest), 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128')
        self.assertEqual(r.rows[-1].capacity, 1)

    def test_random_against_enumerated_aligned_blocks_and_suggestions(self):
        rng = random.Random(114)
        for _ in range(120):
            used = {i for i in range(256) if rng.randrange(4) == 0}
            r = capacity_overview('\n'.join(f'{IPv6Address(i)}/128' for i in used), '::/120')
            largest = None
            for row in r.rows:
                block = 1 << (128-row.prefix)
                expected = [i for i in range(0, 256, block) if not (set(range(i, i+block)) & used)]
                self.assertEqual(row.capacity, len(expected))
                self.assertEqual(row.fragmented_addresses, 256-len(used)-len(expected)*block)
                self.assertEqual(suggest_subnets(r.free, row.prefix, 1).capacity, row.capacity)
                if largest is None and expected:
                    largest = IPv6Network((expected[0], row.prefix))
            self.assertEqual(r.largest, largest)

    def test_uses_complete_ranges_when_cidr_preview_truncated(self):
        with patch('core.subnet_planning.MAX_FREE_DETAILS', 1):
            r = capacity_overview('::1/128\n::3/128', '::/120')
        self.assertFalse(r.free.complete)
        self.assertEqual(r.rows[-1].capacity, 254)
        self.assertEqual(r.rows[-1].fragmented_addresses, 0)

    def test_maximum_input_records(self):
        r = capacity_overview('\n'.join(f'{IPv6Address(2*i)}/128' for i in range(5000)), '::/112')
        self.assertEqual(r.rows[-1].capacity, 65536-5000)
        with self.assertRaises(InputError):
            capacity_overview('\n'.join('::/128' for _ in range(5001)), '::/0')


class CapacityUiTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.InspectionUiTests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.InspectionUiTests.tearDownClass.__func__)
    setUp = fixtures.InspectionUiTests.setUp
    tearDown = fixtures.InspectionUiTests.tearDown

    def test_snapshot_parent_defaults_and_read_only_project(self):
        p = self.d.capacity
        self.assertEqual(p.input.text(), self.page.planning.parent_input.text())
        before = self.page.project_controller.snapshot()
        p.input.setText('::/126')
        self.assertTrue(p.run())
        self.assertEqual(p.result.rows[-1].capacity, 2)
        self.assertEqual(before, self.page.project_controller.snapshot())
        self.page.editor.setPlainText('::/0')
        self.assertTrue(p.run())
        self.assertEqual(p.result.rows[-1].capacity, 2)

    def test_error_and_edit_clear_outputs(self):
        p = self.d.capacity
        p.input.setText('::/126'); self.assertTrue(p.run())
        self.assertTrue(p.save_button.isEnabled())
        p.input.setText('bad')
        self.assertIsNone(p.result)
        self.assertEqual(p.report.toPlainText(), '')
        self.assertFalse(p.run())
        self.assertFalse(p.save_button.isEnabled())
        self.assertFalse(p.copy_button.isEnabled())

    def test_bilingual_reports_preserve_parent(self):
        p = self.d.capacity
        p.input.setText('::/126'); p.run()
        self.app.language_manager.apply('en_US', persist=False)
        self.assertIn('Free Capacity Overview', p.report.toPlainText())
        self.assertIn('/128 | 2 | 0', p.report.toPlainText())
        self.assertEqual(p.input.text(), '::/126')
        self.app.language_manager.apply('zh_CN', persist=False)
        self.assertIn('空闲容量总览', p.report.toPlainText())

    def test_copy_and_snapshot_guarded_save(self):
        p = self.d.capacity
        p.input.setText('::/126'); p.run()
        with patch.object(self.page.clipboard, 'copy_text') as copy:
            p.copy(); self.assertEqual(str(copy.call_args.args[0]), str(p.result.as_text()))
        with patch.object(self.page.output_controller, '_save') as save:
            p.save()
            name, report, guard = save.call_args.args
            self.assertEqual(name, 'IPv6_CapacityOverview.txt')
            self.assertTrue(guard())
            p.run(); self.assertFalse(guard())

    def test_minimum_size_all_languages_themes(self):
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QPoint
        p = self.d.capacity
        p.input.setText('::/0'); p.run()
        tabs = p.parentWidget().parentWidget()
        tabs.setCurrentWidget(p)
        for language in ('zh_CN', 'en_US'):
            self.app.language_manager.apply(language, persist=False)
            for theme in ('light', 'dark'):
                self.app.theme_manager.apply(theme, persist=False)
                self.d.resize(600, 460); self.d.show(); QApplication.processEvents()
                for widget in (p.input, p.run_button, p.save_button, p.report):
                    bottom = widget.mapTo(self.d, QPoint(widget.width()-1, widget.height()-1))
                    self.assertTrue(self.d.rect().contains(bottom), (language, theme, widget))

    def test_real_save_and_changed_parent_during_dialog(self):
        p = self.d.capacity
        p.input.setText('::/126'); p.run()
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName', return_value=(str(self.path), '')):
            p.save()
        self.assertIn('空闲地址数：2', self.path.read_text(encoding='utf-8'))
        self.path.unlink()
        def changed(*args, **kwargs):
            p.input.setText('::/0')
            return str(self.path), ''
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName', side_effect=changed):
            p.save()
        self.assertFalse(self.path.exists())

    def test_external_writer_conflict_preserves_file(self):
        import os
        from ui.standard_dialogs import QMessageBox
        p = self.d.capacity
        p.input.setText('::/126'); p.run()
        self.path.write_text('original', encoding='utf-8'); before = self.path.stat()
        def changed(*args, **kwargs):
            self.path.write_text('external', encoding='utf-8')
            os.utime(self.path, ns=(before.st_atime_ns, before.st_mtime_ns+2_000_000_000))
            return QMessageBox.StandardButton.Yes
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName', return_value=(str(self.path), '')), patch('ui.list_output_controller.QMessageBox.question', side_effect=changed):
            p.save()
        self.assertEqual(self.path.read_text(encoding='utf-8'), 'external')
