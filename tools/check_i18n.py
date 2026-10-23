# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Check TS/QM consistency and literal translation coverage without a compiler."""
import argparse
import ast
import json
from pathlib import Path
import re
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.translation_catalog import audit_catalog

TRANSLATABLE = re.compile(r'[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]')


def source_messages(path):
    tree = ast.parse(Path(path).read_text(encoding='utf-8'), filename=str(path))
    aliases = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == 'core.localized_text':
            aliases.update(item.asname or item.name for item in node.names if item.name == 'text')
    found, errors = [], []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        if isinstance(node.func, ast.Name) and node.func.id in aliases:
            source = node.args[0]
            if not isinstance(source, ast.Constant) or not isinstance(source.value, str):
                errors.append(f'{path}:{node.lineno}: translation template must be a literal')
            elif TRANSLATABLE.search(source.value):
                found.append(('App', source.value, node.lineno))
        elif isinstance(node.func, ast.Attribute) and node.func.attr == 'translate' and len(node.args) >= 2:
            context, source = node.args[:2]
            if all(isinstance(a, ast.Constant) and isinstance(a.value, str) for a in (context, source)):
                # Native Qt controls use qtbase_zh_CN.qm, not the application catalog.
                if context.value != 'QLineEdit':
                    found.append((context.value, source.value, node.lineno))
        display_call = ((isinstance(node.func, ast.Name) and node.func.id in
                         {'QLabel', 'QPushButton', 'QGroupBox', 'QCheckBox', 'QRadioButton'}) or
                        (isinstance(node.func, ast.Attribute) and node.func.attr in
                         {'setText', 'setTitle', 'setWindowTitle', 'setToolTip', 'setPlaceholderText',
                          'setAccessibleName', 'setAccessibleDescription'}))
        if display_call and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            value = node.args[0].value
            if TRANSLATABLE.search(value) and value != '简体中文':
                errors.append(f'{path}:{node.lineno}: display literal is not wrapped in text(): {value!r}')
    return found, errors


def check_project(root=ROOT, *, verify_record=True):
    root = Path(root)
    result = audit_catalog(root, verify_record=verify_record)
    errors = result['errors']
    paths = [p for name in ('core', 'ui', 'services') for p in sorted((root/name).rglob('*.py'))]
    paths += [root/name for name in ('app.py', 'main.py', 'app_info.py') if (root/name).is_file()]
    count = 0
    for path in paths:
        try:
            messages, issues = source_messages(path)
        except (OSError, UnicodeError, SyntaxError) as exc:
            errors.append(f'Cannot inspect source {path}: {exc}')
            continue
        errors.extend(issues)
        for context, source, line in messages:
            count += 1
            if (context, source) not in result['messages']:
                errors.append(f'{path.relative_to(root)}:{line}: missing TS message {(context, source)!r}')
    return dict(status='failed' if errors else 'passed', catalog_messages=len(result['messages']),
                source_messages=count, source_files=len(paths), errors=errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = check_project(args.root)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text+'\n', encoding='utf-8')
    print(text)
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
