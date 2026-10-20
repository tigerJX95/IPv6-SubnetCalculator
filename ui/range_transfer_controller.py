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

"""安全地将地址范围或规划结果送入独立清单工作区。"""
from PyQt6.QtCore import QObject
from core.localized_text import text as tx
from ui.standard_dialogs import QMessageBox


class RangeTransferController(QObject):
    def __init__(self,window):
        super().__init__(window);self.window=window
        window.address_tools_page.range_panel.transfer_requested.connect(self.transfer)
        window.subnet_list_page.output_controller.transfer_requested.connect(self.transfer)

    def transfer(self,text,source=None):
        window=self.window;page=window.subnet_list_page
        if page.service.busy:
            window.feedback.set_message(tx('子网清单正在处理任务，请完成或取消后再发送。'),'info');return
        if source is not None and not source():
            window.feedback.set_message(tx('规划结果已变化，请重新计算后再发送。'),'info');return
        previous=page.editor.toPlainText()
        if previous.strip() and previous!=text:
            answer=QMessageBox.question(window,tx('替换子网清单'),
                (tx('将使用当前规划结果替换清单，并重新检查。是否继续？') if source is not None else tx('将使用地址范围转换结果替换当前清单，并重新检查。是否继续？')),
                QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
            if answer!=QMessageBox.StandardButton.Yes:return
        if page.service.busy or page.editor.toPlainText()!=previous or source is not None and not source():
            window.feedback.set_message(tx('子网清单状态已变化，请重新发送。'),'info');return
        page.editor.setPlainText(text)
        window.tabs.setCurrentWidget(page);page.result_tabs.setCurrentIndex(0);page.analyze()
