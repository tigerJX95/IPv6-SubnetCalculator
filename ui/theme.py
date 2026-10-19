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

"""集中定义主题颜色；所有页面和弹窗使用同一套语义色。"""
from core.localized_text import text as tx, join_text as jt
from PyQt6.QtCore import QObject, QSettings, pyqtSignal
from PyQt6.QtWidgets import QApplication
from app_info import resource_path
from ui.fonts import TITLE_PIXEL_SIZE

THEMES = {
    'light': dict(text='#23364a', window='#f5f7fa', surface='#ffffff', title='#172e45',
        muted='#677b90', border='#d7e0e9', tab='#edf2f7', hover='#e2edf8',
        accent='#096ab8', input_border='#c9d6e3', focus='#2682cc', disabled='#f1f4f7',
        disabled_text='#8696a6', selected='#1674c4', selected_text='#ffffff',
        alternate='#f2f7fc', header='#f1f5f9', handle='#b4c7d9', metric='#173d60',
        hint='#356c99', warning='#a84431', success='#137547', error='#b42318',
        progress='#e6edf5', tooltip='#fff9e9', highlight='#cce5fb', button='#eaf2fb'),
    'dark': dict(text='#d6e2f0', window='#121b27', surface='#1b2838', title='#edf5ff',
        muted='#9aafc7', border='#354960', tab='#182434', hover='#2b4058',
        accent='#83c3ff', input_border='#415771', focus='#70baff', disabled='#243244',
        disabled_text='#7b8ea4', selected='#235f96', selected_text='#ffffff',
        alternate='#213246', header='#25374c', handle='#506c8b', metric='#c7e4ff',
        hint='#97c6f0', warning='#ffbc91', success='#7dddac', error='#ff9d9d',
        progress='#2c4159', tooltip='#2b3b50', highlight='#294e70', button='#29415c'),
}


def stylesheet(name):
    c = THEMES[name]
    arrow = resource_path(tx('assets/chevron_{0}.svg', name)).as_posix()
    return '''
QWidget {{ color: {text}; background: transparent; }}
QMainWindow, QDialog, QWidget#AppRoot {{ background: {window}; }}
QWidget#CalculationPage, QWidget#ResultsPage, QWidget#AddressToolsPage, QWidget#SubnetListPage {{ background: {surface}; }}
QLabel#AppTitle {{ color: {title}; font-size: {title_px}px; font-weight: 700; }}
QLabel#AppSubtitle {{ color: {muted}; }}
QTabWidget::pane {{ border: 1px solid {border}; background: {surface}; border-radius: 8px; }}
QTabBar::tab {{ background: {tab}; padding: 10px 26px; margin-right: 4px;
    border-top-left-radius: 7px; border-top-right-radius: 7px; color: {muted}; }}
QTabBar::tab:selected {{ background: {surface}; color: {accent}; font-weight: 600; }}
QTabBar::tab:hover:!selected {{ background: {hover}; }}
QGroupBox {{ border: 1px solid {border}; border-radius: 8px; margin-top: 12px;
    padding: 15px 12px 10px; background: {surface}; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 5px; color: {hint}; }}
QLineEdit, QComboBox, QPlainTextEdit {{ border: 1px solid {input_border}; border-radius: 5px;
    background: {surface}; padding: 6px 9px; min-height: 22px;
    selection-background-color: {selected}; selection-color: {selected_text}; }}
QComboBox {{ padding-right: 28px; }}
QComboBox::drop-down {{ border: 0; width: 25px; background: transparent; }}
QComboBox::down-arrow {{ image: url("{arrow}"); width: 12px; height: 8px; }}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {{ border: 1px solid {focus}; }}
QLineEdit[invalid="true"], QPlainTextEdit[invalid="true"] {{ border: 2px solid {error}; }}
QLineEdit:disabled, QComboBox:disabled, QPlainTextEdit:disabled {{ background: {disabled}; color: {disabled_text}; }}
QLineEdit {{ placeholder-text-color: {muted}; }}
QTextBrowser#AboutText {{ background: {surface}; color: {text}; border: 0;
    padding: 14px; selection-background-color: {selected}; selection-color: {selected_text}; }}
QComboBox QAbstractItemView {{ background: {surface}; color: {text}; border: 1px solid {border};
    selection-background-color: {selected}; selection-color: {selected_text}; outline: 0; }}
QToolButton {{ border: 0; background: transparent; padding: 0; border-radius: 7px; }}
QToolButton::menu-indicator {{ image: none; width: 0; }}
QToolButton:focus {{ border: 1px solid {focus}; }}
QPushButton {{ background: {button}; color: {text}; border: 1px solid {border}; border-radius: 5px; padding: 7px 15px; }}
QPushButton:hover {{ background: {hover}; }}
QPushButton:focus {{ border: 1px solid {focus}; }}
QPushButton:disabled, QRadioButton:disabled {{ color: {disabled_text}; }}
QRadioButton::indicator {{ width: 14px; height: 14px; border: 1px solid {muted}; border-radius: 7px; background: {surface}; }}
QRadioButton::indicator:checked {{ border: 4px solid {accent}; width: 8px; height: 8px; }}
QTableView {{ border: 1px solid {border}; border-radius: 5px; background: {surface};
    alternate-background-color: {alternate}; selection-background-color: {selected};
    selection-color: {selected_text}; gridline-color: {border}; outline: 0; }}
QHeaderView, QTableCornerButton::section {{ background: {header}; border: 0; }}
QHeaderView::section {{ background: {header}; color: {hint}; border: 0;
    border-bottom: 1px solid {border}; padding: 8px; font-weight: 600; }}
QScrollBar:vertical {{ background: {header}; width: 13px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {handle}; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: {header}; }}
QScrollBar:horizontal {{ background: {header}; height: 13px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {handle}; border-radius: 5px; min-width: 30px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: {header}; }}
QLabel#MetricValue {{ color: {metric}; }}
QLabel#Hint {{ color: {hint}; }}
QLabel#UsageType, QLabel#UsageGuidance {{ color: {warning}; }}
QLabel#UsageType {{ font-weight: 600; }}
QLabel#Reference {{ color: {muted}; }}
QLabel[invalid="true"] {{ color: {error}; border: 1px solid {error}; border-radius: 4px; padding: 3px; font-weight: 700; }}
QLabel#Feedback {{ padding: 5px 1px; }}
QLabel#Feedback[severity="success"] {{ color: {success}; }}
QLabel#Feedback[severity="error"] {{ color: {error}; font-weight: 700; }}
QLabel#Feedback[severity="info"] {{ color: {hint}; }}
QProgressBar {{ border: 0; background: {progress}; border-radius: 5px; min-height: 10px; text-align: center; }}
QProgressBar::chunk {{ background: {focus}; border-radius: 5px; }}
QToolTip {{ color: {text}; background: {tooltip}; border: 1px solid {border}; padding: 7px; }}
QScrollArea {{ border: 0; background: {surface}; }}
QWidget#CalculationViewport, QWidget#CalculationContent, QWidget#ToolsViewport, QWidget#ToolsContent {{ background: {surface}; }}
QMenu {{ background: {surface}; color: {text}; border: 1px solid {border}; padding: 4px; }}
QMenu::item:selected {{ background: {selected}; color: {selected_text}; }}
'''.format(arrow=arrow, title_px=TITLE_PIXEL_SIZE, **c)


class ThemeManager(QObject):
    changed = pyqtSignal(str)

    def __init__(self, application, settings=None):
        super().__init__(application)
        self.application = application
        self.settings = settings if settings is not None else QSettings('IPv6SubnetCalculator', 'Preferences')
        saved = self.settings.value('appearance/theme', 'light')
        self.name = saved if isinstance(saved, str) and saved in THEMES else 'light'
        self.apply(self.name, persist=False)

    @property
    def colors(self):
        return THEMES[self.name]

    def apply(self, name, persist=True):
        if name not in THEMES:
            raise ValueError('Unknown theme: '+str(name))
        self.name = name
        self.application.setProperty('themeName', name)
        self.application.setStyleSheet(stylesheet(name))
        saved = True
        if persist:
            self.settings.setValue('appearance/theme', name)
            self.settings.sync()
            saved = self.settings.status() == QSettings.Status.NoError
        self.changed.emit(name)
        return saved

    def toggle(self):
        return self.apply('dark' if self.name == 'light' else 'light')


def current_colors():
    application = QApplication.instance()
    return THEMES.get(application.property('themeName') if application else 'light', THEMES['light'])


# Kept for integrations that import the default stylesheet.
STYLESHEET = stylesheet('light')
