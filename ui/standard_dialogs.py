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
from core.localized_text import text as tx, join_text as jt
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog as QtFileDialog, QDialog, QApplication, QLineEdit
from ui.localized_widgets import QMessageBox as QtMessageBox
from services.language_service import display
from ui.file_dialog_model import LocalizedFileSystemModel


class QMessageBox(QtMessageBox):
    """保留 Qt 标准返回值，明确中文按钮和保守默认项。"""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._button_sources={}
        QApplication.instance().language_manager.changed.connect(self._translate_buttons)

    def _translate_buttons(self,*_args):
        for button,label in self._button_sources.items():
            if self.button(button) is not None:self.button(button).setText(display(label))

    @staticmethod
    def _show(icon, parent, title, text, buttons, default):
        box = QMessageBox(parent)
        box.setWindowTitle(title)
        box.setIcon(icon)
        box.setTextFormat(Qt.TextFormat.PlainText)
        box.setText(text)
        box.setStandardButtons(buttons)
        labels = {QMessageBox.StandardButton.Ok:tx('确定'), QMessageBox.StandardButton.Cancel:tx('取消'),
            QMessageBox.StandardButton.Yes:tx('是'), QMessageBox.StandardButton.No:tx('否'),
            QMessageBox.StandardButton.Save:tx('保存'), QMessageBox.StandardButton.Discard:tx('不保存'),
            QMessageBox.StandardButton.Close:tx('关闭'), QMessageBox.StandardButton.Retry:tx('重试'),
            QMessageBox.StandardButton.Abort:tx('中止'), QMessageBox.StandardButton.Ignore:tx('忽略')}
        box._button_sources=labels
        box._translate_buttons()
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
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.setOption(QtFileDialog.Option.DontUseNativeDialog)
        self.file_types=LocalizedFileSystemModel(self)
        self.setProxyModel(self.file_types)
        self._caption_source=None
        self._filters_source=None
        self._labels_source={}
        QApplication.instance().language_manager.changed.connect(self._translate_fields)

    def _translate_fields(self,*_args):
        if self._caption_source is None:return
        self.setWindowTitle(display(self._caption_source))
        editor=self.findChild(QLineEdit,'fileNameEdit')
        entered=editor.text() if editor is not None else None
        old=self.nameFilters();selected=self.selectedNameFilter()
        index=old.index(selected) if selected in old else 0
        filters=display(self._filters_source).split(';;')
        self.setNameFilters(filters)
        if filters:self.selectNameFilter(filters[min(index,len(filters)-1)])
        for role,label in self._labels_source.items():self.setLabelText(role,display(label))
        if editor is not None:editor.setText(entered)

    @staticmethod
    def _choose(parent, caption, directory, filter, selectedFilter, options, saving):
        dialog = QFileDialog(parent,display(caption),directory,display(filter))
        dialog._caption_source=caption
        dialog._filters_source=filter
        dialog.setOptions(options | QFileDialog.Option.DontUseNativeDialog)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave if saving else QFileDialog.AcceptMode.AcceptOpen)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile if saving else QFileDialog.FileMode.ExistingFile)
        for role,label in ((QFileDialog.DialogLabel.LookIn,tx('位置：')),(QFileDialog.DialogLabel.FileName,tx('文件名：')),
                           (QFileDialog.DialogLabel.FileType,tx('文件类型：')),(QFileDialog.DialogLabel.Reject,tx('取消')),
                           (QFileDialog.DialogLabel.Accept,tx('保存') if saving else tx('打开'))):
            dialog._labels_source[role]=label
        dialog._translate_fields()
        if selectedFilter:
            dialog.selectNameFilter(display(selectedFilter))
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
