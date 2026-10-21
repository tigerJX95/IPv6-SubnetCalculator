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

"""方案文件对话框、快照与恢复协调；损坏文件不改变当前工作。"""
from core.localized_text import text as tx, join_text as jt
from pathlib import Path
from core.file_commit import capture_file
from ui.standard_dialogs import QFileDialog, QMessageBox
from PyQt6.QtCore import QSignalBlocker, QItemSelectionModel
from PyQt6.QtGui import QShortcut, QKeySequence
from services.error_messages import describe_error
from core.ipv6_core import InputError, calculate
from core.calculation_plan import CalculationPlan, plan_to_payload
from services.plan_storage import load_plan, save_plan
from ui.input_feedback import mark_invalid, clear_invalid


class PlanController:
    def __init__(self, window):
        self.window = window
        self.path = None
        self.saved_document = None
        page = window.calculation_page
        page.save_plan_button.clicked.connect(self.save)
        page.open_plan_button.clicked.connect(self.open)
        for field in (page.network_input, page.target_input, page.plan_name_input):
            field.textChanged.connect(self._status)
        page.plan_notes_input.textChanged.connect(self._status)
        self.shortcuts = []
        for sequence, callback in (('Ctrl+S', self.save), ('Ctrl+Shift+S', lambda: self.save(save_as=True)), ('Ctrl+O', self.open)):
            shortcut = QShortcut(QKeySequence(sequence), window)
            shortcut.activated.connect(callback)
            self.shortcuts.append(shortcut)

    def document(self):
        page = self.window.calculation_page
        return (page.network_input.text().strip().lower(), page.target_input.text().strip(),
                page.plan_name_input.text(), page.plan_notes_input.toPlainText())

    def snapshot(self):
        window = self.window
        if window.result is None:
            raise InputError(tx('请先完成一次有效计算，再保存方案。'))
        calculation = window.calculation_page
        network, prefix = calculation.parameters()
        requested = calculate(network, prefix, preview_limit=0)
        if (requested.network, requested.target_prefix) != (window.result.network, window.result.target_prefix):
            raise InputError(tx('输入参数已修改，请先重新计算后再保存方案。'))
        page = window.results_page
        plan = CalculationPlan(str(window.result.network), window.result.target_prefix,
            calculation.plan_name_input.text(), calculation.plan_notes_input.toPlainText(),
            page.page_size, page.page, page.locator_range, tuple(page.selected_indices()),
            window.tabs.currentIndex() if window.tabs.currentIndex()<3 else 0)
        plan_to_payload(plan)
        return plan

    def _error(self, action, exc):
        message = action+tx('失败：')+describe_error(exc)
        mark_invalid(self.window.calculation_page.plan_file_label,message)
        self.window.feedback.set_message(message, 'error')
        QMessageBox.warning(self.window, action+tx('失败'), message)

    def save(self, save_as=False):
        if self.window.export_service.busy:
            self.window.feedback.set_message(tx('请先完成或取消导出，再保存方案。'), 'info')
            return False
        try:
            plan = self.snapshot()
            document = self.document()
        except InputError as exc:
            self._error(tx('保存方案'), exc)
            return False
        if self.path is not None and not save_as:
            path = self.path
            try:expected=capture_file(path)
            except (OSError,InputError) as exc:
                self._error(tx('保存方案'),exc);return False
        else:
            selected, _ = QFileDialog.getSaveFileName(self.window, tx('保存计算方案'),
                str(self.path) if self.path else 'IPv6Plan.json', tx('IPv6 计算方案 (*.json)'),
                options=QFileDialog.Option.DontConfirmOverwrite)
            if not selected:
                return False
            path = Path(selected)
            if not path.suffix:
                path = path.with_suffix('.json')
            if path.suffix.lower() != '.json':
                self._error(tx('保存方案'), InputError(tx('方案文件扩展名须为 .json。')))
                return False
            try:expected=capture_file(path)
            except (OSError,InputError) as exc:
                self._error(tx('保存方案'),exc);return False
            if expected.exists and QMessageBox.question(self.window, tx('覆盖方案'),
                    tx('目标文件已存在，是否覆盖？'), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                return False
        if self.document()!=document or self.window.export_service.busy:
            self.window.feedback.set_message(tx('方案内容或任务状态已变化，请重新保存。'),'info');return False
        try:
            save_plan(path, plan,expected=expected)
        except (OSError, InputError) as exc:
            self._error(tx('保存方案'), exc)
            return False
        clear_invalid(self.window.calculation_page.plan_file_label)
        self.path = path
        self.saved_document = document
        self._status()
        self.window.feedback.set_message(tx('计算方案已保存。'), 'success')
        return True

    def confirm_discard(self):
        document = self.document()
        tracked = self.path is not None or bool(document[2].strip() or document[3].strip())
        if not tracked or document == self.saved_document:
            return True
        answer = QMessageBox.question(self.window, tx('未保存的方案'), tx('当前方案有未保存的更改，是否先保存？'),
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel)
        if answer == QMessageBox.StandardButton.Save:
            return self.save()
        return answer == QMessageBox.StandardButton.Discard

    def open(self):
        if self.window.export_service.busy:
            self.window.feedback.set_message(tx('请先完成或取消导出，再打开方案。'), 'info')
            return False
        selected, _ = QFileDialog.getOpenFileName(self.window, tx('打开计算方案'), '', tx('IPv6 计算方案 (*.json)'))
        if not selected:
            return False
        return self.open_path(selected)

    def open_path(self, selected, *, dropped=False):
        if self.window.export_service.busy or (dropped and self.window.subnet_list_page.service.busy):
            self.window.feedback.set_message(tx('请先完成或取消后台任务，再打开方案。'), 'info')
            return False
        try:
            plan = load_plan(selected)
        except (OSError, InputError) as exc:
            self._error(tx('打开方案'), exc)
            return False
        document = self.document()
        tracked = self.path is not None or bool(document[2].strip() or document[3].strip())
        dirty = tracked and document != self.saved_document
        if not self.confirm_discard():
            return False
        if dropped and not dirty and QMessageBox.question(self.window,tx('替换当前计算方案'),
                tx('方案校验通过。是否用拖入的方案替换当前计算参数、结果和浏览位置？'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return False
        # 确认期间可能先保存到同一个路径，或文件被外部程序修改。
        # 重新校验实际将恢复的内容，避免把旧快照误标为已保存。
        try:
            plan = load_plan(selected)
        except (OSError, InputError) as exc:
            self._error(tx('打开方案'), exc)
            return False
        self.apply(plan)
        self.path = Path(selected)
        self.saved_document = self.document()
        self._status()
        self.window.feedback.set_message(tx('计算方案已恢复。'), 'success')
        return True

    def apply(self, plan):
        plan_to_payload(plan)
        clear_invalid(self.window.calculation_page.plan_file_label)
        for field in (self.window.calculation_page.network_input,self.window.calculation_page.target_input):
            clear_invalid(field)
        result = calculate(plan.network, str(plan.target_prefix), preview_limit=0)
        window, page = self.window, self.window.results_page
        calculation = window.calculation_page
        calculation.network_input.setText(plan.network)
        calculation.target_input.setText(str(plan.target_prefix))
        calculation.plan_name_input.setText(plan.name)
        calculation.plan_notes_input.setPlainText(plan.notes)
        window.result = result
        calculation.set_result(result)
        with QSignalBlocker(page.page_size_combo):
            page.page_size_combo.setCurrentIndex(page.page_size_combo.findData(plan.page_size))
        page.set_result(result)
        if plan.locator_range is not None:
            page.locator_mode_combo.setCurrentIndex(3)
            page.locator_input.setText(tx('{0}-{1}', plan.locator_range[0], plan.locator_range[1]))
        else:
            page.locator_input.clear()
        page.locator_range = plan.locator_range
        page.show_page(plan.page)
        selection = page.table.selectionModel()
        for number in plan.selected_indices:
            index = page.model.index(number-1-(plan.page-1)*plan.page_size, 0)
            selection.select(index, QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)
        if plan.selected_indices:
            first = page.model.index(plan.selected_indices[0]-1-(plan.page-1)*plan.page_size, 0)
            selection.setCurrentIndex(first, QItemSelectionModel.SelectionFlag.NoUpdate)
            page.table.scrollTo(first)
        page.refresh_statistics()
        window.tabs.setCurrentIndex(plan.tab)

    def _status(self):
        label = self.window.calculation_page.plan_file_label
        clear_invalid(label)
        document = self.document()
        tracked = self.path is not None or bool(document[2].strip() or document[3].strip())
        modified = tracked and document != self.saved_document
        label.setText(tx('方案文件：')+(self.path.name if self.path else tx('未保存'))+(tx('（有未保存更改）') if modified else ''))
        label.setToolTip(str(self.path) if self.path else tx('使用保存图标或 Ctrl+S 将计算方案保存为 JSON。'))
