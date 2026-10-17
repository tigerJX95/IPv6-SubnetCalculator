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

"""集中维护全局与等宽字体，统一调整各页面和弹窗的可读性。"""
import sys
from PyQt6.QtGui import QFont

UI_POINT_SIZE = 12
DATA_POINT_SIZE = 12
BINARY_POINT_SIZE = 11
TITLE_PIXEL_SIZE = 28


def application_font():
    return QFont('Microsoft YaHei UI' if sys.platform == 'win32' else 'sans-serif', UI_POINT_SIZE)


def data_font(*, dense=False):
    return QFont('Consolas', BINARY_POINT_SIZE if dense else DATA_POINT_SIZE)
