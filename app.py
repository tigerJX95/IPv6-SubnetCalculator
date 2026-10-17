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

"""创建 Qt 应用并加载主窗口；不包含业务计算。"""
import sys
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QApplication
from app_info import APP_NAME, APP_VERSION, resource_path
from ui.theme import ThemeManager


def create_application(argv=None, settings=None):
    existing = QApplication.instance()
    if existing is not None:
        return existing
    application = QApplication(sys.argv if argv is None else argv)
    application.setApplicationName(APP_NAME)
    application.setApplicationVersion(APP_VERSION)
    application.setStyle('Fusion')
    font = QFont('Microsoft YaHei UI' if sys.platform == 'win32' else 'sans-serif', 10)
    application.setFont(font)
    application.setWindowIcon(QIcon(str(resource_path('app.ico'))))
    application.theme_manager = ThemeManager(application, settings)
    return application


def run():
    from ui.main_window import MainWindow
    application = create_application()
    window = MainWindow()
    window.show()
    return application.exec()
