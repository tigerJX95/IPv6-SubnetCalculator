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

"""运行源码与资源的构建指纹，不包含用户配置、报告或测试输出。"""
from core.localized_text import text as tx, join_text as jt
import hashlib
import json
import sys
from pathlib import Path
from app_info import APP_VERSION, resource_path


def source_digest(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parents[1]
    names = {'main.py', 'app.py', 'app_info.py', 'app.ico', 'requirements.txt',
             'build.cmd', 'LICENSE', 'NOTICE', 'THIRD_PARTY_NOTICES.md'}
    for folder, pattern in (('core', '*.py'), ('ui', '*.py'), ('services', '*.py'),
                            ('assets', '*'), ('docs/licenses', '*'), ('docs/about', '*')):
        names.update(p.relative_to(root).as_posix() for p in (root/folder).rglob(pattern) if p.is_file())
    digest = hashlib.sha256()
    for name in sorted(names):
        digest.update(name.encode('utf-8')+b'\0')
        digest.update((root/name).read_bytes())
        digest.update(b'\0')
    return digest.hexdigest()


def current_build_info():
    if getattr(sys, 'frozen', False):
        payload = json.loads(resource_path('build_manifest.json').read_text(encoding='utf-8'))
        if payload.get('app_version') != APP_VERSION or not isinstance(payload.get('source_sha256'), str):
            raise ValueError(tx('构建清单的版本或内容无效，请使用 build.cmd 重新构建。'))
        return payload
    return dict(app_version=APP_VERSION, source_sha256=source_digest())
