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
        self.require(self.window.tabs.count() == 4, '工具标签页缺失')
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
        from services.about_content import LICENSE_DOCUMENTS
        self.window.show_about()
        about = self.window.about_dialog
        self.require(about.tabs.count() == 4, '关于窗口页面缺失')
        self.require(APP_VERSION in about.information.toPlainText(), '关于版本不一致')
        self.require(DEFAULT_NETWORK in about.usage.toPlainText(), '离线帮助缺失')
        self.require('无担保' in about.legal.toPlainText(), '法律说明缺失')
        for index, (_, filename) in enumerate(LICENSE_DOCUMENTS):
            about.license_selector.setCurrentIndex(index)
            self.require(len(about.licenses.toPlainText()) > 100, '内置许可内容缺失：'+filename)
            self.require('无法读取内置文档' not in about.licenses.toPlainText(), '无法读取许可：'+filename)
        about.license_selector.setCurrentIndex(0)
        for theme in ('dark', 'light'):
            self.application.theme_manager.apply(theme, persist=False)
            for index in range(4):
                about.tabs.setCurrentIndex(index)
                self.application.processEvents()
        about.close()
        self.checks.append('about_help_licenses_legal_offline')
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
        from services.plan_storage import save_plan, load_plan
        calculation.target_input.setText('64')
        plan = self.window.plan_controller.snapshot()
        path = self.directory/'计算方案.json'
        save_plan(path, plan)
        restored = load_plan(path)
        self.require(restored == plan, '方案 JSON 往返不一致')
        self.window.plan_controller.apply(restored)
        self.require(self.window.result.subnet_count == 65536, '方案恢复计算不正确')
        self.checks.append('plan_save_and_restore_with_unicode_path')
        self.require(self.window.plan_controller.open_path(path), '共用方案导入入口失败')
        self.require(self.window.plan_controller.snapshot()==restored, '共用导入入口未恢复方案状态')
        # 自检只读临时方案，不触发桌面拖放或用户确认。
        self.window.plan_controller.path=None
        self.window.plan_controller.saved_document=None
        from PyQt6.QtCore import QCoreApplication
        self.require('全选' in QCoreApplication.translate('QLineEdit','Select All'), '缺少 Qt 中文标准菜单')
        self.require(resource_path('assets/qtbase_zh_CN.qm').is_file(), '缺少内置中文翻译')
        calculation.target_input.setText('47')
        self.window.calculate()
        self.require(calculation.target_input.property('invalid'), '目标前缀错误缺少红框')
        self.require(self.window.feedback.text().startswith('⚠'), '错误缺少警示标识')
        self.require(self.window.feedback.property('severity')=='error', '错误提示状态不正确')
        calculation.target_input.setText('64')
        self.require(not calculation.target_input.property('invalid'), '编辑后红框未清除')
        self.window.calculate()
        self.checks.append('shared_plan_import_chinese_catalog_and_input_error_recovery')

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
        panel=self.window.address_tools_page.range_panel
        panel.start_input.setText('::1');panel.end_input.setText('::ff');panel.convert()
        self.require(panel.result.address_count==255,'Range address count mismatch')
        self.require(sum(n.num_addresses for n in panel.result.cidrs)==255,'Range coverage mismatch')
        original=panel.result
        self.application.language_manager.apply('en_US',persist=False)
        self.require(panel.result is original and 'CIDRs:' in panel.summary.text(),'Range state/translation mismatch')
        self.application.language_manager.apply('zh_CN',persist=False)
        panel.start_input.setText('2026:1015:abcd::1');panel.end_input.setText('2026:1015:abcd::ff')
        self.checks.append('address_range_exact_coverage_and_bilingual_state')
        self.check_language_state()
        self.check_file_metadata_language()
        self.schedule(self.start_list_check)

    def check_file_metadata_language(self):
        from ui.standard_dialogs import QFileDialog
        folder=self.directory/'FolderTypeCheck'
        folder.mkdir()
        dialog=QFileDialog(self.window)
        try:
            dialog.setDirectory(str(self.directory))
            proxy=dialog.file_types
            original=proxy.sourceModel().index(str(folder))
            self.require(original.isValid(),'Folder index missing')
            index=proxy.mapFromSource(original.siblingAtColumn(2))
            self.require(proxy.data(index)=='文件夹','Chinese folder type missing')
            self.application.language_manager.apply('en_US',persist=False)
            self.require(proxy.data(index)=='Folder','English folder type missing')
            about=self.window.about_dialog
            about.license_selector.setCurrentIndex(0)
            self.require('Third-Party Components' in about.licenses.toPlainText(),'English component overview missing')
            self.require(not any('\u4e00'<=c<='\u9fff' for c in about.licenses.toPlainText()),'Chinese text in English overview')
            self.checks.append('file_metadata_and_component_overview_follow_language')
        finally:
            self.application.language_manager.apply('zh_CN',persist=False)
            dialog.deleteLater()

    def check_language_state(self):
        manager=self.application.language_manager
        page=self.window.results_page
        page.select_index(104)
        before=self.window.plan_controller.snapshot()
        result=self.window.result
        about=self.window.about_dialog
        about.tabs.setCurrentIndex(2)
        about.license_selector.setCurrentIndex(1)
        original=about.licenses.toPlainText()
        manager.apply('en_US',persist=False)
        self.require(self.window.tabs.tabText(0)=='Calculation','English tab missing')
        self.require('IPv6 Subnet Calculator' in self.window.windowTitle(),'English title missing')
        self.require(self.window.plan_controller.snapshot()==before,'Language switch changed calculation view')
        self.require(self.window.result is result,'Language switch recalculated result')
        self.require(about.tabs.currentIndex()==2 and about.license_selector.currentIndex()==1,'Language switch changed About selection')
        self.require(about.licenses.toPlainText()==original,'License original changed')
        self.require('User Guide' in about.usage.toPlainText(),'English offline guide missing')
        self.require('Runtime Components' in about.information.toPlainText(),'English program information missing')
        manager.apply('zh_CN',persist=False)
        self.require(self.window.tabs.tabText(0)=='子网计算','Chinese restoration missing')
        self.require(self.window.plan_controller.snapshot()==before,'Chinese restoration changed view')
        about.tabs.setCurrentIndex(0)
        about.license_selector.setCurrentIndex(0)
        page.clear_selection()
        self.checks.append('bilingual_live_switch_preserves_calculation_view_and_license_originals')

    def start_list_check(self):
        from services.subnet_list_service import load_subnet_list
        path = self.directory/'已有子网清单.txt'
        path.write_text('# 示例\n2026:1015:abcd::/48\n2026:1015:abcd:1::/64\n'
                        '2026:1015:abcd:1::1/64\n2026:1015:abcd:2::/64\nbad', encoding='utf-8-sig')
        page = self.window.subnet_list_page
        page.editor.setPlainText(load_subnet_list(path))
        page.service.completed.connect(self.completed_list_check)
        self.phase = 'list_check'
        page.analyze()

    def completed_list_check(self, outcome):
        if self.error:
            self.finish()
            return
        try:
            kind, result = outcome
            page = self.window.subnet_list_page
            if self.phase == 'list_check':
                self.require(kind == 'ok', '清单后台检查失败：'+str(result))
                self.require((result.valid_count, result.error_count) == (4, 1), '清单逐行校验不正确')
                self.require((result.duplicate_pairs, result.containment_pairs, result.adjacent_pairs) == (1,3,2),
                             '清单关系统计不正确')
                self.require(page.record_model.rowCount() == 5, '清单结果模型不完整')
                self.require(len(result.normalized_text().splitlines()) == 3, '清单去重不正确')
                self.checks.append('subnet_list_unicode_import_and_background_relations')
                from services.text_output import save_text_atomic
                from services.language_service import display
                self.require(page.output_controller.actions['networks'].isEnabled(),'List output action disabled')
                text_path=self.directory/'有效清单.txt'
                save_text_atomic(text_path,str(result.normalized_text())+'\n')
                self.require(len(text_path.read_text(encoding='utf-8').splitlines())==3,'Saved CIDR count mismatch')
                self.application.language_manager.apply('en_US',persist=False)
                report_path=self.directory/'检查报告.txt'
                save_text_atomic(report_path,display(result.as_text()))
                self.require('IPv6 Subnet List Check Report' in report_path.read_text(encoding='utf-8'),'English saved report missing')
                self.application.language_manager.apply('zh_CN',persist=False)
                self.checks.append('list_txt_output_and_localized_report')
                self.phase = 'planning_free'
                page.editor.setPlainText('::/127\n::2/127')
                page.planning.parent_input.setText('::/124')
                page.start_planning('free')
            elif self.phase == 'planning_free':
                self.require(kind == 'ok', '后台空闲空间计算失败：'+str(result))
                self.require(result.occupied_addresses == 4 and result.free_addresses == 12, '空闲容量不正确')
                self.require(result.cidr_text() == '::4/126\n::8/125', '空闲 CIDR 覆盖不正确')
                self.require(page.planning.copy_free_button.isEnabled(), '完整空闲结果无法复制')
                self.checks.append('parent_free_space_exact_union_and_difference')
                self.phase = 'planning_aggregate'
                page.start_planning('aggregate')
            elif self.phase == 'planning_aggregate':
                self.require(kind == 'ok', '后台 CIDR 整理失败：'+str(result))
                self.require(result.cidr_text() == '::/126' and result.address_count == 4, 'CIDR 等价整理不正确')
                self.require(page.editor.toPlainText() == '::/127\n::2/127', 'CIDR 整理改写了原始输入')
                self.checks.append('cidr_aggregation_preserves_coverage_and_input')
                from services.text_output import save_text_atomic
                self.require(page.output_controller.actions['aggregate_cidrs'].isEnabled(),'Planning output action disabled')
                self.require(page.planning.send_aggregate_button.isEnabled(),'Planning transfer disabled')
                output=self.directory/'整理结果.txt'
                save_text_atomic(output,str(result.cidr_text())+'\n')
                self.require(output.read_text(encoding='utf-8')=='::/126\n','Planning TXT mismatch')
                self.checks.append('planning_txt_output_and_transfer_actions')
                self.phase = 'list_cancel'
                page.editor.setPlainText('\n'.join(['::/0']*5000))
                page.analyze()
                page.cancel()
            else:
                self.require(kind == 'cancel', '清单取消未返回取消状态')
                self.require(page.analysis is None, '清单取消后显示了未完成结果')
                self.require(len(page.editor.toPlainText().splitlines()) == 5000, '清单取消丢失输入')
                page.editor.clear()
                self.checks.append('subnet_list_cancel_preserves_input')
                self.schedule(self.navigation_cycle)
        except Exception as exc:
            self.fail(str(exc) or type(exc).__name__)

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
            if fmt == 'xlsx':
                self.application.language_manager.apply('en_US',persist=False)
            self.service.start(self.current_path, result, fmt, 1, 100000 if fmt == 'txt' else 20000)
            if fmt == 'xlsx':
                self.application.language_manager.apply('zh_CN',persist=False)

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
                    ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                    book=ElementTree.fromstring(archive.read('xl/workbook.xml'))
                    self.require(book.find('x:sheets/x:sheet',ns).get('name')=='IPv6 Subnets',
                                 'English sheet name missing')
                    with archive.open('xl/worksheets/sheet1.xml') as header_stream:
                        for _,element in ElementTree.iterparse(header_stream,events=('end',)):
                            if element.tag.endswith('}row'):
                                headers=[cell.findtext('x:is/x:t',namespaces=ns) for cell in element]
                                self.require(headers==['No.','IPv6 Subnet'],'English export headers missing')
                                break
                    self.checks.append('english_xlsx_headers_and_frozen_export_language')
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
        if self.window.subnet_list_page.service.busy:
            self.window.subnet_list_page.cancel()
        if self.service.busy:
            self.service.cancel()
        else:
            self.finish()

    def finish(self):
        if self.finished or self.service.busy or self.window.subnet_list_page.service.busy:
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
