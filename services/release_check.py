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

"""可由源码和打包程序调用的隔离检查，不更改用户偏好或剪贴板。"""
import json
import os
import platform
import sys
import tempfile
from pathlib import Path
from time import monotonic
from ipaddress import IPv6Address
from xml.etree import ElementTree
from zipfile import ZipFile
from PyQt6.QtCore import QObject, QTimer, QSettings, qVersion, PYQT_VERSION_STR
from PyQt6.QtGui import QIcon
from app_info import APP_VERSION, DEFAULT_NETWORK, resource_path
from core.ipv6_core import calculate
from services.export_service import ExportService
from services.build_info import current_build_info


def environment_info():
    return dict(app_version=APP_VERSION, source_sha256=current_build_info()['source_sha256'], python=platform.python_version(),
                os=platform.system(), platform=platform.platform(),
                architecture=platform.machine(), qt=qVersion(), pyqt=PYQT_VERSION_STR,
                frozen=bool(getattr(sys, 'frozen', False)))


def write_report(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.ipv6-check-', suffix='.json', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class ReleaseCheck(QObject):
    def __init__(self, application, window, directory, report_path):
        super().__init__(application)
        self.application, self.window = application, window
        self.directory, self.report_path = Path(directory), Path(report_path)
        self.started = monotonic()
        self.last_beat = self.started
        self.heartbeat_gaps = []
        self.export_gaps = {'txt': [], 'xlsx': []}
        self.checks = []
        self.error = None
        self.finished = False
        self.cycle = 0
        self.phase = None
        self.service = ExportService(self)
        self.service.completed.connect(self.completed_export)
        self.heartbeat = QTimer(self)
        self.heartbeat.setInterval(10)
        self.heartbeat.timeout.connect(self.beat)
        self.timeout = QTimer(self)
        self.timeout.setSingleShot(True)
        self.timeout.timeout.connect(lambda: self.fail('检查超过 45 秒，已请求取消导出。'))

    def beat(self):
        now = monotonic()
        self.heartbeat_gaps.append((now-self.last_beat)*1000)
        if self.service.busy and self.phase in self.export_gaps:
            self.export_gaps[self.phase].append((now-self.last_beat)*1000)
        self.last_beat = now

    def schedule(self, function):
        def guarded():
            if self.finished or self.error:
                return
            try:
                function()
            except Exception as exc:
                self.fail(str(exc) or type(exc).__name__)
        QTimer.singleShot(0, guarded)

    def require(self, condition, message):
        if not condition:
            raise AssertionError(message)

    def start(self):
        self.heartbeat.start()
        self.timeout.start(45000)
        self.schedule(self.check_resources_and_boundaries)

    def check_resources_and_boundaries(self):
        from ui.widgets import IconButton
        self.window.show()
        self.require(self.window.tabs.count() == 3, '工具标签页缺失')
        self.window.calculate()
        page = self.window.results_page
        self.require(page.model.rowCount() == 100, '默认结果行数不正确')
        self.require(self.window.result.subnet_count == 65536, '默认子网总数不正确')
        for button in self.window.findChildren(IconButton):
            for state, icon in button._icons.items():
                self.require(not icon.isNull(), f'缺少图标：{button.objectName()}/{state}')
        for theme in ('dark', 'light'):
            self.application.theme_manager.apply(theme, persist=False)
            arrow = QIcon(str(resource_path(f'assets/chevron_{theme}.svg')))
            self.require(not arrow.pixmap(12, 8).isNull(), f'无法加载 {theme} 下拉箭头')
        for filename in ('LICENSE', 'NOTICE', 'THIRD_PARTY_NOTICES.md',
                         'docs/licenses/PyQt6_GPLv3.txt', 'docs/licenses/Qt_LGPLv3.txt',
                         'docs/licenses/PyQt6_sip_LICENSE.txt'):
            self.require(resource_path(filename).is_file(), '缺少许可资源：'+filename)
        calculation = self.window.calculation_page
        self.require(calculation.copy_summary_button.isEnabled(), '摘要复制入口不可用')
        self.require('目标子网前缀：/64' in calculation.summary_text(), '摘要缺少目标前缀')
        self.require('可划分子网数：65,536' in calculation.summary_text(), '摘要子网总数不正确')
        snapshot = calculation.summary_text()
        calculation.target_input.setText('128')
        self.require(calculation.summary_text() == snapshot, '摘要混入尚未计算的输入')
        self.checks.append('calculation_summary_snapshot')
        tools = self.window.address_tools_page
        self.require(not tools.copy_formats_button.isEnabled(), '未转换时应禁用格式复制')
        tools.address_input.setText('::ffff:192.0.2.1')
        tools.convert()
        self.require(tools.formats.expanded == '0000:0000:0000:0000:0000:ffff:c000:0201', '映射地址展开不完整')
        self.require(len(tools.formats.binary) == 128, '二进制位数不正确')
        tools.network_a_input.setText('::/0')
        tools.network_b_input.setText('::/0')
        tools.analyze()
        self.require(tools.relation.overlap_count == 2**128, '最大空间重叠数量不正确')
        tools.network_a_input.setText('::/127')
        tools.network_b_input.setText('::2/128')
        tools.analyze()
        self.require(tools.relation.kind == 'adjacent', '不同前缀相邻判断不正确')
        tools.network_b_input.setText('bad')
        tools.analyze()
        self.require(not tools.copy_relation_button.isEnabled(), '非法分析后未禁用复制')
        tools.network_a_input.setText(DEFAULT_NETWORK)
        tools.network_b_input.setText('2026:1015:abcd::/64')
        tools.analyze()
        self.require(tools.relation.kind == 'a_contains_b', '包含方向不正确')
        self.checks.append('address_formats_and_network_relations')
        self.checks.append('default_calculation_and_resources')
        self.window.calculation_page.network_input.setText('::/0')
        self.window.calculation_page.target_input.setText('128')
        self.window.calculate()
        page.show_page(page.total_pages)
        self.require(page.model.records[-1] == (2**128, 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128'),
                     '最大 IPv6 结果末页不正确')
        self.require(page.model.rowCount() <= 200, '表格超出单页记录上限')
        self.require(f'可划分子网数：{2**128:,}' in calculation.summary_text(), '摘要最大整数丢失精度')
        self.checks.append('maximum_ipv6_space_and_last_page')
        self.window.calculation_page.network_input.setText(DEFAULT_NETWORK)
        self.window.calculation_page.target_input.setText('64')
        self.window.calculate()
        self.schedule(self.navigation_cycle)

    def navigation_cycle(self):
        page = self.window.results_page
        step = self.cycle
        if step >= 100:
            self.checks.append('100_navigation_selection_cycles')
            self.start_export('txt')
            return
        page.page_size_combo.setCurrentIndex(step % 4)
        first = 1 + step*311
        page.locator_mode_combo.setCurrentIndex(3)
        page.locator_input.setText(f'{first}-{first+250}')
        page.locate()
        self.require(page.selected_indices() == [first], '定位选择状态不正确')
        self.window.tabs.setCurrentIndex(0)
        self.window.tabs.setCurrentIndex(2)
        self.require(self.window.address_tools_page.relation.kind == 'a_contains_b', '工具结果状态丢失')
        self.window.tabs.setCurrentIndex(1)
        self.require(page.selected_indices() == [first], '切换标签后选择丢失')
        if step % 10 == 0:
            self.application.theme_manager.apply('dark' if step % 20 else 'light', persist=False)
            self.window.resize(900 if step % 20 else 1080, 620 if step % 20 else 800)
        page.clear_selection()
        self.require(page.locator_range == (first, first+250), '清除选择误清除了定位范围')
        page.show_page(page.total_pages)
        self.require(page.model.records[-1][0] == 65536, '末页数据不正确')
        self.cycle += 1
        self.schedule(self.navigation_cycle)

    def start_export(self, fmt):
        self.phase = fmt
        self.phase_started = monotonic()
        self.last_beat = self.phase_started
        filename = '子网结果.'+fmt if fmt != 'cancel' else '取消保留.txt'
        self.current_path = self.directory/filename
        result = calculate('::/0', '128', preview_limit=0)
        if fmt == 'cancel':
            self.current_path.write_bytes(b'original')
            self.service.start(self.current_path, result, 'txt', 1, result.subnet_count)
            QTimer.singleShot(0, self.service.cancel)
        else:
            self.service.start(self.current_path, result, fmt, 1, 100000 if fmt == 'txt' else 20000)

    def completed_export(self, outcome):
        if self.error:
            self.finish()
            return
        try:
            kind, payload = outcome
            if self.phase == 'cancel':
                self.require(kind == 'cancel', '取消导出未返回取消状态')
                self.require(self.current_path.read_bytes() == b'original', '取消导出覆盖了原文件')
                self.require(not list(self.directory.glob('.ipv6-export-*')), '取消后遗留临时文件')
                self.checks.append('cancel_preserves_original_and_cleans_temporary_file')
                self.finish()
                return
            self.require(kind == 'ok', '后台导出失败：'+str(payload))
            if self.phase == 'txt':
                with self.current_path.open(encoding='utf-8') as stream:
                    rows = sum(1 for _ in stream)
                self.require(rows == 100000, 'TXT 行数不正确')
            else:
                with ZipFile(self.current_path) as archive:
                    self.require(archive.testzip() is None, 'XLSX 压缩包损坏')
                    with archive.open('xl/worksheets/sheet1.xml') as stream:
                        rows = 0
                        for _, element in ElementTree.iterparse(stream, events=('end',)):
                            if element.tag.endswith('}row'):
                                rows += 1
                                element.clear()
                    self.require(rows == 20001, 'XLSX 行数不正确')
            self.checks.append(f'background_{self.phase}_export_with_unicode_path')
            self.schedule(lambda: self.start_export('xlsx' if self.phase == 'txt' else 'cancel'))
        except Exception as exc:
            self.fail(str(exc) or type(exc).__name__)

    def fail(self, message):
        if self.finished:
            return
        self.error = message
        if self.service.busy:
            self.service.cancel()
        else:
            self.finish()

    def finish(self):
        if self.finished or self.service.busy:
            return
        self.finished = True
        self.timeout.stop()
        self.heartbeat.stop()
        self.window.close()
        self.window.deleteLater()
        payload = dict(environment=environment_info(), status='failed' if self.error else 'passed',
                       checks=self.checks, navigation_cycles=self.cycle,
                       elapsed_seconds=round(monotonic()-self.started, 4),
                       event_loop=dict(ticks=len(self.heartbeat_gaps),
                           maximum_observed_gap_ms=round(max(self.heartbeat_gaps, default=0), 3)),
                       background_event_loop={fmt: dict(ticks=len(gaps),
                           maximum_observed_gap_ms=round(max(gaps, default=0), 3))
                           for fmt, gaps in self.export_gaps.items()})
        if self.error:
            payload['error'] = self.error
        try:
            write_report(self.report_path, payload)
        except OSError:
            self.application.exit(2)
            return
        self.application.exit(1 if self.error else 0)


def run_self_check(report_path):
    from app import create_application
    from ui.main_window import MainWindow
    report_path = Path(report_path).resolve()
    try:
        write_report(report_path, dict(status='running', environment=environment_info()))
    except (OSError, ValueError):
        return 2
    with tempfile.TemporaryDirectory(prefix='IPv6校验-') as directory:
        settings = QSettings(str(Path(directory)/'preferences.ini'), QSettings.Format.IniFormat)
        application = create_application([], settings=settings)
        application.setQuitOnLastWindowClosed(False)
        checker = ReleaseCheck(application, MainWindow(), directory, report_path)
        checker.start()
        return application.exec()
