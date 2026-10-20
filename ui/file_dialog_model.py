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

"""文件列表展示跟随应用语言，避免平台返回的类型说明混入其他语言。"""
from PyQt6.QtCore import QIdentityProxyModel,Qt,QLocale
from PyQt6.QtWidgets import QApplication,QAbstractItemView
from core.localized_text import text as tx
from services.language_service import display


class LocalizedFileSystemModel(QIdentityProxyModel):
    """只改变展示元数据，保留源模型路径、索引、过滤、排序与文件操作。"""
    def __init__(self,dialog):
        super().__init__(dialog)
        self.dialog=dialog
        QApplication.instance().language_manager.changed.connect(self.retranslate)

    def headerData(self,section,orientation,role=Qt.ItemDataRole.DisplayRole):
        if orientation==Qt.Orientation.Horizontal and role==Qt.ItemDataRole.DisplayRole and 0<=section<4:
            return display((tx('名称'),tx('大小'),tx('类型'),tx('修改日期'))[section])
        return super().headerData(section,orientation,role)

    def data(self,index,role=Qt.ItemDataRole.DisplayRole):
        if index.isValid() and index.column() in (1,2,3) and role in (Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.ToolTipRole):
            source=self.sourceModel();original=self.mapToSource(index)
            info=source.fileInfo(original.siblingAtColumn(0))
            if index.column()==1:
                return '' if info.isDir() else QLocale().formattedDataSize(info.size())
            if index.column()==3:
                modified=info.lastModified()
                return QLocale().toString(modified,QLocale.FormatType.ShortFormat) if modified.isValid() else ''
            if info.isSymLink():return display(tx('快捷方式'))
            if info.isRoot():return display(tx('磁盘驱动器'))
            if info.isDir():return display(tx('文件夹'))
            suffix=info.suffix().lower()
            labels={'txt':tx('文本文档'),'cidr':tx('IPv6 CIDR 清单'),'json':tx('JSON 文档'),
                    'xlsx':tx('Excel 工作簿'),'zip':tx('ZIP 压缩文件'),'py':tx('Python 脚本'),
                    'cmd':tx('Windows 命令脚本'),'bat':tx('Windows 命令脚本'),'md':tx('Markdown 文档'),
                    'exe':tx('应用程序'),'dll':tx('动态链接库'),'lnk':tx('快捷方式')}
            return display(labels.get(suffix,tx('{0} 文件',suffix.upper()) if suffix else tx('文件')))
        return super().data(index,role)

    def retranslate(self,*_args):
        self.headerDataChanged.emit(Qt.Orientation.Horizontal,0,3)
        # 当前文件夹的视图收到展示更新，不重置模型或清空选择。
        parents=[]
        for view in self.dialog.findChildren(QAbstractItemView):
            if view.model() is self:
                parent=view.rootIndex()
                if parent not in parents:parents.append(parent)
        for parent in parents:
            count=self.rowCount(parent)
            if count:
                self.dataChanged.emit(self.index(0,1,parent),self.index(count-1,3,parent),
                    [Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.ToolTipRole])
