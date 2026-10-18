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

"""有版本的计算方案格式：只保存参数和视图，不枚举或信任派生结果。"""
from dataclasses import dataclass
from core.ipv6_core import InputError, calculate, validate_subnet_index

PLAN_FORMAT = 'IPv6SubnetCalculator.plan'
PLAN_VERSION = 1
PAGE_SIZES = (25, 50, 100, 200)


@dataclass(frozen=True)
class CalculationPlan:
    network: str
    target_prefix: int
    name: str = ''
    notes: str = ''
    page_size: int = 100
    page: int = 1
    locator_range: tuple | None = None
    selected_indices: tuple = ()
    tab: int = 0


def _text(value, limit, label):
    if not isinstance(value, str) or len(value) > limit or '\x00' in value:
        raise InputError(f'{label}须为不超过 {limit} 个字符的文本。')
    try:
        value.encode('utf-8')
    except UnicodeError as exc:
        raise InputError(f'{label}包含无效的 Unicode 字符。') from exc
    return value


def plan_from_payload(payload):
    if not isinstance(payload, dict) or payload.get('format') != PLAN_FORMAT:
        raise InputError('这不是有效的 IPv6 子网计算方案文件。')
    if type(payload.get('version')) is not int or payload['version'] != PLAN_VERSION:
        raise InputError('方案格式版本不支持，请使用对应版本的程序。')
    required = {'format', 'version', 'name', 'notes', 'network', 'target_prefix', 'view'}
    if set(payload) != required:
        raise InputError('方案字段缺失或包含不支持的字段。')
    name = _text(payload['name'], 80, '方案名称')
    notes = _text(payload['notes'], 2000, '方案备注')
    network = _text(payload['network'], 200, 'IPv6 网络')
    prefix = payload['target_prefix']
    if type(prefix) is not int:
        raise InputError('方案目标前缀须为 0～128 的整数。')
    result = calculate(network, str(prefix), preview_limit=0)
    view = payload['view']
    if not isinstance(view, dict) or set(view) != {'page_size', 'page', 'locator_range', 'selected_indices', 'tab'}:
        raise InputError('方案浏览位置字段无效。')
    size, tab = view['page_size'], view['tab']
    if type(size) is not int or size not in PAGE_SIZES or type(tab) is not int or tab not in (0, 1, 2):
        raise InputError('方案每页条数或页面编号无效。')
    def index(value, total):
        if not isinstance(value, str):
            raise InputError('方案页码及序号须使用十进制文本保存。')
        return validate_subnet_index(value, total)
    page = index(view['page'], (result.subnet_count+size-1)//size)
    span = view['locator_range']
    if span is not None:
        if not isinstance(span, list) or len(span) != 2:
            raise InputError('方案定位范围无效。')
        span = tuple(index(value, result.subnet_count) for value in span)
        if span[0] > span[1]:
            raise InputError('方案定位范围的结束序号不能小于起始序号。')
    selected = view['selected_indices']
    if not isinstance(selected, list) or len(selected) > size:
        raise InputError('方案选择数量超出当前页范围。')
    selected = tuple(index(value, result.subnet_count) for value in selected)
    if len(set(selected)) != len(selected) or any((value-1)//size+1 != page for value in selected):
        raise InputError('方案选择包含重复序号或不属于当前页的记录。')
    return CalculationPlan(str(result.network), result.target_prefix, name, notes, size, page,
                           span, tuple(sorted(selected)), tab)


def plan_to_payload(plan):
    payload = dict(format=PLAN_FORMAT, version=PLAN_VERSION, name=plan.name, notes=plan.notes,
        network=plan.network, target_prefix=plan.target_prefix,
        view=dict(page_size=plan.page_size, page=str(plan.page),
            locator_range=None if plan.locator_range is None else [str(value) for value in plan.locator_range],
            selected_indices=[str(value) for value in plan.selected_indices], tab=plan.tab))
    plan_from_payload(payload)
    return payload
