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

"""主窗口只负责页面和服务的协调；计算、复制、导出均由对应模块维护。"""
from ui.localized_widgets import QMainWindow, QLabel, QTabWidget
from core.localized_text import text as tx, join_text as jt
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication
from app_info import APP_NAME, APP_VERSION
from core.ipv6_core import calculate, InputError
from services.clipboard_service import ClipboardService
from services.export_service import ExportService
from ui.calculation_page import CalculationPage
from ui.results_page import ResultsPage
from ui.address_tools_page import AddressToolsPage
from ui.range_transfer_controller import RangeTransferController
from ui.subnet_list_page import SubnetListPage
from ui.export_controller import ExportController
from ui.plan_controller import PlanController
from ui.plan_drop_controller import PlanDropController
from ui.input_feedback import mark_invalid, clear_invalid
from ui.about_dialog import AboutDialog
from ui.widgets import FeedbackLabel, ThemeButton, AboutButton, LanguageButton


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tx('{0} V{1}', APP_NAME, APP_VERSION))
        self.resize(1080, 800)
        self.setMinimumSize(900, 620)
        self.closing_after_export = False
        self.closing_after_list_check = False
        self.result = None
        self.about_dialog = None
        central = QWidget()
        central.setObjectName('AppRoot')
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(22, 18, 22, 12)
        layout.setSpacing(8)
        title = QLabel(APP_NAME)
        title.setObjectName('AppTitle')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel(tx('离线 IPv6 子网计算、分析与轻量规划工具。'))
        subtitle.setObjectName('AppSubtitle')
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading = QHBoxLayout()
        heading.setContentsMargins(0, 0, 0, 0)
        heading.addSpacing(126)
        heading.addWidget(title, 1)
        self.theme_manager = QApplication.instance().theme_manager
        self.theme_button = ThemeButton(self.theme_manager)
        self.theme_button.clicked.connect(self._toggle_theme)
        title_actions = QHBoxLayout()
        title_actions.setSpacing(6)
        self.language_manager=QApplication.instance().language_manager
        self.language_button=LanguageButton(self.language_manager,self.theme_manager)
        title_actions.addWidget(self.language_button)
        title_actions.addWidget(self.theme_button)
        self.about_button = AboutButton(self.theme_manager)
        self.about_button.clicked.connect(self.show_about)
        self.about_shortcut = QShortcut(QKeySequence('F1'), self)
        self.about_shortcut.activated.connect(self.show_about)
        title_actions.addWidget(self.about_button)
        heading.addLayout(title_actions)
        layout.addLayout(heading)
        layout.addWidget(subtitle)
        layout.addSpacing(5)
        self.clipboard = ClipboardService(self)
        self.export_service = ExportService(self)
        self.tabs = QTabWidget()
        self.calculation_page = CalculationPage()
        self.results_page = ResultsPage(self.clipboard)
        self.address_tools_page = AddressToolsPage(self.clipboard)
        self.subnet_list_page = SubnetListPage(self.clipboard)
        self.tabs.addTab(self.calculation_page, tx('子网计算'))
        self.tabs.addTab(self.results_page, tx('子网结果'))
        self.tabs.addTab(self.address_tools_page, tx('地址工具'))
        self.tabs.addTab(self.subnet_list_page, tx('子网清单'))
        layout.addWidget(self.tabs, 1)
        self.feedback = FeedbackLabel()
        layout.addWidget(self.feedback)

        self.range_transfer_controller=RangeTransferController(self)
        self.plan_controller = PlanController(self)
        self.plan_drop_controller = PlanDropController(self)
        self.export_controller = ExportController(self, self.export_service)
        self.calculation_page.calculate_requested.connect(self.calculate)
        self.calculation_page.summary_copy_requested.connect(self._copy_calculation_summary)
        self.results_page.export_requested.connect(lambda: self.export_controller.request_export(self.result))
        self.results_page.feedback.connect(self.feedback.set_message)
        self.address_tools_page.feedback.connect(self.feedback.set_message)
        self.subnet_list_page.feedback.connect(self.feedback.set_message)
        self.subnet_list_page.busy_changed.connect(self._list_busy_changed)
        self.clipboard.feedback.connect(self.feedback.set_message)
        self.export_controller.feedback.connect(self.feedback.set_message)
        self.export_controller.busy_changed.connect(self._export_busy_changed)

    def show_about(self):
        if self.about_dialog is None:
            self.about_dialog = AboutDialog(self)
        self.about_dialog.show()
        self.about_dialog.raise_()
        self.about_dialog.activateWindow()

    def _copy_calculation_summary(self, text):
        self.clipboard.copy_text(text, tx('计算摘要已复制到剪贴板。'), self.calculation_page)

    def _toggle_theme(self):
        saved = self.theme_manager.toggle()
        name = tx('深色') if self.theme_manager.name == 'dark' else tx('浅色')
        self.feedback.set_message(tx('已切换到{0}主题。', name) if saved else
            tx('已切换到{0}主题，但无法保存偏好，下次启动可能恢复默认主题。', name),
            'success' if saved else 'error')

    def calculate(self):
        if self.export_service.busy:
            self.feedback.set_message(tx('请先完成或取消导出。'), 'info')
            return
        for field in (self.calculation_page.network_input,self.calculation_page.target_input):
            clear_invalid(field)
        network, prefix = self.calculation_page.parameters()
        try:
            result = calculate(network, prefix, preview_limit=0)
        except InputError as exc:
            field = self.calculation_page.target_input if exc.field == 'target' else self.calculation_page.network_input
            mark_invalid(field,str(exc))
            field.setFocus()
            self.tabs.setCurrentWidget(self.calculation_page)
            self.result = None
            self.calculation_page.set_result(None)
            self.results_page.set_result(None)
            self.feedback.set_message(tx('输入错误：')+str(exc), 'error')
            return
        self.result = result
        self.calculation_page.set_result(result)
        self.results_page.set_result(result)
        self.feedback.set_message(tx('输入地址已规范化到所属网络。') if result.normalized else tx('计算完成。'), 'success')
        self.tabs.setCurrentWidget(self.results_page)

    def _export_busy_changed(self, busy):
        self.results_page.set_export_enabled(not busy)
        self.calculation_page.calculate_button.setEnabled(not busy)
        self.calculation_page.save_plan_button.setEnabled(not busy and self.result is not None)
        self.calculation_page.open_plan_button.setEnabled(not busy)

    def _list_busy_changed(self, busy):
        if not busy and self.closing_after_list_check:
            self.closing_after_list_check = False
            QTimer.singleShot(0, self.close)

    def closeEvent(self, event):
        if self.export_service.busy:
            self.closing_after_export = True
            self.export_controller.cancel()
            self.feedback.set_message(tx('正在取消导出并清理临时文件，完成后退出…'), 'info')
            event.ignore()
            return
        if self.subnet_list_page.service.busy:
            self.closing_after_list_check = True
            self.subnet_list_page.cancel()
            self.feedback.set_message(tx('正在取消清单检查，完成后退出…'), 'info')
            event.ignore()
            return
        if not self.plan_controller.confirm_discard():
            self.closing_after_export = False
            event.ignore()
            return
        if not self.subnet_list_page.project_controller.confirm_discard():
            self.closing_after_export = False
            self.closing_after_list_check = False
            event.ignore()
            return
        if self.about_dialog is not None:
            self.about_dialog.close()
        event.accept()
