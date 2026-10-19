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

"""窗口内文件拖放只导入单个本地方案；文本编辑拖放保持原行为。"""
from core.localized_text import text as tx, join_text as jt
from pathlib import Path
from PyQt6.QtCore import QObject, QEvent, QTimer, Qt
from PyQt6.QtWidgets import QApplication, QWidget
from core.ipv6_core import InputError


class PlanDropController(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window=window
        self.pending_urls=[]
        self.timer=QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._import_pending)
        window.setAcceptDrops(True)
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, watched, event):
        if (event.type() not in (QEvent.Type.DragEnter,QEvent.Type.DragMove,QEvent.Type.Drop)
                or not isinstance(watched,QWidget) or watched.window() is not self.window
                or not event.mimeData().hasUrls()):
            return False
        if not event.possibleActions() & Qt.DropAction.CopyAction:
            event.ignore()
            return True
        event.setDropAction(Qt.DropAction.CopyAction)
        event.accept()
        if event.type()==QEvent.Type.Drop:
            self.pending_urls=list(event.mimeData().urls())
            # 定时器归属窗口；退出时不留下访问已销毁控件的回调。
            self.timer.start(0)
        return True

    def _import_pending(self):
        urls,self.pending_urls=self.pending_urls,[]
        if self.window.isVisible():
            self.import_urls(urls)

    def import_urls(self, urls):
        try:
            if len(urls)!=1:
                raise InputError(tx('一次只能拖入一个计算方案文件。'))
            if not urls[0].isLocalFile():
                raise InputError(tx('只支持本地计算方案文件，不支持网络链接。'))
            path=Path(urls[0].toLocalFile())
            if not path.is_file():
                raise InputError(tx('请拖入一个现有文件，不支持文件夹。'))
            if path.suffix.lower()!='.json':
                raise InputError(tx('拖放仅支持 .json 计算方案；TXT／CIDR 请在子网清单页导入。'))
        except InputError as exc:
            self.window.plan_controller._error(tx('导入方案'),exc)
            return False
        return self.window.plan_controller.open_path(path,dropped=True)
