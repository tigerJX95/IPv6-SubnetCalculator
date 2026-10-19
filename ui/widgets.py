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

"""共用图标按钮、可复制统计标签和反馈显示。"""
from ui.localized_widgets import QToolButton, QLabel
from core.localized_text import text as tx, join_text as jt, Text
from math import cos, sin, pi
from functools import lru_cache
from PyQt6.QtCore import Qt, QSize, QEvent, QPointF, pyqtSignal
from PyQt6.QtGui import QIcon, QImage, QPixmap, QColor, QPainter, QPen
from PyQt6.QtWidgets import QApplication, QMenu
from app_info import resource_path
from ui.fonts import data_font
from ui.theme import current_colors


@lru_cache(maxsize=64)
def dark_icon(path, state):
    """Map existing icon tiles to dark surfaces while preserving shape and alpha."""
    source = QImage(str(path)).convertToFormat(QImage.Format.Format_ARGB32)
    base = QColor('#314c69' if state == 'hover' else '#233041' if state == 'disabled' else '#24374c')
    ink = QColor('#93a8bf' if state == 'disabled' else '#89c7ff')
    for y in range(source.height()):
        for x in range(source.width()):
            pixel = source.pixelColor(x, y)
            strength = max(0.0, min(1.0, (255-pixel.red())/210))
            source.setPixelColor(x, y, QColor(*(round(a+(b-a)*strength)
                for a, b in zip(base.getRgb()[:3], ink.getRgb()[:3])), pixel.alpha()))
    return QPixmap.fromImage(source)


class IconButton(QToolButton):
    def __init__(self, name, tooltip, parent=None):
        super().__init__(parent)
        self.asset_name = name
        self._icons = {state: QIcon(str(resource_path(tx('assets/{0}_{1}.png', name, state))))
                       for state in ('normal', 'hover', 'disabled')}
        self._dark_icons = {}
        for state in self._icons:
            pixmap = dark_icon(resource_path(tx('assets/{0}_{1}.png', name, state)), state)
            icon = QIcon(pixmap)
            icon.addPixmap(pixmap, QIcon.Mode.Disabled)
            self._dark_icons[state] = icon
        self._hovered = False
        self.setToolTip(tooltip)
        self.setAccessibleName(tooltip.line() if isinstance(tooltip,Text) else tooltip.split("\n")[0])
        self.setObjectName(name)
        size = 34 if name.endswith('_small') else 44
        self.setIconSize(QSize(size, size))
        self.setFixedSize(size + 2, size + 2)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._refresh_icon()
        manager = getattr(QApplication.instance(), 'theme_manager', None)
        if manager is not None:
            manager.changed.connect(self._refresh_icon)

    def _refresh_icon(self, *_args):
        state = 'disabled' if not self.isEnabled() else 'hover' if self._hovered else 'normal'
        icons = self._dark_icons if QApplication.instance().property('themeName') == 'dark' else self._icons
        self.setIcon(icons[state])

    def enterEvent(self, event):
        self._hovered = True
        self._refresh_icon()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._refresh_icon()
        super().leaveEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.EnabledChange and hasattr(self, '_icons'):
            self._refresh_icon()
        super().changeEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.click()
            event.accept()
        else:
            super().keyPressEvent(event)


class AboutButton(QToolButton):
    """与主题按钮一致的透明矢量图标，不使用带底纹的图块。"""
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.setObjectName('about_small')
        self.setFixedSize(38,38)
        self.setIconSize(QSize(26,26))
        self.setToolTip(tx('关于程序、使用说明、第三方许可和法律责任（F1）'))
        self.setAccessibleName(self.sourceToolTip())
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        manager.changed.connect(self.refresh)
        self.refresh()

    def refresh(self, *_args):
        pixmap=QPixmap(52,52)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter=QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(2,2)
        color=QColor(current_colors()['accent'])
        painter.setPen(QPen(color,1.8,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
        painter.drawEllipse(QPointF(13,13),9,9)
        painter.drawLine(QPointF(13,12),QPointF(13,18))
        painter.drawLine(QPointF(11,18),QPointF(15,18))
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(13,8.5),1.1,1.1)
        painter.end()
        self.setIcon(QIcon(pixmap))

    def keyPressEvent(self,event):
        if event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter):
            self.click()
            event.accept()
        else:
            super().keyPressEvent(event)


class ThemeButton(QToolButton):
    """A moon/sun button using vector painting and a keyboard shortcut."""
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setObjectName('theme_toggle')
        self.setFixedSize(38, 38)
        self.setIconSize(QSize(26, 26))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setShortcut('Ctrl+Shift+T')
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        manager.changed.connect(self.refresh)
        self.refresh()

    def refresh(self, *_args):
        dark = self.manager.name == 'dark'
        text = tx('当前：{0}主题\n切换到{1}主题（Ctrl+Shift+T）', tx('深色') if dark else tx('浅色'), tx('浅色') if dark else tx('深色'))
        self.setToolTip(text)
        self.setAccessibleName(text.replace('\n', '，'))
        pixmap = QPixmap(52, 52)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(2, 2)
        color = QColor(current_colors()['accent'])
        painter.setPen(QPen(color, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        if dark:
            painter.drawEllipse(QPointF(13, 13), 4.5, 4.5)
            for step in range(8):
                angle = step*pi/4
                painter.drawLine(QPointF(13+7.5*cos(angle), 13+7.5*sin(angle)),
                                 QPointF(13+10*cos(angle), 13+10*sin(angle)))
        else:
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(12, 13), 9, 9)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.drawEllipse(QPointF(17, 8), 8, 8)
        painter.end()
        self.setIcon(QIcon(pixmap))

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.click()
            event.accept()
        else:
            super().keyPressEvent(event)


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setWordWrap(True)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit()
        else:
            super().keyPressEvent(event)


class FeedbackLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('Feedback')
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setWordWrap(True)
        self.setMinimumHeight(30)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.set_message(tx('输入参数后点击“开始计算”。'))

    def set_message(self, text, severity='info'):
        self.setText(('⚠ '+text) if severity == 'error' else text)
        self.setAccessibleDescription(text)
        self.setProperty('severity', severity)
        self.style().unpolish(self)
        self.style().polish(self)


def value_label(text='—', parent=None):
    label = QLabel(text, parent)
    label.setObjectName('MetricValue')
    label.setFont(data_font())
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return label


class LanguageButton(QToolButton):
    """透明地球图标；菜单使用语言自称，切换不重建任何工作页。"""
    def __init__(self,manager,theme_manager,parent=None):
        super().__init__(parent)
        self.manager=manager
        self.setObjectName('language_toggle')
        self.setFixedSize(38,38)
        self.setIconSize(QSize(26,26))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setToolTip(tx('语言：简体中文 / English'))
        self.setAccessibleName(tx('语言：简体中文 / English'))
        self.menu=QMenu(self)
        self.actions_by_language={}
        for code,label in (('zh_CN','简体中文'),('en_US','English')):
            action=self.menu.addAction(label)
            action.setCheckable(True)
            action.triggered.connect(lambda checked=False,code=code:self.choose(code))
            self.actions_by_language[code]=action
        self.setMenu(self.menu)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        manager.changed.connect(self.refresh)
        theme_manager.changed.connect(self.refresh)
        self.refresh()

    def choose(self,name):
        if name==self.manager.name:
            self.refresh()
            return
        saved=self.manager.apply(name)
        if not saved:
            window=self.window()
            if hasattr(window,'feedback'):
                window.feedback.set_message(tx('语言已切换，但无法保存偏好，下次启动可能恢复默认语言。'),'error')

    def refresh(self,*_):
        for code,action in self.actions_by_language.items():action.setChecked(code==self.manager.name)
        pixmap=QPixmap(52,52);pixmap.fill(Qt.GlobalColor.transparent)
        painter=QPainter(pixmap);painter.setRenderHint(QPainter.RenderHint.Antialiasing);painter.scale(2,2)
        painter.setPen(QPen(QColor(current_colors()['accent']),1.5))
        painter.drawEllipse(QPointF(13,13),9,9)
        painter.drawEllipse(QPointF(13,13),4.2,9)
        painter.drawLine(QPointF(4,13),QPointF(22,13))
        painter.drawLine(QPointF(6,8),QPointF(20,8))
        painter.drawLine(QPointF(6,18),QPointF(20,18))
        painter.end();self.setIcon(QIcon(pixmap))
