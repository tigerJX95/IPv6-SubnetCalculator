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

"""程序信息、离线帮助、许可证及法律说明的独立窗口。"""
from ui.localized_widgets import QLabel, QTabWidget, QComboBox, QTextBrowser
from core.localized_text import text as tx, join_text as jt
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDesktopServices, QColor, QPalette, QTextCursor, QTextCharFormat
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QApplication
from app_info import APP_NAME, APP_VERSION
from services.about_content import (HELP_DOCUMENT, LEGAL_DOCUMENT, LICENSE_DOCUMENTS,
                                    read_document, program_information)
from ui.dialogs import AppDialog
from ui.widgets import IconButton
from ui.theme import current_colors


class OfflineBrowser(QTextBrowser):
    """Display bundled text only; open HTTPS links exclusively on user action."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)
        self.setObjectName('AboutText')
        self._document_path=None
        self.anchorClicked.connect(self.open_link)
        language=getattr(QApplication.instance(),"language_manager",None)
        if language is not None:language.changed.connect(self._language_changed)
        self.setAccessibleName(tx('关于窗口内容，可选择并复制文本'))
        manager = getattr(QApplication.instance(), 'theme_manager', None)
        if manager is not None:
            manager.changed.connect(self._refresh_links)

    def _refresh_links(self, *_args):
        color = QColor(current_colors()['accent'])
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Link, color)
        palette.setColor(QPalette.ColorRole.LinkVisited, color)
        self.setPalette(palette)
        block = self.document().begin()
        while block.isValid():
            fragment_iterator = block.begin()
            while not fragment_iterator.atEnd():
                fragment = fragment_iterator.fragment()
                if fragment.isValid() and fragment.charFormat().isAnchor():
                    cursor = QTextCursor(self.document())
                    cursor.setPosition(fragment.position())
                    cursor.setPosition(fragment.position()+fragment.length(), QTextCursor.MoveMode.KeepAnchor)
                    style = QTextCharFormat()
                    style.setForeground(color)
                    cursor.mergeCharFormat(style)
                fragment_iterator += 1
            block = block.next()

    def loadResource(self, resource_type, url):
        # No automatic image, local-file or network resource requests.
        return None

    def open_link(self, url):
        if url.scheme().lower() == 'https' and url.host():
            if not QDesktopServices.openUrl(url):
                self.setToolTip(tx('无法打开系统浏览器，请复制链接后手动打开：')+url.toString())

    def _language_changed(self,*_args):
        if self._document_path is None:return
        v,h=self.verticalScrollBar().value(),self.horizontalScrollBar().value()
        self.display_document(self._document_path)
        self.verticalScrollBar().setValue(v)
        self.horizontalScrollBar().setValue(h)

    def display_document(self, relative):
        self._document_path=relative
        language=QApplication.instance().language_manager.name
        if language=='en_US' and relative in (HELP_DOCUMENT,LEGAL_DOCUMENT):
            relative=relative.replace('.md','_EN.md')
        try:
            text = read_document(relative)
        except RuntimeError as exc:
            self.setPlainText(str(exc))
            return
        if relative.endswith('.md'):
            self.setMarkdown(text)
        else:
            self.setPlainText(text)
        self._refresh_links()
        self.verticalScrollBar().setValue(0)
        self.horizontalScrollBar().setValue(0)


class AboutDialog(AppDialog):
    def __init__(self, parent=None):
        super().__init__(tx('关于 {0} V{1}', APP_NAME, APP_VERSION), parent)
        self.setObjectName('AboutDialog')
        self.setModal(False)
        self.setMinimumSize(680, 440)
        self.resize(820, 620)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 14)
        layout.setSpacing(10)
        title = QLabel(tx('{0}  V{1}', APP_NAME, APP_VERSION))
        title.setObjectName('AppTitle')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        subtitle = QLabel(tx('离线计算 · 使用帮助 · 开源许可'))
        subtitle.setObjectName('AppSubtitle')
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        self.tabs = QTabWidget()
        self.information = OfflineBrowser()
        self.information.setMarkdown(program_information())
        self.usage = OfflineBrowser()
        self.usage.display_document(HELP_DOCUMENT)
        self.licenses = OfflineBrowser()
        self.license_selector = QComboBox()
        self.license_selector.setAccessibleName(tx('选择许可文档'))
        self.license_selector.setToolTip(tx('选择组件概览或内置许可原文，无需联网'))
        for label, relative in LICENSE_DOCUMENTS:
            self.license_selector.addItem(label, relative)
        self.license_selector.currentIndexChanged.connect(self._load_license)
        license_page = QWidget()
        license_layout = QVBoxLayout(license_page)
        license_layout.setContentsMargins(12, 12, 12, 12)
        license_layout.addWidget(self.license_selector)
        license_layout.addWidget(self.licenses, 1)
        self.legal = OfflineBrowser()
        self.legal.display_document(LEGAL_DOCUMENT)
        for widget, label in ((self.information, tx('程序信息')), (self.usage, tx('使用说明')),
                              (license_page, tx('第三方许可')), (self.legal, tx('法律责任'))):
            self.tabs.addTab(widget, label)
        self._load_license()
        layout.addWidget(self.tabs, 1)
        footer = QHBoxLayout()
        hint = QLabel(tx('文本可选择复制 · Esc 关闭'))
        hint.setObjectName('Reference')
        footer.addWidget(hint)
        footer.addStretch()
        self.close_button = IconButton('close_small', tx('关闭关于窗口（Esc）'))
        self.close_button.clicked.connect(self.close)
        footer.addWidget(self.close_button)
        layout.addLayout(footer)

    def _load_license(self, *_args):
        self.licenses.display_document(self.license_selector.currentData())

    def showEvent(self, event):
        area = self.screen().availableGeometry()
        self.resize(min(self.width(), area.width()-24), min(self.height(), area.height()-60))
        super().showEvent(event)
