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

"""将展示文本绑定到 Qt 控件；重新翻译只更新文字，不重建控件或编辑内容。"""
from PyQt6 import QtWidgets as W
from PyQt6.QtCore import QSignalBlocker
from PyQt6.QtGui import QAction
from core.localized_text import Text
from services.language_service import display


class Localized:
    def __init__(self,*args,**kwargs):
        self._localized={}
        super().__init__(*args,**kwargs)
        app=W.QApplication.instance()
        manager=getattr(app,'language_manager',None)
        if manager is not None:
            manager.changed.connect(self.retranslate)

    def _bind(self,key,value):
        self._localized[key]=value
        getattr(super(),key)(display(value))

    def retranslate(self,*_):
        for key,value in self._localized.items():
            getattr(super(),key)(display(value))

    def setWindowTitle(self,value):self._bind('setWindowTitle',value)
    def setToolTip(self,value):self._bind('setToolTip',value)
    def setAccessibleName(self,value):self._bind('setAccessibleName',value)
    def setAccessibleDescription(self,value):self._bind('setAccessibleDescription',value)
    def sourceToolTip(self):return self._localized.get('setToolTip',super().toolTip())


class QLabel(Localized,W.QLabel):
    def __init__(self,*args,**kwargs):
        value=args[0] if args and isinstance(args[0],str) else None
        super().__init__(*args,**kwargs)
        if value is not None:self.setText(value)
    def setText(self,value):self._bind('setText',value)
    def sourceText(self):return self._localized.get('setText',super().text())
    def clear(self):self.setText('')


class QGroupBox(Localized,W.QGroupBox):
    def __init__(self,*args,**kwargs):
        value=args[0] if args and isinstance(args[0],str) else None
        super().__init__(*args,**kwargs)
        if value is not None:self.setTitle(value)
    def setTitle(self,value):self._bind('setTitle',value)


class QLineEdit(Localized,W.QLineEdit):
    def setPlaceholderText(self,value):self._bind('setPlaceholderText',value)


class QPlainTextEdit(Localized,W.QPlainTextEdit):
    def setPlaceholderText(self,value):self._bind('setPlaceholderText',value)


class QComboBox(Localized,W.QComboBox):
    def __init__(self,*args,**kwargs):
        self._items=[]
        super().__init__(*args,**kwargs)
    def addItem(self,value,userData=None):
        self._items.append(value)
        super().addItem(display(value),userData)
    def addItems(self,values):
        for value in values:self.addItem(value)
    def setItemText(self,index,value):
        self._items[index]=value
        super().setItemText(index,display(value))
    def clear(self):
        self._items=[]
        super().clear()
    def sourceCurrentText(self):
        index=self.currentIndex()
        return self._items[index] if 0<=index<len(self._items) else ''
    def retranslate(self,*args):
        super().retranslate(*args)
        with QSignalBlocker(self):
            for i,value in enumerate(self._items):super().setItemText(i,display(value))


class QTabWidget(Localized,W.QTabWidget):
    def __init__(self,*args,**kwargs):
        self._tabs=[]
        super().__init__(*args,**kwargs)
    def addTab(self,widget,value):
        self._tabs.append(value)
        return super().addTab(widget,display(value))
    def retranslate(self,*args):
        super().retranslate(*args)
        for i,value in enumerate(self._tabs):super().setTabText(i,display(value))


class QRadioButton(Localized,W.QRadioButton):
    def __init__(self,*args,**kwargs):
        value=args[0] if args and isinstance(args[0],str) else None
        super().__init__(*args,**kwargs)
        if value is not None:self.setText(value)
    def setText(self,value):self._bind('setText',value)


class QDialog(Localized,W.QDialog):pass
class QMainWindow(Localized,W.QMainWindow):pass
class QToolButton(Localized,W.QToolButton):pass
class QTextBrowser(Localized,W.QTextBrowser):
    def setMarkdown(self,value):
        self._localized.pop('setPlainText',None)
        self._bind('setMarkdown',value)
    def setPlainText(self,value):
        self._localized.pop('setMarkdown',None)
        self._bind('setPlainText',value)
class QMessageBox(Localized,W.QMessageBox):
    def setText(self,value):self._bind('setText',value)


class QFormLayout(W.QFormLayout):
    def addRow(self,*args):
        values=list(args)
        if values and isinstance(values[0],str):values[0]=QLabel(values[0])
        return super().addRow(*values)


class LanguageAction(Localized,QAction):
    def setText(self,value):self._bind('setText',value)
