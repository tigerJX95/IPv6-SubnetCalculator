# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""CIDR output must be exact, bounded, reusable and snapshot protected."""
import random
from ipaddress import IPv6Address, IPv6Network, summarize_address_range
from unittest.mock import patch
from core.ipv6_core import InputError
from core.list_inspection import compare_coverage, coverage_cidrs, lookup_address
from core.subnet_list import analyze_subnet_list
from tests import test_list_inspection as fixtures
import unittest


class CidrOutputCoreTests(unittest.TestCase):
    def test_membership_normalizes_deduplicates_retains_containment(self):
        output = lookup_address('::1/126\n::/126\n::1/128\n::/0', '::1').cidr_output()
        self.assertEqual(output.as_text(), '::1/128\n::/126\n::/0')

    def test_empty_membership_and_coverage(self):
        self.assertEqual(lookup_address('', '::1').cidr_output().as_text(), '')
        self.assertEqual(compare_coverage('', '').cidr_output('added').as_text(), '')

    def test_categories_preserve_direction_and_roundtrip(self):
        result = compare_coverage('::/127', '::1/128\n::2/128')
        for category, text in [('added', '::2/128'), ('removed', '::/128'), ('common', '::1/128')]:
            output = result.cidr_output(category)
            self.assertEqual(output.as_text(), text)
            self.assertEqual(analyze_subnet_list(text).error_count, 0)

    def test_full_ipv6_space_is_single_cidr(self):
        self.assertEqual(compare_coverage('', '::/0').cidr_output('added').as_text(), '::/0')

    def test_unaligned_range_matches_standard_library(self):
        ranges = ((1, 2**128-2),)
        output = coverage_cidrs(ranges)
        self.assertEqual(output.cidrs, tuple(summarize_address_range(IPv6Address(1), IPv6Address(2**128-2))))
        self.assertEqual(sum(n.num_addresses for n in output.cidrs), 2**128-2)

    def test_limit_boundary_and_overflow_refuse_partial_output(self):
        for count in (5000, 5001):
            output = coverage_cidrs(tuple((2*i, 2*i) for i in range(count)))
            self.assertEqual(output.count, count)
            self.assertEqual(len(output.cidrs), min(count, 5000))
            if count == 5000:
                self.assertEqual(len(output.as_text().splitlines()), 5000)
            else:
                with self.assertRaises(InputError): output.as_text()

    def test_random_cidr_outputs_match_independent_address_sets(self):
        rng = random.Random(113)
        for _ in range(100):
            first, second = [{i for i in range(128) if rng.randrange(3)==0} for _ in range(2)]
            result = compare_coverage(*('\n'.join(f'{IPv6Address(i)}/128' for i in values) for values in (first, second)))
            for category, expected in [('added', second-first), ('removed', first-second), ('common', first&second)]:
                output = result.cidr_output(category)
                self.assertEqual({int(a) for net in output.cidrs for a in net}, expected)
                self.assertTrue(all(isinstance(n, IPv6Network) for n in output.cidrs))

    def test_unknown_category_rejected(self):
        with self.assertRaises(ValueError): compare_coverage('', '').cidr_output('baseline')


# Reuse fixture methods without inheriting the existing test cases a second time.
class CidrOutputUiTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.InspectionUiTests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.InspectionUiTests.tearDownClass.__func__)
    setUp = fixtures.InspectionUiTests.setUp
    tearDown = fixtures.InspectionUiTests.tearDown

    def test_selection_updates_cidrs_without_changing_inputs_or_report(self):
        self.p.input.setPlainText('::1/128\n::2/128'); self.p.run()
        report = self.p.report.toPlainText()
        for index, expected in [(0, '::2/128'), (1, '::/128'), (2, '::1/128')]:
            self.p.category.setCurrentIndex(index)
            self.assertEqual(self.p.cidr_output.as_text(), expected)
            self.assertEqual(self.p.report.toPlainText(), report)
        self.assertEqual(self.page.editor.toPlainText(), '# baseline\n::/127')

    def test_input_edit_clears_cidr_output(self):
        self.p.run(); self.p.category.setCurrentIndex(1)
        self.assertTrue(self.p.copy_cidrs_button.isEnabled())
        self.p.input.setPlainText('::/0')
        self.assertIsNone(self.p.cidr_output)
        self.assertFalse(self.p.copy_cidrs_button.isEnabled())
        self.assertFalse(self.p.save_cidrs_button.isEnabled())

    def test_empty_category_cannot_output(self):
        self.p.run()
        self.assertFalse(self.p.copy_cidrs_button.isEnabled())
        with patch.object(self.page.clipboard, 'copy_text') as copy:
            self.p.copy_cidrs()
        copy.assert_not_called()

    def test_save_pure_cidrs_can_be_reimported(self):
        self.p.run(); self.p.category.setCurrentIndex(1)
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName', return_value=(str(self.path), '')):
            self.p.save_cidrs()
        self.assertEqual(self.path.read_text(), '::/127\n')
        self.assertEqual(analyze_subnet_list(self.path.read_text()).error_count, 0)

    def test_category_changed_in_save_dialog_aborts_save(self):
        self.p.run(); self.p.category.setCurrentIndex(1)
        def change(*args, **kwargs):
            self.p.category.setCurrentIndex(0)
            return str(self.path), ''
        with patch('ui.list_output_controller.QFileDialog.getSaveFileName', side_effect=change): self.p.save_cidrs()
        self.assertFalse(self.path.exists())

    def test_lookup_copy_is_pure_normalized_cidrs(self):
        panel = self.d.lookup
        panel.input.setText('::1'); panel.run()
        with patch.object(self.page.clipboard, 'copy_text', return_value=True) as copy: panel.copy_cidrs()
        self.assertEqual(copy.call_args.args[0], '::/127')

    def test_english_keeps_category_result_and_translates_status(self):
        self.p.run(); self.p.category.setCurrentIndex(1)
        output = self.p.cidr_output
        self.app.language_manager.apply('en_US', persist=False)
        self.assertEqual(self.p.category.currentData(), 'removed')
        self.assertIs(self.p.cidr_output, output)
        self.assertIn('Removed coverage', self.p.category.currentText())
        self.assertIn('Complete CIDRs: 1', self.p.cidr_status.text())

    def test_overflow_disables_list_output_keeps_report_available(self):
        # A /0 baseline minus 5,000 isolated addresses creates over 5,000 CIDRs.
        self.p.source = '::/0'
        self.p.input.setPlainText('\n'.join(f'{IPv6Address(2*i+1)}/128' for i in range(5000)))
        self.p.run(); self.p.category.setCurrentIndex(1)
        self.assertGreater(self.p.cidr_output.count, 5000)
        self.assertFalse(self.p.copy_cidrs_button.isEnabled())
        self.assertFalse(self.p.save_cidrs_button.isEnabled())
        self.assertTrue(self.p.save_button.isEnabled())

    def test_visible_output_controls_fit_minimum_dialog_both_languages(self):
        from PyQt6.QtWidgets import QApplication
        from ui.localized_widgets import QTabWidget
        tabs = self.d.findChild(QTabWidget)
        self.d.resize(600, 460); self.d.show()
        for language in ('zh_CN', 'en_US'):
            self.app.language_manager.apply(language, persist=False)
            for index, panel in enumerate((self.d.lookup, self.d.comparison)):
                tabs.setCurrentIndex(index); QApplication.processEvents()
                for button in (panel.copy_cidrs_button, panel.save_cidrs_button):
                    self.assertTrue(self.d.rect().contains(button.mapTo(self.d, button.rect().bottomRight())))
