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


def load_plan(path):
    with Path(path).open('rb') as stream:
        data = stream.read(MAX_PLAN_BYTES+1)
    if len(data) > MAX_PLAN_BYTES:
        raise InputError(tx('方案文件超过 64 KiB，请选择计算方案 JSON，而不是子网列表。'))
    try:
        payload = json.loads(data.decode('utf-8-sig'), object_pairs_hook=_unique_object,
                             parse_constant=_invalid_constant)
        return plan_from_payload(payload)
    except (UnicodeError, ValueError, RecursionError) as exc:
        if isinstance(exc, InputError):
            raise
        raise InputError(tx('方案文件不是有效的 UTF-8 JSON。')) from exc


def save_plan(path, plan):
    data = (json.dumps(plan_to_payload(plan), ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')
    if len(data) > MAX_PLAN_BYTES:
        raise InputError(tx('方案文件内容过大，请缩短名称或备注。'))
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix='.ipv6-plan-', suffix='.json', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
