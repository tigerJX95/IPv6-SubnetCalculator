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

"""Qt 翻译器和界面语言偏好；业务数据、用户输入和 JSON 不参与翻译。"""
from PyQt6.QtCore import QObject,pyqtSignal,QTranslator,QLocale,QCoreApplication
from PyQt6.QtWidgets import QApplication
from app_info import resource_path
from core.localized_text import render

LANGUAGES=('zh_CN','en_US')


def display(value):
    app=QApplication.instance()
    manager=getattr(app,'language_manager',None)
    if manager is None or manager.name=='zh_CN':return str(value)
    return render(value,lambda source:QCoreApplication.translate('App',source))


class LanguageManager(QObject):
    changed=pyqtSignal(str)
    def __init__(self,application,settings):
        super().__init__(application)
        self.application=application
        self.settings=settings
        self.name='zh_CN'
        self.chinese=QTranslator(self)
        self.english=QTranslator(self)
        if not self.chinese.load(str(resource_path('assets/qtbase_zh_CN.qm'))):
            raise RuntimeError('Missing Chinese Qt translation catalog')
        if not self.english.load(str(resource_path('assets/i18n/app_en.qm'))):
            raise RuntimeError('Missing English application translation catalog')
        saved=settings.value('appearance/language','zh_CN')
        self.apply(saved if saved in LANGUAGES else 'zh_CN',persist=False)

    def apply(self,name,persist=True):
        if name not in LANGUAGES:raise ValueError('Unsupported language: '+str(name))
        self.application.removeTranslator(self.chinese)
        self.application.removeTranslator(self.english)
        self.name=name
        self.application.setProperty('languageName',name)
        QLocale.setDefault(QLocale(name))
        self.application.installTranslator(self.chinese if name=='zh_CN' else self.english)
        saved=True
        if persist:
            self.settings.setValue('appearance/language',name)
            self.settings.sync()
            saved=self.settings.status()==self.settings.Status.NoError
        self.changed.emit(name)
        return saved


def export_labels():
    """在 GUI 线程取得冻结的导出标签；工作线程始终使用此快照。"""
    from core.subnet_export import ExportLabels
    app = QApplication.instance()
    manager = getattr(app, 'language_manager', None)
    if manager is None or manager.name == 'zh_CN':
        return ExportLabels()
    translate = lambda source: QCoreApplication.translate('Export', source)
    return ExportLabels(translate('IPv6子网'), translate('序号'), translate('IPv6 子网'))
