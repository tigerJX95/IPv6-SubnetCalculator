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

"""集中维护标准弹窗，中文版本不依赖操作系统显示语言。"""
from PyQt6.QtCore import QTranslator, Qt, QLocale
from PyQt6.QtWidgets import QFileDialog as QtFileDialog, QMessageBox as QtMessageBox, QDialog
from app_info import resource_path


def install_chinese_dialogs(application):
    # 标准文件类型、日期和大小使用当前界面语言，而非系统语言。
    QLocale.setDefault(QLocale('zh_CN'))
    translator = QTranslator(application)
    if not translator.load(str(resource_path('assets/qtbase_zh_CN.qm'))):
        raise RuntimeError('无法加载中文对话框资源，请重新安装完整程序。')
    application.installTranslator(translator)
    application.qt_chinese_translator = translator


class QMessageBox(QtMessageBox):
    """保留 Qt 标准返回值，明确中文按钮和保守默认项。"""
    @staticmethod
    def _show(icon, parent, title, text, buttons, default):
        box = QMessageBox(parent)
        box.setWindowTitle(title)
        box.setIcon(icon)
        box.setTextFormat(Qt.TextFormat.PlainText)
        box.setText(text)
        box.setStandardButtons(buttons)
        labels = {QMessageBox.StandardButton.Ok:'确定', QMessageBox.StandardButton.Cancel:'取消',
            QMessageBox.StandardButton.Yes:'是', QMessageBox.StandardButton.No:'否',
            QMessageBox.StandardButton.Save:'保存', QMessageBox.StandardButton.Discard:'不保存',
            QMessageBox.StandardButton.Close:'关闭', QMessageBox.StandardButton.Retry:'重试',
            QMessageBox.StandardButton.Abort:'中止', QMessageBox.StandardButton.Ignore:'忽略'}
        for button, label in labels.items():
            if box.button(button) is not None:
                box.button(button).setText(label)
        if default != QMessageBox.StandardButton.NoButton:
            box.setDefaultButton(default)
        try:
            box.exec()
            return box.standardButton(box.clickedButton())
        finally:
            box.deleteLater()

    @staticmethod
    def warning(parent, title, text, buttons=QtMessageBox.StandardButton.Ok,
                defaultButton=QtMessageBox.StandardButton.NoButton):
        return QMessageBox._show(QMessageBox.Icon.Warning,parent,title,text,buttons,defaultButton)

    @staticmethod
    def information(parent, title, text, buttons=QtMessageBox.StandardButton.Ok,
                    defaultButton=QtMessageBox.StandardButton.NoButton):
        return QMessageBox._show(QMessageBox.Icon.Information,parent,title,text,buttons,defaultButton)

    @staticmethod
    def question(parent, title, text, buttons=QtMessageBox.StandardButton.Yes|QtMessageBox.StandardButton.No,
                 defaultButton=QtMessageBox.StandardButton.No):
        return QMessageBox._show(QMessageBox.Icon.Question,parent,title,text,buttons,defaultButton)


class QFileDialog(QtFileDialog):
    """使用自带中文目录浏览器，避免系统语言影响文件选择窗口。"""
    @staticmethod
    def _choose(parent, caption, directory, filter, selectedFilter, options, saving):
        dialog = QFileDialog(parent,caption,directory,filter)
        dialog.setOptions(options | QFileDialog.Option.DontUseNativeDialog)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave if saving else QFileDialog.AcceptMode.AcceptOpen)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile if saving else QFileDialog.FileMode.ExistingFile)
        for role,label in ((QFileDialog.DialogLabel.LookIn,'位置：'),(QFileDialog.DialogLabel.FileName,'文件名：'),
                           (QFileDialog.DialogLabel.FileType,'文件类型：'),(QFileDialog.DialogLabel.Reject,'取消'),
                           (QFileDialog.DialogLabel.Accept,'保存' if saving else '打开')):
            dialog.setLabelText(role,label)
        if selectedFilter:
            dialog.selectNameFilter(selectedFilter)
        try:
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return '', ''
            paths=dialog.selectedFiles()
            return (paths[0] if paths else ''), dialog.selectedNameFilter()
        finally:
            dialog.deleteLater()

    @staticmethod
    def getOpenFileName(parent=None, caption='', directory='', filter='', selectedFilter='', options=QtFileDialog.Option(0)):
        return QFileDialog._choose(parent,caption,directory,filter,selectedFilter,options,False)

    @staticmethod
    def getSaveFileName(parent=None, caption='', directory='', filter='', selectedFilter='', options=QtFileDialog.Option(0)):
        return QFileDialog._choose(parent,caption,directory,filter,selectedFilter,options,True)
