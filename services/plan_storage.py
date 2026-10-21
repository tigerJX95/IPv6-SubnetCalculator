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

"""UTF-8 JSON 方案读写；先校验再写入，成功后原子替换目标文件。"""
from core.localized_text import text as tx, join_text as jt
import json
import os
import tempfile
from core.file_commit import capture_file,commit_file,SaveConflict
from pathlib import Path
from core.ipv6_core import InputError
from core.calculation_plan import plan_from_payload, plan_to_payload

MAX_PLAN_BYTES = 64 * 1024


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError(tx('方案 JSON 包含重复字段：')+key)
        result[key] = value
    return result


def _invalid_constant(value):
    raise InputError(tx('方案 JSON 包含无效数值：')+value)


def _load_document(path, parser, maximum, limit_message):
    with Path(path).open('rb') as stream:
        data = stream.read(maximum+1)
    if len(data) > maximum:
        raise InputError(limit_message)
    try:
        payload = json.loads(data.decode('utf-8-sig'), object_pairs_hook=_unique_object,
                             parse_constant=_invalid_constant)
        return parser(payload)
    except (UnicodeError, ValueError, RecursionError) as exc:
        if isinstance(exc, InputError):
            raise
        raise InputError(tx('方案文件不是有效的 UTF-8 JSON。')) from exc


def _save_document(path, payload, maximum, *, expected=None):
    data = (json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')
    if len(data) > maximum:
        raise InputError(tx('方案文件内容过大，请缩短名称或备注。'))
    path = Path(path)
    expected=expected if expected is not None else capture_file(path)
    fd, temporary = tempfile.mkstemp(prefix='.ipv6-plan-', suffix='.json', dir=str(expected.path.parent))
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        commit_file(temporary,path,expected)
    except SaveConflict:
        temporary=None
        raise
    finally:
        if temporary is not None and os.path.exists(temporary):
            os.unlink(temporary)


def load_plan(path):
    return _load_document(path, plan_from_payload, MAX_PLAN_BYTES,
        tx('方案文件超过 64 KiB，请选择计算方案 JSON，而不是子网列表。'))


def save_plan(path, plan, *, expected=None):
    return _save_document(path, plan_to_payload(plan), MAX_PLAN_BYTES, expected=expected)
