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

"""Explicit planning-project save/load with snapshot and replacement protection."""
from pathlib import Path
from PyQt6.QtCore import Qt
from core.localized_text import text as tx
from core.planning_project import PlanningProject
from core.file_commit import capture_file
from core.ipv6_core import InputError
from services.project_storage import load_project, save_project
from services.error_messages import describe_error
from ui.standard_dialogs import QFileDialog, QMessageBox
from ui.localized_widgets import QLabel
from ui.widgets import IconButton
from PyQt6.QtWidgets import QHBoxLayout


class ProjectController:
    def __init__(self, page, layout):
        self.page = page
        self.path = None
        self.saved = None
        row = QHBoxLayout()
        self.open_button = IconButton('open_plan', tx('打开规划项目 JSON（清单、父网段及分配参数）'))
        self.save_button = IconButton('save_plan', tx('另存规划项目 JSON（保留清单原文及注释）'))
        self.label = QLabel(tx('规划项目：未保存'))
        self.label.setTextFormat(Qt.TextFormat.PlainText)
        self.label.setWordWrap(True)
        row.addWidget(self.open_button)
        row.addWidget(self.save_button)
        row.addWidget(self.label, 1)
        layout.insertLayout(0, row)
        self.open_button.clicked.connect(self.open)
        self.save_button.clicked.connect(self.save)
        for edit in (page.editor, page.planning.parent_input,
                     page.planning.allocation.prefix_input, page.planning.allocation.count_input):
            edit.textChanged.connect(self.refresh)
        page.result_tabs.currentChanged.connect(self.refresh)
        page.busy_changed.connect(self.refresh)

    def snapshot(self):
        p = self.page
        return PlanningProject(p.editor.toPlainText(), p.planning.parent_input.text(),
            p.planning.allocation.prefix_input.text(), p.planning.allocation.count_input.text(),
            p.result_tabs.currentIndex())

    def refresh(self, *_):
        self.open_button.setEnabled(not self.page.service.busy)
        self.save_button.setEnabled(not self.page.service.busy)
        if self.path is not None:
            self.label.setText(tx('规划项目：{0}{1}', self.path.name,
                tx('（有未保存更改）') if self.snapshot() != self.saved else ''))
            self.label.setToolTip(str(self.path))

    def error(self, exc):
        self.page.feedback.emit(tx('规划项目操作失败：{0}', describe_error(exc)), 'error')

    def save(self):
        if self.page.service.busy:
            return False
        before = self.snapshot()
        selected, _ = QFileDialog.getSaveFileName(self.page, tx('保存规划项目'),
            str(self.path) if self.path else 'IPv6Planning.json', tx('IPv6 规划项目 (*.json)'),
            options=QFileDialog.Option.DontConfirmOverwrite)
        if not selected:
            return False
        try:
            path = Path(selected)
            if not path.suffix:
                path = path.with_suffix('.json')
            if path.suffix.lower() != '.json':
                raise InputError(tx('方案文件扩展名须为 .json。'))
            expected = capture_file(path)
            if expected.exists and QMessageBox.question(self.page, tx('覆盖规划项目'),
                    tx('目标文件已存在，是否覆盖？'),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                return False
            if self.page.service.busy or before != self.snapshot():
                self.page.feedback.emit(tx('规划内容或任务状态已变化，请重新操作。'), 'info')
                return False
            save_project(path, before, expected=expected)
        except (OSError, InputError) as exc:
            self.error(exc)
            return False
        self.path, self.saved = path, before
        self.refresh()
        self.page.feedback.emit(tx('规划项目已保存。'), 'success')
        return True

    def open(self):
        if self.page.service.busy:
            return False
        before = self.snapshot()
        selected, _ = QFileDialog.getOpenFileName(self.page, tx('打开规划项目'), '', tx('IPv6 规划项目 (*.json)'))
        if not selected:
            return False
        try:
            load_project(selected)  # Reject damaged input before offering to replace work.
            if QMessageBox.question(self.page, tx('恢复规划项目'),
                    tx('恢复将替换当前清单和规划参数。请先保存需要保留的内容，是否继续？'),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                return False
            project = load_project(selected)  # Recheck after the nested dialog.
            if self.page.service.busy or before != self.snapshot():
                self.page.feedback.emit(tx('规划内容或任务状态已变化，请重新操作。'), 'info')
                return False
        except (OSError, InputError) as exc:
            self.error(exc)
            return False
        p = self.page
        p.editor.setPlainText(project.text)
        p.planning.parent_input.setText(project.parent)
        p.planning.allocation.prefix_input.setText(project.prefix)
        p.planning.allocation.count_input.setText(project.count)
        p._invalidate()
        p.result_tabs.setCurrentIndex(project.tab)
        self.path, self.saved = Path(selected), self.snapshot()
        self.refresh()
        self.page.feedback.emit(tx('规划项目已恢复；请重新检查清单或计算空闲空间，再生成分配建议。'), 'success')
        return True
