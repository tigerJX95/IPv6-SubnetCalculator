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

"""Versioned planning inputs; derived results are deliberately recalculated."""
from dataclasses import dataclass
from core.localized_text import text as tx
from core.ipv6_core import InputError
from core.subnet_list import validate_list_text

PROJECT_FORMAT = 'IPv6SubnetCalculator.planning'
PROJECT_VERSION = 1

@dataclass(frozen=True)
class PlanningProject:
    text: str
    parent: str
    prefix: str
    count: str
    tab: int = 2


def project_from_payload(payload):
    keys = {'format', 'version', 'text', 'parent', 'prefix', 'count', 'tab'}
    if not isinstance(payload, dict) or set(payload) != keys or payload.get('format') != PROJECT_FORMAT:
        raise InputError(tx('这不是有效的 IPv6 规划项目。'))
    if type(payload['version']) is not int or payload['version'] != PROJECT_VERSION:
        raise InputError(tx('规划项目格式版本不支持。'))
    for key, limit in (('text', 1048576), ('parent', 200), ('prefix', 5), ('count', 6)):
        value = payload[key]
        if not isinstance(value, str) or len(value) > limit or '\x00' in value:
            raise InputError(tx('规划项目包含无效字段。'))
        try:
            value.encode('utf-8')
        except UnicodeError as exc:
            raise InputError(tx('规划项目包含无效字段。')) from exc
    validate_list_text(payload['text'], allow_empty=True)
    if type(payload['tab']) is not int or payload['tab'] not in range(5):
        raise InputError(tx('规划项目包含无效字段。'))
    # Preserve unfinished or invalid inputs so a draft can be repaired after loading.
    return PlanningProject(*(payload[key] for key in ('text', 'parent', 'prefix', 'count', 'tab')))


def project_to_payload(project):
    payload = dict(format=PROJECT_FORMAT, version=PROJECT_VERSION,
        text=project.text, parent=project.parent, prefix=project.prefix,
        count=project.count, tab=project.tab)
    project_from_payload(payload)
    return payload
