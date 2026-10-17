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
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QApplication
from app_info import APP_NAME, APP_VERSION
from core.ipv6_core import calculate, InputError
from services.clipboard_service import ClipboardService
from services.export_service import ExportService
from ui.calculation_page import CalculationPage
from ui.results_page import ResultsPage
from ui.export_controller import ExportController
from ui.widgets import FeedbackLabel, ThemeButton


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f'{APP_NAME} V{APP_VERSION}')
        self.resize(1080, 800)
        self.setMinimumSize(900, 620)
        self.closing_after_export = False
        self.result = None
        central = QWidget()
        central.setObjectName('AppRoot')
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(22, 18, 22, 12)
        layout.setSpacing(8)
        title = QLabel(APP_NAME)
        title.setObjectName('AppTitle')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel('网络范围 · 子网划分 · 容量计算')
        subtitle.setObjectName('AppSubtitle')
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading = QHBoxLayout()
        heading.setContentsMargins(0, 0, 0, 0)
        heading.addSpacing(38)
        heading.addWidget(title, 1)
        self.theme_manager = QApplication.instance().theme_manager
        self.theme_button = ThemeButton(self.theme_manager)
        self.theme_button.clicked.connect(self._toggle_theme)
        heading.addWidget(self.theme_button, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(heading)
        layout.addWidget(subtitle)
        layout.addSpacing(5)
        self.clipboard = ClipboardService(self)
        self.export_service = ExportService(self)
        self.tabs = QTabWidget()
        self.calculation_page = CalculationPage()
        self.results_page = ResultsPage(self.clipboard)
        self.tabs.addTab(self.calculation_page, '子网计算')
        self.tabs.addTab(self.results_page, '子网结果')
        layout.addWidget(self.tabs, 1)
        self.feedback = FeedbackLabel()
        layout.addWidget(self.feedback)

        self.export_controller = ExportController(self, self.export_service)
        self.calculation_page.calculate_requested.connect(self.calculate)
        self.results_page.export_requested.connect(lambda: self.export_controller.request_export(self.result))
        self.results_page.feedback.connect(self.feedback.set_message)
        self.clipboard.feedback.connect(self.feedback.set_message)
        self.export_controller.feedback.connect(self.feedback.set_message)
        self.export_controller.busy_changed.connect(self._export_busy_changed)

    def _toggle_theme(self):
        saved = self.theme_manager.toggle()
        name = '深色' if self.theme_manager.name == 'dark' else '浅色'
        self.feedback.set_message(f'已切换到{name}主题。' if saved else
            f'已切换到{name}主题，但无法保存偏好，下次启动可能恢复默认主题。',
            'success' if saved else 'error')

    def calculate(self):
        if self.export_service.busy:
            self.feedback.set_message('请先完成或取消导出。', 'info')
            return
        network, prefix = self.calculation_page.parameters()
        try:
            result = calculate(network, prefix, preview_limit=0)
        except InputError as exc:
            self.result = None
            self.calculation_page.set_result(None)
            self.results_page.set_result(None)
            self.feedback.set_message('输入错误：'+str(exc), 'error')
            return
        self.result = result
        self.calculation_page.set_result(result)
        self.results_page.set_result(result)
        self.feedback.set_message('输入地址已规范化到所属网络。' if result.normalized else '计算完成。', 'success')
        self.tabs.setCurrentWidget(self.results_page)

    def _export_busy_changed(self, busy):
        self.results_page.set_export_enabled(not busy)
        self.calculation_page.calculate_button.setEnabled(not busy)

    def closeEvent(self, event):
        if self.export_service.busy:
            self.closing_after_export = True
            self.export_controller.cancel()
            self.feedback.set_message('正在取消导出并清理临时文件，完成后退出…', 'info')
            event.ignore()
            return
        event.accept()
