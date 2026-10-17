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

"""源码、性能和可选打包程序检查；报告明确区分自动检查和人工验收。"""
import argparse
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app_info import APP_VERSION
from tools.performance import measure_performance
from services.build_info import source_digest


def run(command, logfile, environment, timeout):
    with logfile.open('w', encoding='utf-8') as stream:
        completed = subprocess.run(command, cwd=ROOT, env=environment, stdout=stream,
            stderr=subprocess.STDOUT, text=True, timeout=timeout)
    return completed.returncode


def read_check(report, returncode, require_frozen, expected_digest):
    if not report.is_file():
        raise RuntimeError('Check did not create a report: '+report.name)
    payload = json.loads(report.read_text(encoding='utf-8'))
    if (returncode != 0 or payload.get('status') != 'passed'
            or payload.get('environment', {}).get('app_version') != APP_VERSION
            or payload.get('environment', {}).get('source_sha256') != expected_digest
            or payload.get('environment', {}).get('frozen') is not require_frozen):
        raise RuntimeError('Check failed or version/build type mismatch: '+report.name)
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-dir', type=Path, default=ROOT/'verification')
    parser.add_argument('--exe', type=Path, help='optional executable built from the same source version')
    args = parser.parse_args()
    output = args.report_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    if platform.system() != 'Windows' and not env.get('DISPLAY') and not env.get('WAYLAND_DISPLAY'):
        env.setdefault('QT_QPA_PLATFORM', 'offscreen')
    result = dict(app_version=APP_VERSION, os=platform.system(), python=platform.python_version(),
                  status='running', manual_windows_acceptance='pending', steps={})
    result['windows_automated_checks'] = 'not_run'
    started = time.monotonic()
    expected_digest = source_digest()
    result['source_sha256'] = expected_digest
    def save():
        (output/'summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    save()
    try:
        print('1/4 Running regression tests...', flush=True)
        code = run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], output/'tests.log', env, 240)
        log = (output/'tests.log').read_text(encoding='utf-8')
        match = re.search(r'Ran (\d+) tests?', log)
        result['steps']['regression'] = dict(status='passed' if code == 0 else 'failed',
                                             tests=int(match.group(1)) if match else None)
        if code:
            raise RuntimeError('Regression tests failed; see tests.log')
        save()
        print('2/4 Measuring calculation, pagination, export and memory...', flush=True)
        result['steps']['performance'] = dict(status='passed', metrics=measure_performance())
        save()
        print('3/4 Checking source application...', flush=True)
        report = output/'source.json'
        report.unlink(missing_ok=True)
        code = run([sys.executable, 'main.py', '--self-check', str(report)], output/'source.log', env, 90)
        result['steps']['source'] = read_check(report, code, False, expected_digest)
        save()
        print('4/4 Checking packaged application...' if args.exe else '4/4 Packaged application not supplied; skipped.', flush=True)
        if args.exe:
            executable = args.exe.resolve()
            if not executable.is_file():
                raise FileNotFoundError('Executable not found: '+str(executable))
            report = output/'executable.json'
            report.unlink(missing_ok=True)
            code = run([str(executable), '--self-check', str(report)], output/'executable.log', env, 90)
            packaged = read_check(report, code, True, expected_digest)
            if packaged['environment']['os'] != platform.system():
                raise RuntimeError('Executable OS does not match the verification host')
            result['steps']['executable'] = packaged
            if platform.system() == 'Windows':
                result['windows_automated_checks'] = 'passed'
        else:
            result['steps']['executable'] = dict(status='not_run')
        result['status'] = 'passed'
    except Exception as exc:
        result['status'] = 'failed'
        result['error'] = str(exc) or type(exc).__name__
    result['elapsed_seconds'] = round(time.monotonic()-started, 3)
    save()
    lines = [f'# IPv6SubnetCalculator V{APP_VERSION} Verification', '',
        f'- Overall checks: {result["status"]}',
        f'- Host: {result["os"]}; Python {result["python"]}',
        f'- Windows automated checks: {result["windows_automated_checks"]}',
        '- Manual Windows acceptance: pending (see docs/WINDOWS_ACCEPTANCE.md)',
        '', 'Timings describe this run and machine. Python allocation measurements exclude Qt/native memory.',
        'A passed automatic run does not replace DPI, file association, Excel and long-session manual checks.',
        '', 'Detailed metrics and environment: summary.json; source/executable details: source.json and executable.json.']
    if result.get('error'):
        lines += ['', 'Error: '+result['error']]
    (output/'SUMMARY.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('Result: '+result['status']+'; reports: '+str(output), flush=True)
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
