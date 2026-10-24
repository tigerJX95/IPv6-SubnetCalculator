# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Reject stale/broken translations and keep localized failures usable."""
import errno
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from PyQt6.QtCore import QSettings, QLocale
from app import create_application
from core.localized_text import text, render, format_signature, exception_text, Text
from core.ipv6_core import InputError
from services.error_messages import describe_error
from services.language_service import display
from services.translation_catalog import audit_catalog, pair_record, TS_PATH, QM_PATH, RECORD_PATH
from tools.check_i18n import check_project, source_messages
from tools.update_translations import update

ROOT = Path(__file__).resolve().parents[1]


class CatalogAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preferences = tempfile.TemporaryDirectory()
        cls.app = create_application([], QSettings(str(Path(cls.preferences.name)/'prefs.ini'), QSettings.Format.IniFormat))
        cls.app.setQuitOnLastWindowClosed(False)

    @classmethod
    def tearDownClass(cls):
        cls.app.language_manager.apply('zh_CN', persist=False)
        cls.preferences.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root/'assets/i18n').mkdir(parents=True)
        for path in (TS_PATH, QM_PATH, RECORD_PATH):
            shutil.copyfile(ROOT/path, self.root/path)
        self.tree = ET.parse(self.root/TS_PATH)
        self.message = next(c for c in self.tree.getroot().findall('context') if c.findtext('name') == 'App').find('message')

    def tearDown(self):
        self.temp.cleanup()

    def write_ts(self):
        self.tree.write(self.root/TS_PATH, encoding='utf-8', xml_declaration=True)

    def errors(self, **kwargs):
        return '\n'.join(audit_catalog(self.root, **kwargs)['errors'])

    def test_complete_project_catalog_sources_and_record_pass(self):
        result = check_project(ROOT)
        self.assertEqual(result['errors'], [])
        self.assertGreater(result['catalog_messages'], 700)
        self.assertGreater(result['source_messages'], 800)

    def test_changed_ts_without_recompile_rejected(self):
        self.message.find('translation').text = 'Changed translation'
        self.write_ts()
        errors = self.errors()
        self.assertIn('TS/QM translation differs', errors)
        self.assertIn('generation record is stale', errors)

    def test_windows_crlf_checkout_preserves_catalog_record(self):
        expected = pair_record(self.root)
        path = self.root/TS_PATH
        path.write_bytes(path.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
        self.assertEqual(pair_record(self.root), expected)
        self.assertEqual(audit_catalog(self.root)['errors'], [])

    def test_lone_cr_text_newlines_preserve_catalog_record(self):
        expected = pair_record(self.root)
        path = self.root/TS_PATH
        path.write_bytes(path.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r'))
        self.assertEqual(pair_record(self.root), expected)
        self.assertEqual(audit_catalog(self.root)['errors'], [])

    def test_qm_binary_changes_still_invalidate_record(self):
        expected = pair_record(self.root)
        path = self.root/QM_PATH
        path.write_bytes(path.read_bytes()+b'\r\n')
        self.assertNotEqual(pair_record(self.root)['qm_sha256'], expected['qm_sha256'])
        self.assertIn('generation record is stale', self.errors())

    def test_unfinished_translation_rejected_even_when_nonempty(self):
        self.message.find('translation').set('type', 'unfinished')
        self.write_ts()
        self.assertIn('Unfinished', self.errors())

    def test_blank_translation_rejected(self):
        self.message.find('translation').text = '   '
        self.write_ts()
        self.assertIn('Empty source or translation', self.errors())

    def test_duplicate_context_source_rejected(self):
        context = self.tree.getroot().find('context')
        context.append(ET.fromstring(ET.tostring(self.message)))
        self.write_ts()
        self.assertIn('Duplicate TS message', self.errors())

    def test_format_fields_specifiers_and_conversions_checked(self):
        message = next(m for m in self.tree.getroot().iter('message') if '{0:,}' in (m.findtext('source') or ''))
        old = message.find('translation').text
        for bad in (old.replace('{0:,}', '{0}'), old.replace('{0:,}', '{1:,}'), old+'{other}', old+'{'):
            message.find('translation').text = bad; self.write_ts()
            self.assertRegex(self.errors(), 'Format fields/specifiers differ|Invalid format syntax')

    def test_wrong_context_rejected_by_qm_lookup(self):
        self.tree.getroot().find('context/name').text = 'WrongAppContext'
        self.write_ts()
        self.assertIn('TS/QM translation differs', self.errors())

    def test_corrupt_or_missing_qm_reported(self):
        (self.root/QM_PATH).write_bytes(b'not a QM')
        self.assertIn('Cannot load QM', self.errors())
        (self.root/QM_PATH).unlink()
        self.assertIn('Cannot load QM', self.errors())

    def test_missing_or_invalid_ts_reported_without_traceback(self):
        (self.root/TS_PATH).write_text('<broken>')
        self.assertIn('Cannot read TS catalog', self.errors())
        (self.root/TS_PATH).unlink()
        self.assertIn('Cannot read TS catalog', self.errors())

    def test_removed_ts_message_still_requires_regeneration(self):
        self.tree.getroot().find('context').remove(self.message)
        self.write_ts()
        self.assertIn('generation record is stale', self.errors())

    def test_missing_or_invalid_generation_record_fails(self):
        (self.root/RECORD_PATH).write_text('{}')
        self.assertIn('generation record is stale', self.errors())
        (self.root/RECORD_PATH).unlink()
        self.assertIn('Cannot read TS/QM generation record', self.errors())

    def test_source_alias_missing_from_catalog_detected(self):
        path = self.root/'ui'; path.mkdir()
        (path/'new.py').write_text("from core.localized_text import text as localized\nlabel = localized('新增未翻译按钮')\n")
        self.assertIn('missing TS message', '\n'.join(check_project(self.root)['errors']))

    def test_unwrapped_display_literal_detected(self):
        path = self.root/'ui'; path.mkdir()
        (path/'new.py').write_text("label.setToolTip('遗漏翻译的说明')\n")
        self.assertIn('display literal is not wrapped', '\n'.join(check_project(self.root)['errors']))

    def test_dynamic_template_and_invalid_python_do_not_pass(self):
        path = self.root/'ui'; path.mkdir(); file = path/'new.py'
        file.write_text("from core.localized_text import text as tx\nvalue = tx(name)\n")
        self.assertIn('template must be a literal', '\n'.join(check_project(self.root)['errors']))
        file.write_text('this is not valid python !!!')
        self.assertIn('Cannot inspect source', '\n'.join(check_project(self.root)['errors']))

    def test_user_data_comments_and_native_qt_context_not_flagged(self):
        path = self.root/'data.py'
        path.write_text("# 中文注释\nraw = '用户备注'\nQCoreApplication.translate('QLineEdit', 'Select All')\n")
        self.assertEqual(source_messages(path), ([], []))

    def test_audit_does_not_change_installed_language(self):
        self.app.language_manager.apply('en_US', persist=False)
        before = QLocale().name(), display(text('保存'))
        audit_catalog(self.root)
        self.assertEqual((QLocale().name(), display(text('保存'))), before)
        self.app.language_manager.apply('zh_CN', persist=False)

    def test_cli_returns_failure_and_structured_report_for_broken_catalog(self):
        (self.root/QM_PATH).write_bytes(b'broken')
        report = self.root/'report.json'
        done = subprocess.run([sys.executable, str(ROOT/'tools/check_i18n.py'), '--root', str(self.root), '--report', str(report)], capture_output=True, timeout=20)
        self.assertEqual(done.returncode, 1)
        self.assertEqual(json.loads(report.read_text())['status'], 'failed')
        self.assertNotIn(b'Traceback', done.stderr)

    def test_failed_compilation_preserves_shipped_qm_and_record(self):
        before = [(self.root/path).read_bytes() for path in (QM_PATH, RECORD_PATH)]
        for folder in ('core', 'ui', 'services'): (self.root/folder).mkdir()
        for name in ('app.py', 'main.py', 'app_info.py'): (self.root/name).write_text('')
        with patch('tools.update_translations.subprocess.run', side_effect=subprocess.CalledProcessError(1, ['lrelease'])):
            with self.assertRaises(subprocess.CalledProcessError): update(self.root, 'lrelease')
        self.assertEqual(before, [(self.root/path).read_bytes() for path in (QM_PATH, RECORD_PATH)])


class TranslationFailureTests(unittest.TestCase):
    def test_invalid_translated_fields_fall_back_to_canonical_message(self):
        value = text('地址数：{0:,}', 2**128)
        for bad in ('Count: {1:,}', 'Count: {name}', 'Count: {0.__class__}', 'Count: {', '', None):
            self.assertEqual(render(value, lambda source: bad), str(value))

    def test_field_reordering_and_user_braces_are_preserved(self):
        value = text('第 {0} 项：{1}', 5, '用户{input}')
        self.assertEqual(render(value, lambda source: '{1} (item {0})'), '用户{input} (item 5)')

    def test_changed_format_specification_or_conversion_falls_back(self):
        value = text('数量：{0:,}', 10000)
        for bad in ('Count: {0!r}', 'Count: {0:.1f}', 'Count: {0}'):
            self.assertEqual(render(value, lambda source: bad), str(value))

    def test_nested_format_fields_checked_and_escaped_braces_allowed(self):
        self.assertEqual(format_signature('{0:{1}}'), format_signature('{0:{1}}'))
        self.assertNotEqual(format_signature('{0:{1}}'), format_signature('{0:{2}}'))
        self.assertEqual(render(text('数量：{0}', 3), lambda source: '{{Count}}: {0}'), '{Count}: 3')

    def test_missing_translated_lines_fall_back_without_index_error(self):
        value = text('第一行\n第二行').line(1)
        self.assertEqual(render(value, lambda source: 'Single line'), '第二行')

    def test_nested_localized_exception_keeps_template_and_raw_path(self):
        error = InputError(text('文件：{0}', '用户{file}.txt'))
        templates = {'失败：{0}': 'Failed: {0}', '文件：{0}': 'File: {0}'}
        self.assertIs(exception_text(error), error.args[0])
        self.assertEqual(render(text('失败：{0}', error), lambda source: templates.get(source, source)), 'Failed: File: 用户{file}.txt')
        self.assertIsInstance(describe_error(error), Text)

    def test_os_error_preserves_filename_and_error_code(self):
        error = PermissionError(errno.EACCES, 'OS detail', '用户路径{file}.txt')
        result = describe_error(error)
        self.assertIn('用户路径{file}.txt', result)
        self.assertIn(str(errno.EACCES), result)

    def test_invalid_source_template_remains_a_programming_error(self):
        with self.assertRaises(IndexError): text('Invalid {1}', 2)

    def test_background_localized_error_can_render_after_language_change(self):
        from services.subnet_list_service import _ListThread
        worker = _ListThread('bad', task='free', parent_network='::/0')
        worker.run()
        self.assertEqual(worker.outcome[0], 'error')
        self.assertIsInstance(worker.outcome[1], Text)
        self.assertIn('规划要求', str(worker.outcome[1]))
