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

"""离线帮助、许可文本与运行版本信息；与关于窗口布局分开维护。"""
from PyQt6.QtCore import PYQT_VERSION_STR, qVersion
from PyQt6.sip import SIP_VERSION_STR
from importlib.metadata import version, PackageNotFoundError
from app_info import APP_NAME, APP_VERSION, resource_path

# Only bundled, explicitly listed documents can be opened by the about window.
LICENSE_DOCUMENTS = (
    ('第三方组件概览', 'THIRD_PARTY_NOTICES.md'),
    ('项目许可 · GPL-3.0-or-later', 'LICENSE'),
    ('项目版权与许可范围', 'NOTICE'),
    ('PyQt6 · GPL v3 原文', 'docs/licenses/PyQt6_GPLv3.txt'),
    ('Qt 6 · LGPL v3 原文', 'docs/licenses/Qt_LGPLv3.txt'),
    ('Qt 中文控件 · 来源与许可', 'docs/licenses/Qt_Translations_NOTICE.txt'),
    ('PyQt6-sip · 许可原文', 'docs/licenses/PyQt6_sip_LICENSE.txt'),
)
HELP_DOCUMENT = 'docs/about/USAGE.md'
LEGAL_DOCUMENT = 'docs/about/LEGAL.md'
DOCUMENT_PATHS = frozenset(path for _, path in LICENSE_DOCUMENTS) | {HELP_DOCUMENT, LEGAL_DOCUMENT}


def read_document(relative):
    if relative not in DOCUMENT_PATHS:
        raise ValueError('未知的关于文档。')
    try:
        text = resource_path(relative).read_text(encoding='utf-8')
        if not text.strip():
            raise ValueError('empty document')
        return text
    except (OSError, UnicodeError, ValueError) as exc:
        raise RuntimeError('无法读取内置文档：'+relative+'。请重新下载完整的程序或源码。') from exc


def program_information():
    try:
        sip_distribution = version('PyQt6-sip')
    except PackageNotFoundError:
        sip_distribution = f'发行元数据不可用（SIP 引擎 {SIP_VERSION_STR}）'
    return f'''**IPv6SubnetCalculator · V{APP_VERSION}**

面向 Windows 的离线 IPv6 子网计算与地址分析工具。

- **主要功能**：网络范围与容量计算、分页定位、方案保存与恢复、地址格式转换、双网段关系分析、已有 CIDR 清单检查、空闲空间、等价 CIDR 整理、TXT／Excel 导出。
- **项目许可**：GNU GPL v3.0 或任何后续版本（GPL-3.0-or-later）。
- **版权**：Copyright © 2026 IPv6SubnetCalculator contributors。
- **致谢**：感谢 PyQt6、Qt 6 和 SIP 上游项目及其贡献者。

### 当前运行组件

| 组件 | 实际运行版本 |
|---|---|
| PyQt6 | {PYQT_VERSION_STR} |
| Qt | {qVersion()} |
| PyQt6-sip | {sip_distribution} |

许可原文、使用说明与法律责任信息可在本窗口离线查看。
本程序提供数学计算与辅助规划信息，不会修改系统网络配置，也不验证地址的实际可达性。
'''
