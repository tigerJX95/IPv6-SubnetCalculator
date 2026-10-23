# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Compile and validate English translations using an installed Qt Linguist tool."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.translation_catalog import TS_PATH, QM_PATH, RECORD_PATH, pair_record
from tools.check_i18n import check_project


def update(root, compiler):
    root = Path(root).resolve()
    # Stage compiler output; keep the existing shipped QM intact if validation fails.
    with tempfile.TemporaryDirectory(prefix='ipv6-i18n-') as directory:
        staged = Path(directory)
        for folder in ('core', 'ui', 'services'):
            shutil.copytree(root/folder, staged/folder, ignore=shutil.ignore_patterns('__pycache__'))
        for name in ('app.py', 'main.py', 'app_info.py'):
            shutil.copyfile(root/name, staged/name)
        (staged/TS_PATH).parent.mkdir(parents=True)
        shutil.copyfile(root/TS_PATH, staged/TS_PATH)
        subprocess.run([compiler, str(staged/TS_PATH), '-qm', str(staged/QM_PATH)], check=True)
        result = check_project(staged, verify_record=False)
        if result['errors']:
            raise ValueError('\n'.join(result['errors']))
        record = pair_record(staged)
        shutil.copyfile(staged/QM_PATH, root/QM_PATH)
        (root/RECORD_PATH).write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--lrelease', default=shutil.which('lrelease') or shutil.which('pyside6-lrelease'))
    args = parser.parse_args()
    if not args.lrelease:
        parser.error('Qt Linguist lrelease is required; pass --lrelease PATH. Existing QM files are unchanged.')
    try:
        result = update(args.root, args.lrelease)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print('Translation update failed: '+str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
