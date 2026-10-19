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

"""所有输入共用的错误边框、警示图标和编辑后清除逻辑。"""
from ui.localized_widgets import QLineEdit, LanguageAction
from PyQt6.QtWidgets import QStyle


def clear_invalid(widget):
    widget.setProperty('invalid', False)
    action = getattr(widget, '_input_error_action', None)
    if action is not None:
        action.setVisible(False)
    widget.setAccessibleDescription(getattr(widget,'_original_description',''))
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def bind_input(widget):
    if getattr(widget, '_error_bound', False):
        return
    widget._error_bound=True
    widget._original_description=widget.accessibleDescription()
    if hasattr(widget,'textChanged'):
        widget.textChanged.connect(lambda *_:clear_invalid(widget))


def mark_invalid(widget, message):
    bind_input(widget)
    widget.setProperty('invalid', True)
    widget.setAccessibleDescription(message)
    if isinstance(widget,QLineEdit):
        action=getattr(widget,'_input_error_action',None)
        if action is None:
            action=LanguageAction(widget)
            action.setIcon(widget.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning))
            widget.addAction(action,QLineEdit.ActionPosition.TrailingPosition)
            widget._input_error_action=action
        action.setToolTip(message)
        action.setVisible(True)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
