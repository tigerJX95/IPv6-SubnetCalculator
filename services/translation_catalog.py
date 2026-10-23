# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Validate the editable TS catalog against the shipped QM and generation record."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from PyQt6.QtCore import QCoreApplication, QTranslator
from core.localized_text import format_signature

TS_PATH = 'assets/i18n/app_en.ts'
QM_PATH = 'assets/i18n/app_en.qm'
RECORD_PATH = 'assets/i18n/app_en.catalog.json'


def pair_record(root):
    root = Path(root)
    return dict(schema=1, language='en_US',
                ts_sha256=hashlib.sha256((root/TS_PATH).read_bytes()).hexdigest(),
                qm_sha256=hashlib.sha256((root/QM_PATH).read_bytes()).hexdigest())


def audit_catalog(root, *, verify_record=True):
    """Read resources without installing a translator or changing the current locale."""
    root = Path(root)
    errors, messages = [], {}
    try:
        tree = ET.parse(root/TS_PATH).getroot()
    except (OSError, ET.ParseError, UnicodeError) as exc:
        return dict(errors=['Cannot read TS catalog: '+str(exc)], messages={})
    if tree.tag != 'TS' or tree.get('language') != 'en_US':
        errors.append('TS catalog must declare language en_US')
    for context in tree.findall('context'):
        name = context.findtext('name')
        if not name:
            errors.append('TS context name is empty')
        for message in context.findall('message'):
            translation = message.find('translation')
            if translation is not None and translation.get('type') in ('obsolete', 'vanished'):
                continue
            source = message.findtext('source') or ''
            key = (name, source)
            if key in messages:
                errors.append(f'Duplicate TS message: {key!r}')
            value = translation.text if translation is not None else None
            messages[key] = value
            if not source.strip() or not value or not value.strip():
                errors.append(f'Empty source or translation: {key!r}')
                continue
            if translation.get('type') == 'unfinished' or message.get('numerus') == 'yes':
                errors.append(f'Unfinished or unsupported plural message: {key!r}')
            try:
                if format_signature(source) != format_signature(value):
                    errors.append(f'Format fields/specifiers differ: {key!r}')
            except ValueError as exc:
                errors.append(f'Invalid format syntax: {key!r}: {exc}')
            if re.search(r'[\u4e00-\u9fff]', value.replace('简体中文', '')):
                errors.append(f'Untranslated Chinese text in English catalog: {key!r}')
    if not messages:
        errors.append('TS catalog has no active messages')
    # Keep an app alive for QTranslator.load; never install this audit translator.
    application = QCoreApplication.instance() or QCoreApplication([])
    translator = QTranslator()
    if not translator.load(str(root/QM_PATH)):
        errors.append('Cannot load QM catalog')
    else:
        for (context, source), value in messages.items():
            if value and translator.translate(context or '', source.encode('utf-8')) != value:
                errors.append(f'TS/QM translation differs: {(context, source)!r}')
    if verify_record:
        try:
            record = json.loads((root/RECORD_PATH).read_text(encoding='utf-8'))
            if record != pair_record(root):
                errors.append('TS/QM generation record is stale; run tools/update_translations.py')
        except (OSError, ValueError, UnicodeError) as exc:
            errors.append('Cannot read TS/QM generation record: '+str(exc))
    # Retain local ownership until all translation queries finish.
    del translator, application
    return dict(errors=errors, messages=messages)
