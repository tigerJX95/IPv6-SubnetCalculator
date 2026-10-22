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

"""双语全窗口审计及相反系统语言下的文件元数据回归。"""
import re,tempfile,unittest
from pathlib import Path
from time import monotonic
from unittest.mock import patch
from PyQt6.QtCore import Qt,QSettings,QCoreApplication,QEvent,QItemSelectionModel,QTimer
from PyQt6.QtGui import QFileSystemModel,QAction
from PyQt6.QtWidgets import QApplication,QLabel,QAbstractButton,QComboBox,QTabWidget,QLineEdit,QPlainTextEdit,QTreeView,QListView,QGroupBox,QTableView
from PyQt6.QtTest import QTest
from app import create_application
from core.localized_text import text as tx
from core.subnet_list import analyze_subnet_list
from core.subnet_planning import free_space,aggregate_cidrs
from services.language_service import display
from ui.file_dialog_model import LocalizedFileSystemModel
from ui.standard_dialogs import QFileDialog,QMessageBox
from ui.main_window import MainWindow
from ui.dialogs import RangeCopyDialog,SubnetDetailDialog,ExportRangeDialog,ExportProgressDialog


class OppositeSystemModel(QFileSystemModel):
    """Simulates native file-type strings independent of application language."""
    def data(self,index,role=Qt.ItemDataRole.DisplayRole):
        if index.column()==2 and role==Qt.ItemDataRole.DisplayRole:
            return 'File Folder' if self.isDir(index) else '中文系统文件类型'
        return super().data(index,role)


class LanguageAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.app=create_application([],QSettings(str(Path(cls.temp.name)/'prefs.ini'),QSettings.Format.IniFormat))
        cls.app.setQuitOnLastWindowClosed(False)

    @classmethod
    def tearDownClass(cls):
        cls.app.language_manager.apply('zh_CN',persist=False);cls.temp.cleanup()

    def setUp(self):
        self.app.language_manager.apply('zh_CN',persist=False)
        self.tmp=tempfile.TemporaryDirectory(prefix='i18n-audit-');self.root=Path(self.tmp.name)
        (self.root/'File Folder').mkdir()
        for suffix in ('txt','cidr','json','xlsx','zip','py','cmd','md','exe','dll','unknown'):(self.root/('example.'+suffix)).write_bytes(b'Hello world!')
        (self.root/'no_extension').write_bytes(b'hello')
        self.w=MainWindow();self.w.show();self.w.calculate()
        self.dialogs=[]

    def tearDown(self):
        self.w.subnet_list_page.project_controller.saved = self.w.subnet_list_page.project_controller.snapshot()
        for d in self.dialogs:d.close();d.deleteLater()
        self.app.language_manager.apply('zh_CN',persist=False)
        self.w.plan_controller.path=None;self.w.close();self.w.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);QApplication.processEvents();self.tmp.cleanup()

    def switch(self,language):
        self.app.language_manager.apply(language,persist=False);QApplication.processEvents()

    def wait(self,condition):
        deadline=monotonic()+5
        while monotonic()<deadline:
            QApplication.processEvents()
            if condition():return
            QTest.qWait(4)
        self.fail('Filesystem/dialog timeout')

    def no_chinese(self,value):
        self.assertNotRegex(value.replace('简体中文',''),r'[\u4e00-\u9fff：，。；、（）｜～]',repr(value))

    def audit_widgets(self,root,language):
        english={'Open','Save','Cancel','Close','Yes','No','Discard','Retry','Ignore','Abort','OK','Back','Forward','Undo','Redo','Cut','Copy','Paste','Delete','Rename','Name','Size','Type','Folder','Directory','Computer','Look in','File name','Files of type','New Folder','Parent Directory','List View','Detail View','Show hidden files','Select All'}
        for w in [root,*root.findChildren(QGroupBox),*root.findChildren(QLabel),*root.findChildren(QAbstractButton),*root.findChildren(QComboBox),*root.findChildren(QTabWidget),*root.findChildren(QLineEdit),*root.findChildren(QPlainTextEdit),*root.findChildren(QAction)]:
            strings=[]
            if not isinstance(w,QAction):strings.extend([w.windowTitle(),w.toolTip(),w.accessibleName(),w.accessibleDescription()])
            else:strings.extend([w.text(),w.toolTip()])
            if isinstance(w,QGroupBox):strings.append(w.title())
            if isinstance(w,(QLabel,QAbstractButton)):strings.append(w.text())
            if isinstance(w,(QLineEdit,QPlainTextEdit)):strings.append(w.placeholderText())
            if isinstance(w,QComboBox) and w.objectName()!='lookInCombo':strings.extend(w.itemText(i) for i in range(w.count()))
            if isinstance(w,QTabWidget):strings.extend(w.tabText(i) for i in range(w.count()))
            for value in strings:
                if language=='en_US':self.no_chinese(value)
                else:self.assertNotIn(value.replace('&','').strip().rstrip(':….'),english,repr(value))

        for view in root.findChildren(QTableView):
            model=view.model()
            if model is None:continue
            for column in range(model.columnCount()):
                value=model.headerData(column,Qt.Orientation.Horizontal)
                if language=='en_US' and value is not None:self.no_chinese(str(value))
            for row in range(min(model.rowCount(),3)):
                for column in range(model.columnCount()):
                    value=model.data(model.index(row,column))
                    if language=='en_US' and value is not None:self.no_chinese(str(value))

    def picker(self):
        d=QFileDialog(self.w);d.setViewMode(QFileDialog.ViewMode.Detail);d.setDirectory(str(self.root));d.show();self.dialogs.append(d)
        source=d.file_types.sourceModel()
        self.wait(lambda:source.index(str(self.root/'example.txt')).isValid())
        return d

    def model(self):
        d=QFileDialog(self.w);self.dialogs.append(d)
        source=OppositeSystemModel(d);source.setRootPath(str(self.root))
        proxy=LocalizedFileSystemModel(d);proxy.setSourceModel(source)
        self.wait(lambda:source.index(str(self.root/'example.txt')).isValid())
        return source,proxy

    def test_native_file_folder_is_chinese_and_name_stays_original(self):
        source,proxy=self.model();index=source.index(str(self.root/'File Folder'))
        self.assertEqual(source.data(index.siblingAtColumn(2)),'File Folder')
        self.assertEqual(proxy.data(proxy.mapFromSource(index.siblingAtColumn(2))),'文件夹')
        self.assertEqual(proxy.data(proxy.mapFromSource(index)),'File Folder')

    def test_opposite_chinese_os_file_types_do_not_leak_into_english(self):
        source,proxy=self.model();self.switch('en_US')
        for name in ('File Folder','example.txt','example.unknown','no_extension'):
            index=proxy.mapFromSource(source.index(str(self.root/name)).siblingAtColumn(2));self.no_chinese(proxy.data(index))
        index=proxy.mapFromSource(source.index(str(self.root/'File Folder')).siblingAtColumn(2));self.assertEqual(proxy.data(index),'Folder')

    def test_all_supported_file_type_labels_and_generic_fallback(self):
        source,proxy=self.model()
        labels={'txt':('文本文档','Text Document'),'cidr':('IPv6 CIDR 清单','IPv6 CIDR List'),'json':('JSON 文档','JSON Document'),'xlsx':('Excel 工作簿','Excel Workbook'),'zip':('ZIP 压缩文件','ZIP Archive'),'py':('Python 脚本','Python Script'),'cmd':('Windows 命令脚本','Windows Command Script'),'md':('Markdown 文档','Markdown Document'),'exe':('应用程序','Application'),'dll':('动态链接库','Dynamic Link Library'),'unknown':('UNKNOWN 文件','UNKNOWN File')}
        for language,n in [('zh_CN',0),('en_US',1),('zh_CN',0)]:
            self.switch(language)
            for suffix,expected in labels.items():
                index=proxy.mapFromSource(source.index(str(self.root/('example.'+suffix))).siblingAtColumn(2))
                self.assertEqual(proxy.data(index),expected[n]);self.assertEqual(proxy.data(index,Qt.ItemDataRole.ToolTipRole),expected[n])

    def test_headers_sizes_and_dates_follow_language(self):
        source,proxy=self.model();index=source.index(str(self.root/'example.txt'))
        for language,headers in [('zh_CN',['名称','大小','类型','修改日期']),('en_US',['Name','Size','Type','Date Modified'])]:
            self.switch(language)
            self.assertEqual([proxy.headerData(i,Qt.Orientation.Horizontal) for i in range(4)],headers)
            size=proxy.data(proxy.mapFromSource(index.siblingAtColumn(1)))
            self.assertIn('字节' if language=='zh_CN' else 'bytes',size)
            date=proxy.data(proxy.mapFromSource(index.siblingAtColumn(3)));self.assertTrue(date)
            if language=='en_US':self.no_chinese(date)

    def test_open_picker_live_switch_preserves_filename_directory_filter_and_selection(self):
        d=self.picker();d.setNameFilters(['Text (*.txt)','All (*)']);d.selectNameFilter('All (*)')
        source=d.file_types.sourceModel();idx=d.file_types.mapFromSource(source.index(str(self.root/'example.txt')))
        view=d.findChild(QTreeView,'treeView');view.selectionModel().setCurrentIndex(idx,QItemSelectionModel.SelectionFlag.ClearAndSelect|QItemSelectionModel.SelectionFlag.Rows)
        editor=d.findChild(QLineEdit,'fileNameEdit');editor.setText('用户输入.xlsx')
        selected=[i.data() for i in view.selectionModel().selectedRows()]
        notifications=[];d.file_types.dataChanged.connect(lambda *_:notifications.append(True))
        for language in ('en_US','zh_CN','en_US'):
            self.switch(language)
            self.assertEqual(editor.text(),'用户输入.xlsx');self.assertTrue(Path(d.directory().absolutePath()).samefile(self.root));self.assertEqual(d.selectedNameFilter(),'All (*)')
            self.assertEqual([i.data() for i in view.selectionModel().selectedRows()],selected)
        self.assertTrue(notifications)

    def test_proxy_preserves_paths_and_source_roles(self):
        source,proxy=self.model();original=source.index(str(self.root/'example.json'));mapped=proxy.mapFromSource(original)
        self.assertEqual(proxy.mapToSource(mapped),original)
        self.assertTrue(Path(proxy.data(mapped,QFileSystemModel.Roles.FilePathRole)).samefile(self.root/'example.json'))
        self.assertEqual(proxy.flags(mapped),source.flags(original))

    def test_all_production_file_dialog_entry_points_in_both_languages(self):
        captions=[tx('导出 IPv6 子网'),tx('保存计算方案'),tx('打开计算方案'),tx('导入 IPv6 CIDR 清单'),tx('保存清单或规划文本')]
        for language in ('zh_CN','en_US'):
            self.switch(language)
            def inspect(d):
                d.setDirectory(str(self.root));d.show();QApplication.processEvents();self.audit_widgets(d,language)
                self.assertIs(d.proxyModel(),d.file_types)
                return d.DialogCode.Rejected
            with patch.object(QFileDialog,'exec',inspect):
                for caption in captions:QFileDialog.getSaveFileName(self.w,caption,'output.txt',tx('文本文件 (*.txt)'))

    def test_file_dialog_existing_widgets_and_actions_retranslate_both_directions(self):
        def inspect(d):
            d.setDirectory(str(self.root));d.show();QApplication.processEvents()
            for language in ('en_US','zh_CN','en_US','zh_CN'):
                self.switch(language);self.audit_widgets(d,language)
            return d.DialogCode.Rejected
        with patch.object(QFileDialog,'exec',inspect):QFileDialog.getSaveFileName(self.w,tx('保存计算方案'),'IPv6Plan.json',tx('IPv6 计算方案 (*.json)'))

    def test_main_pages_and_all_tool_dialogs_both_directions(self):
        tools=self.w.address_tools_page;tools.convert();tools.analyze();tools.range_panel.convert()
        page=self.w.subnet_list_page;page.editor.setPlainText('::/127\n::2/127');page.set_analysis(analyze_subnet_list(page.editor.toPlainText()))
        page.planning.completed('free',('ok',free_space('::/127\n::2/127','::/124')));page.planning.completed('aggregate',('ok',aggregate_cidrs('::/127\n::2/127')))
        dialogs=[RangeCopyDialog(self.w.result,self.w.clipboard,parent=self.w),SubnetDetailDialog(self.w.result,1,self.w.clipboard,self.w),ExportRangeDialog(65536,self.w),ExportProgressDialog('output.xlsx',2**128,self.w)]
        for language in ('zh_CN','en_US','zh_CN','en_US'):
            self.switch(language);self.audit_widgets(self.w,language)
            for d in dialogs:self.audit_widgets(d,language)
        dialogs[-1].finish()
        for d in dialogs:d.deleteLater()

    def test_about_help_legal_and_component_overview_follow_language(self):
        self.w.show_about();a=self.w.about_dialog
        for language in ('zh_CN','en_US','zh_CN','en_US'):
            self.switch(language);a.license_selector.setCurrentIndex(0);self.audit_widgets(a,language)
            if language=='en_US':
                for view in (a.information,a.usage,a.legal,a.licenses):self.no_chinese(view.toPlainText())
                self.assertIn('Third-Party Components',a.licenses.toPlainText())
            else:self.assertIn('第三方组件',a.licenses.toPlainText())

    def test_license_originals_are_unchanged_in_both_languages(self):
        from app_info import resource_path
        from services.about_content import LICENSE_DOCUMENTS
        self.w.show_about();a=self.w.about_dialog
        for language in ('zh_CN','en_US'):
            self.switch(language)
            for index,(_,path) in enumerate(LICENSE_DOCUMENTS[1:],1):
                a.license_selector.setCurrentIndex(index)
                self.assertEqual(a.licenses.toPlainText().strip(),resource_path(path).read_text().strip())

    def test_dynamic_normalization_and_error_messages_use_english_punctuation(self):
        from core.subnet_planning import free_space
        tools=self.w.address_tools_page
        self.switch('en_US');tools.network_a_input.setText('2026:1015:abcd::1/48');tools.network_b_input.setText('2026:1015:abcd::2/64');tools.analyze()
        self.no_chinese(self.w.feedback.text());self.assertIn('A, B',self.w.feedback.text())
        try:free_space('bad\ninvalid','::/0')
        except Exception as exc:self.no_chinese(display(str(exc)))

    def test_standard_edit_context_menus_are_localized(self):
        fields=[self.w.calculation_page.network_input,self.w.address_tools_page.address_input,self.w.address_tools_page.range_panel.start_input,self.w.subnet_list_page.editor]
        for language in ('zh_CN','en_US','zh_CN'):
            self.switch(language)
            for field in fields:
                menu=field.createStandardContextMenu();self.audit_widgets(menu,language);menu.deleteLater()

    def test_standard_message_buttons_and_live_switches(self):
        errors=[]
        def inspect():
            box=QApplication.activeModalWidget()
            try:
                for language in ('en_US','zh_CN','en_US'):
                    self.switch(language);self.audit_widgets(box,language)
                    no=box.button(QMessageBox.StandardButton.No)
                    self.assertIs(box.defaultButton(),no)
            except Exception as exc:errors.append(exc)
            finally:box.button(QMessageBox.StandardButton.No).click()
        QTimer.singleShot(0,inspect)
        QMessageBox.question(self.w,tx('覆盖确认'),tx('文件已存在，是否覆盖？\n{0}','output.txt'))
        if errors:raise errors[0]

    def test_progress_status_and_cancellation_retranslate(self):
        d=ExportProgressDialog('output.xlsx',2**128,self.w)
        for language in ('zh_CN','en_US','zh_CN','en_US'):
            self.switch(language);d.set_progress(2**127,2**128);self.audit_widgets(d,language)
        d.request_cancel();self.no_chinese(d.count_label.text());self.switch('zh_CN');self.assertIn('取消',d.count_label.text());d.finish();d.deleteLater()

    def test_information_warning_and_unsaved_work_buttons(self):
        for language in ('zh_CN','en_US'):
            self.switch(language)
            for opener in (QMessageBox.information,QMessageBox.warning):
                errors=[]
                def inspect():
                    box=QApplication.activeModalWidget()
                    try:self.audit_widgets(box,language)
                    except Exception as exc:errors.append(exc)
                    finally:box.button(QMessageBox.StandardButton.Ok).click()
                QTimer.singleShot(0,inspect)
                opener(self.w,tx('格式错误'),tx('请输入 IPv6 地址。'))
                if errors:raise errors[0]
            errors=[]
            def inspect_unsaved():
                box=QApplication.activeModalWidget()
                try:
                    self.audit_widgets(box,language)
                    self.assertIs(box.defaultButton(),box.button(QMessageBox.StandardButton.Cancel))
                except Exception as exc:errors.append(exc)
                finally:box.button(QMessageBox.StandardButton.Cancel).click()
            QTimer.singleShot(0,inspect_unsaved)
            QMessageBox.question(self.w,tx('覆盖确认'),tx('请输入 IPv6 地址。'),
                QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Discard|QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Cancel)
            if errors:raise errors[0]

    def test_native_file_not_found_warning_is_localized(self):
        from PyQt6.QtWidgets import QMessageBox as NativeMessageBox
        for language in ('zh_CN','en_US'):
            self.switch(language);d=self.picker()
            d.setFileMode(QFileDialog.FileMode.ExistingFile);d.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
            QApplication.processEvents();d.findChild(QLineEdit,'fileNameEdit').setText('nonexistent.txt');QApplication.processEvents();errors=[];seen=[]
            def dismiss():
                box=QApplication.activeModalWidget()
                try:
                    self.assertIsInstance(box,NativeMessageBox)
                    self.audit_widgets(box,language);seen.append(True)
                except Exception as exc:errors.append(exc)
                finally:
                    if isinstance(box,NativeMessageBox):box.buttons()[0].click()
                    else:d.reject()
            QTimer.singleShot(20,dismiss);d.accept();QApplication.processEvents()
            self.wait(lambda:bool(seen or errors))
            d.close()
            if errors:raise errors[0]
            self.assertTrue(seen)

    def test_user_text_is_not_translated_as_ui_text(self):
        text='# 父网段：::/0\n# File Folder\n::/127'
        self.w.subnet_list_page.editor.setPlainText(text)
        self.w.calculation_page.plan_name_input.setText('父网段 File Folder')
        self.w.calculation_page.plan_notes_input.setPlainText('原始备注')
        for language in ('en_US','zh_CN','en_US'):
            self.switch(language);self.assertEqual(self.w.subnet_list_page.editor.toPlainText(),text)
            self.assertEqual(self.w.calculation_page.plan_name_input.text(),'父网段 File Folder');self.assertEqual(self.w.calculation_page.plan_notes_input.toPlainText(),'原始备注')
        self.w.calculation_page.plan_name_input.clear();self.w.calculation_page.plan_notes_input.clear()


if __name__=='__main__':unittest.main()
