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

"""清单／规划的保存与回流入口；对话框后复核结果快照。"""
from pathlib import Path
from PyQt6.QtCore import QObject,pyqtSignal
from PyQt6.QtWidgets import QMenu,QToolButton
from core.localized_text import text as tx
from ui.localized_widgets import LanguageAction
from ui.standard_dialogs import QFileDialog,QMessageBox
from services.language_service import display
from services.text_output import save_text_atomic
from services.error_messages import describe_error


class ListOutputController(QObject):
    transfer_requested=pyqtSignal(str,object)

    def __init__(self,page):
        super().__init__(page);self.page=page;self.actions={}
        self._menu(page.save_button,[
            ('input',tx('保存原始输入为 TXT'),self.save_input),
            ('networks',tx('保存有效去重 CIDR 为 TXT'),self.save_networks),
            ('list_report',tx('保存检查报告为 TXT'),self.save_list_report)])
        p=page.planning
        for task,button in [('free',p.save_free_button),('aggregate',p.save_aggregate_button)]:
            self._menu(button,[
                (task+'_cidrs',tx('保存完整 CIDR 清单为 TXT'),lambda checked=False,task=task:self.save_planning(task)),
                (task+'_report',tx('保存规划报告为 TXT'),lambda checked=False,task=task:self.save_planning(task,report=True))])
        p.send_free_button.clicked.connect(lambda:self.send_planning('free'))
        p.send_aggregate_button.clicked.connect(lambda:self.send_planning('aggregate'))
        self.refresh()

    def _menu(self,button,entries):
        menu=QMenu(button);menu.setToolTipsVisible(True)
        for key,label,callback in entries:
            action=LanguageAction(menu);action.setText(label);action.setToolTip(label)
            action.triggered.connect(callback);menu.addAction(action);self.actions[key]=action
        button.setMenu(menu);button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

    def refresh(self):
        page=self.page;p=page.planning;ready=not page.service.busy
        analysis=page.analysis
        self.actions['input'].setEnabled(ready and bool(page.editor.toPlainText().strip()))
        self.actions['networks'].setEnabled(ready and analysis is not None and bool(analysis.unique_networks))
        self.actions['list_report'].setEnabled(ready and analysis is not None)
        page.save_button.setEnabled(any(self.actions[key].isEnabled() for key in ('input','networks','list_report')))
        for task,button,send in [('free',p.save_free_button,p.send_free_button),('aggregate',p.save_aggregate_button,p.send_aggregate_button)]:
            result=getattr(p,task+'_result')
            complete=result is not None and (task!='free' or result.complete)
            full=ready and complete and bool(result.cidrs)
            self.actions[task+'_cidrs'].setEnabled(full)
            self.actions[task+'_report'].setEnabled(ready and result is not None)
            button.setEnabled(ready and result is not None);send.setEnabled(full)

    def _current(self,owner,attribute,snapshot):
        return not self.page.service.busy and getattr(owner,attribute) is snapshot

    def save_input(self):
        page=self.page;text=page.editor.toPlainText()
        if not text.strip() or page.service.busy:return
        self._save('IPv6List_Input.txt',text,lambda:not page.service.busy and page.editor.toPlainText()==text)

    def save_networks(self):
        result=self.page.analysis
        if result is None or not result.unique_networks or self.page.service.busy:return
        self._save('IPv6List_CIDRs.txt',str(result.normalized_text())+'\n',lambda:self._current(self.page,'analysis',result))

    def save_list_report(self):
        result=self.page.analysis
        if result is None or self.page.service.busy:return
        self._save('IPv6List_Report.txt',result.as_text(),lambda:self._current(self.page,'analysis',result))

    def save_planning(self,task,report=False):
        p=self.page.planning;result=getattr(p,task+'_result')
        if result is None or self.page.service.busy:return
        if not report and (not result.cidrs or task=='free' and not result.complete):return
        filename=('IPv6_FreeSpace' if task=='free' else 'IPv6_Aggregation')+('_Report.txt' if report else '_CIDRs.txt')
        self._save(filename,result.as_text() if report else str(result.cidr_text())+'\n',lambda:self._current(p,task+'_result',result))

    def _save(self,filename,value,current):
        path,_=QFileDialog.getSaveFileName(self.page,tx('保存清单或规划文本'),filename,tx('文本文件 (*.txt)'),options=QFileDialog.Option.DontConfirmOverwrite)
        if not path:return
        destination=Path(path)
        if not destination.suffix:destination=destination.with_suffix('.txt')
        if destination.suffix.lower()!='.txt':
            self.page.feedback.emit(tx('请使用 .txt 扩展名保存文本文件。'),'error');return
        if not current():
            self.page.feedback.emit(tx('输入、结果或任务状态已变化，请重新选择保存。'),'info');return
        if destination.exists():
            answer=QMessageBox.question(self.page,tx('覆盖确认'),tx('文件已存在，是否覆盖？\n{0}',destination),
                QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
            if answer!=QMessageBox.StandardButton.Yes:return
        if not current():
            self.page.feedback.emit(tx('输入、结果或任务状态已变化，请重新选择保存。'),'info');return
        # 报告使用实际保存时的界面语言，原始输入和纯 CIDR 保留原文。
        try:save_text_atomic(destination,display(value))
        except Exception as exc:
            self.page.feedback.emit(tx('保存文本失败：')+describe_error(exc),'error');return
        self.page.feedback.emit(tx('文本已保存：{0}',destination),'success')

    def send_planning(self,task):
        p=self.page.planning;result=getattr(p,task+'_result')
        if result is None or self.page.service.busy or not result.cidrs or task=='free' and not result.complete:return
        self.transfer_requested.emit(str(result.cidr_text()),lambda:self._current(p,task+'_result',result))
