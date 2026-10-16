"""IPv6 子网计算器图形界面。"""
from __future__ import annotations
import shutil
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from ipv6_core import calculate, InputError, locate_subnet
from subnet_export import XLSX_MAX_RECORDS, ExportCancelled, export_all, page_subnets
from export_estimate import estimate_export_range, format_size_range


class Tooltip:
    def __init__(self, widget, text):
        self.widget, self.text, self.popup = widget, text, None
        widget.bind('<Enter>', self.show, add='+')
        widget.bind('<Leave>', self.hide, add='+')
        widget.bind('<ButtonPress>', self.hide, add='+')
        widget.bind('<Destroy>', self.hide, add='+')

    def show(self, _=None):
        if self.popup:
            return
        top = tk.Toplevel(self.widget)
        top.overrideredirect(True)
        top.attributes('-topmost', True)
        top.geometry(f'+{self.widget.winfo_rootx()+12}+{self.widget.winfo_rooty()+self.widget.winfo_height()+4}')
        tk.Label(top, text=self.text, justify='left', bg='#fff7d5', fg='#233850',
                 font=('Microsoft YaHei UI', 10), padx=10, pady=7, relief='solid', bd=1).pack()
        self.popup = top

    def hide(self, _=None):
        if self.popup:
            self.popup.destroy()
            self.popup = None


def determine_export_format(path: Path, oversized: bool) -> str:
    """校验另存为窗口选择的格式，禁止静默截断结果。"""
    suffix = path.suffix.lower()
    if suffix not in ('.xlsx', '.txt'):
        raise ValueError('请选择 Excel（.xlsx）或 TXT（.txt）格式保存。')
    if oversized and suffix != '.txt':
        raise ValueError('当前子网数量超过 Excel 容量限制，只能导出 TXT（.txt）。')
    return suffix[1:]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('IPv6 子网计算器 V0.2')
        self.geometry('1080x830')
        self.minsize(900, 710)
        icon = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'app.ico'
        if icon.exists():
            try: self.iconbitmap(str(icon))
            except tk.TclError: pass
        self.result = None
        self.page = 1
        self.export_stop = None
        self.export_thread = None
        self._button_images = {}
        self._create_ui()
        self.protocol('WM_DELETE_WINDOW', self.on_close)

    def _icon_button(self, parent, name, tooltip, command):
        """统一浅色线性图标，并为未来深色主题预留独立素材。"""
        root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'assets'
        if name not in self._button_images:
            self._button_images[name] = {
                state: tk.PhotoImage(file=str(root / f'{name}_{state}.png'))
                for state in ('normal', 'hover', 'disabled')
            }
        artwork = self._button_images[name]
        button = tk.Button(parent, image=artwork['normal'], command=command,
                           relief='flat', bd=0, padx=0, pady=0,
                           bg='#f0f0f0', activebackground='#f0f0f0',
                           highlightthickness=0, cursor='hand2',
                           disabledforeground='#AAB7C3')
        button.bind('<Enter>', lambda e: button.configure(image=artwork['hover'])
                    if str(button.cget('state')) == 'normal' else None, add='+')
        button.bind('<Leave>', lambda e: button.configure(image=artwork['normal'])
                    if str(button.cget('state')) == 'normal' else None, add='+')
        Tooltip(button, tooltip)
        return button

    def _set_button_state(self, button, enabled, name):
        state = 'normal' if enabled else 'disabled'
        button.configure(state=state, image=self._button_images[name]['normal' if enabled else 'disabled'])

    def _create_ui(self):
        sty = ttk.Style(self)
        if 'vista' in sty.theme_names(): sty.theme_use('vista')
        sty.configure('.', font=('Microsoft YaHei UI', 11))
        sty.configure('Title.TLabel', font=('Microsoft YaHei UI', 22, 'bold'))
        sty.configure('Hint.TLabel', font=('Microsoft YaHei UI', 11), foreground='#17659a')
        sty.configure('Warn.TLabel', font=('Microsoft YaHei UI', 11, 'bold'), foreground='#b42318')
        sty.configure('Success.TLabel', font=('Microsoft YaHei UI', 11, 'bold'), foreground='#137547')
        sty.configure('Result.TLabel', font=('Consolas', 12, 'bold'))
        sty.configure('Treeview', font=('Consolas', 12), rowheight=30)
        sty.configure('Treeview.Heading', font=('Microsoft YaHei UI', 11, 'bold'))
        base = ttk.Frame(self, padding=17)
        base.pack(fill='both', expand=True)
        ttk.Label(base, text='IPv6 子网计算器', style='Title.TLabel', anchor='center').pack(fill='x')
        ttk.Label(base, text='网络范围 · 子网划分 · 容量计算', style='Hint.TLabel', anchor='center').pack(fill='x', pady=(1, 12))
        form = ttk.LabelFrame(base, text='计算参数', padding=12)
        form.pack(fill='x')
        form.columnconfigure(0, weight=4)
        form.columnconfigure(1, weight=1)
        ttk.Label(form, text='IPv6 网络地址及前缀').grid(row=0, column=0, sticky='w')
        ttk.Label(form, text='目标子网前缀').grid(row=0, column=1, sticky='w')
        self.net = tk.StringVar(value='2026:1015:abcd::/48')
        self.target = tk.StringVar(value='64')
        net_entry = ttk.Entry(form, textvariable=self.net, font=('Consolas', 13, 'bold'))
        net_entry.grid(row=1, column=0, sticky='ew', padx=(0, 12), pady=(5, 8))
        prefix_entry = ttk.Entry(form, textvariable=self.target, font=('Consolas', 13, 'bold'))
        prefix_entry.grid(row=1, column=1, sticky='ew', pady=(5, 8))
        Tooltip(prefix_entry, '目标前缀：0～128，且不得小于原网络前缀。')
        self._icon_button(form, 'calculate', '开始计算 IPv6 子网', self.calculate).grid(row=2, column=0, sticky='w')
        net_entry.bind('<Return>', lambda _: self.calculate())
        prefix_entry.bind('<Return>', lambda _: self.calculate())
        self.status = tk.StringVar(value='输入参数后点击“开始计算”。')
        self.status_label = ttk.Label(base, textvariable=self.status, style='Hint.TLabel')
        self.status_label.pack(fill='x', pady=(9, 6))
        summary = ttk.LabelFrame(base, text='网络计算摘要', padding=9)
        summary.pack(fill='x', pady=(0, 10))
        summary.columnconfigure(1, weight=1)
        self.fields = {}
        for row, (title, key) in enumerate((('网络地址', 'network'), ('网络起始地址', 'start'),
                                            ('网络结束地址', 'end'), ('可划分子网数', 'count'),
                                            ('每个子网地址数', 'capacity'))):
            ttk.Label(summary, text=title + '：').grid(row=row, column=0, sticky='w', pady=2)
            var = tk.StringVar(value='—')
            self.fields[key] = var
            ttk.Label(summary, textvariable=var, style='Result.TLabel').grid(row=row, column=1, sticky='w', pady=2)
        results = ttk.LabelFrame(base, text='子网结果列表', padding=8)
        results.pack(fill='both', expand=True)
        results.columnconfigure(0, weight=1)
        results.rowconfigure(1, weight=1)
        self.table = ttk.Treeview(results, columns=('num','subnet'), show='headings', selectmode='extended')
        self.table.heading('num', text='序号')
        self.table.heading('subnet', text='IPv6 子网')
        self.table.column('num', width=115, minwidth=90, anchor='center', stretch=False)
        self.table.column('subnet', width=700, anchor='center')
        self.table.grid(row=1, column=0, sticky='nsew')
        bar = ttk.Scrollbar(results, orient='vertical', command=self.table.yview)
        bar.grid(row=1, column=1, sticky='ns')
        self.table.configure(yscrollcommand=bar.set)
        self.table.bind('<Control-c>', self._key_copy)
        self.table.bind('<Control-a>', self._key_select_all)
        self.table.bind('<Control-A>', self._key_select_all)
        paging = ttk.Frame(results)
        paging.grid(row=2, column=0, sticky='ew', pady=(7, 0))
        self.nav_buttons = []
        for name, tip, callback in (
            ('first', '首页', lambda: self.show_page(1)),
            ('previous', '上一页', lambda: self.show_page(self.page-1)),
            ('next', '下一页', lambda: self.show_page(self.page+1)),
            ('last', '末页', self.show_last)):
            btn = self._icon_button(paging, name, tip, callback)
            btn.pack(side='left', padx=(0, 6))
            self.nav_buttons.append(btn)
        ttk.Label(paging, text='页码：').pack(side='left', padx=(12, 4))
        self.page_entry = tk.StringVar(value='1')
        self.jump_input = ttk.Entry(paging, textvariable=self.page_entry, width=11)
        self.jump_input.pack(side='left')
        self.jump_input.bind('<Return>', lambda _: self.jump())
        self.jump_button = self._icon_button(paging, 'jump', '跳转到指定页码', self.jump)
        self.jump_button.pack(side='left', padx=6)
        # 分页信息放在列表右下角，与翻页按钮保持同一行。
        page_info = ttk.Frame(paging)
        page_info.pack(side='right', padx=(12, 0))
        ttk.Label(page_info, text='每页显示：').pack(side='left')
        self.size = tk.StringVar(value='100')
        size_combo = ttk.Combobox(page_info, textvariable=self.size,
                                  values=('25', '50', '100', '200'),
                                  state='readonly', width=5)
        size_combo.pack(side='left', padx=(0, 10))
        size_combo.bind('<<ComboboxSelected>>', lambda _: self.change_size())
        self.page_status = tk.StringVar(value='暂无计算结果')
        ttk.Label(page_info, textvariable=self.page_status,
                  style='Hint.TLabel').pack(side='left')
        footer = ttk.Frame(results)
        footer.grid(row=0, column=0, sticky='ew', pady=(0, 6))
        self.copy_selected_button = self._icon_button(footer, 'copy', '复制选中的子网（Ctrl+C）', self.copy_selected)
        self.copy_selected_button.pack(side='left', padx=(0, 7))
        self.copy_page_button = self._icon_button(footer, 'copy_page', '复制当前页全部子网（点击直接复制，无需先选中）', self.copy_page)
        self.copy_page_button.pack(side='left')
        self.export_button = self._icon_button(footer, 'export',
            '导出全部子网或指定序号范围（TXT / Excel）。\nExcel 最多 1,048,575 条；超出可确认改为 TXT。\n超大导出可能占用大量磁盘空间和时间。',
            self.request_export)
        self.export_button.pack(side='right')
        locator = ttk.Frame(results)
        locator.grid(row=3, column=0, sticky='ew', pady=(8, 0))
        ttk.Label(locator, text='地址定位：').pack(side='left')
        self.locate_address = tk.StringVar()
        self.locate_entry = ttk.Entry(locator, textvariable=self.locate_address,
                                      font=('Consolas', 11), width=40)
        self.locate_entry.pack(side='left', padx=(4, 7), fill='x', expand=True)
        Tooltip(self.locate_entry, '输入当前网络中的任意 IPv6 地址，定位并选中其所属子网。')
        self.locate_entry.bind('<Return>', lambda _: self.locate())
        self.locate_button = ttk.Button(locator, text='定位所属子网', command=self.locate)
        self.locate_button.pack(side='left')
        Tooltip(self.locate_button, '直接跳转至该地址所在的子网及页面，不逐条搜索。')
        self._set_locator_state(False)
        self.table.tag_configure('even', background='#FFFFFF')
        self.table.tag_configure('odd', background='#EDF4FA')
        self._update_nav()
        self._set_button_state(self.export_button, False, 'export')

    def _set_locator_state(self, enabled):
        state = 'normal' if enabled else 'disabled'
        self.locate_entry.configure(state=state)
        self.locate_button.configure(state=state)

    def locate(self):
        if not self.result:
            return
        try:
            index = locate_subnet(self.result.network, self.result.target_prefix, self.locate_address.get())
        except InputError as exc:
            messagebox.showwarning('定位失败', str(exc), parent=self)
            return
        page = (index - 1) // int(self.size.get()) + 1
        self.show_page(page)
        for item in self.table.get_children():
            if int(self.table.item(item, 'values')[0]) == index:
                self.table.selection_set(item)
                self.table.focus(item)
                self.table.see(item)
                break
        self.status.set(f'定位成功：第 {index:,} 个子网。')
        self.status_label.configure(style='Success.TLabel')

    def _choose_export_range(self, total):
        """选择全部导出或按一基序号选择闭区间。"""
        dlg = tk.Toplevel(self)
        dlg.title('选择子网导出范围')
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()
        frame = ttk.Frame(dlg, padding=18)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text=f'本次计算共有 {total:,} 个子网。').pack(anchor='w', pady=(0, 10))
        mode = tk.StringVar(value='all')
        ttk.Radiobutton(frame, text='导出全部子网', variable=mode, value='all').pack(anchor='w')
        ttk.Radiobutton(frame, text='按序号范围导出（含起止项）', variable=mode, value='range').pack(anchor='w', pady=(8, 4))
        inputs = ttk.Frame(frame)
        inputs.pack(fill='x', pady=(3, 11))
        ttk.Label(inputs, text='起始序号：').grid(row=0, column=0)
        start_var = tk.StringVar(value='1')
        start_entry = ttk.Entry(inputs, textvariable=start_var, width=18)
        start_entry.grid(row=0, column=1, padx=(0, 10))
        ttk.Label(inputs, text='结束序号：').grid(row=0, column=2)
        end_var = tk.StringVar(value=str(min(total, 1000)))
        end_entry = ttk.Entry(inputs, textvariable=end_var, width=18)
        end_entry.grid(row=0, column=3)
        Tooltip(start_entry, '输入子网序号，最小为 1。')
        Tooltip(end_entry, f'输入子网序号，最大为 {total:,}，包含此项。')
        chosen = []
        def update(*_):
            state = 'normal' if mode.get() == 'range' else 'disabled'
            start_entry.configure(state=state)
            end_entry.configure(state=state)
        mode.trace_add('write', update)
        update()
        def accept():
            if mode.get() == 'all':
                chosen.append((1, total))
            else:
                a, b = start_var.get().strip(), end_var.get().strip()
                if (not a.isascii() or not b.isascii() or not a.isdecimal() or
                    not b.isdecimal() or len(a) > 42 or len(b) > 42 or
                    not 1 <= int(a) <= int(b) <= total):
                    messagebox.showwarning('导出范围错误', f'请输入 1～{total:,} 之间的有效起止序号，且起始序号不得大于结束序号。', parent=dlg)
                    return
                chosen.append((int(a), int(b)))
            dlg.destroy()
        actions = ttk.Frame(frame)
        actions.pack(fill='x')
        ttk.Button(actions, text='取消', command=dlg.destroy).pack(side='right')
        ttk.Button(actions, text='确定', command=accept).pack(side='right', padx=(0, 10))
        dlg.protocol('WM_DELETE_WINDOW', dlg.destroy)
        dlg.bind('<Return>', lambda _: accept())
        self.wait_window(dlg)
        return chosen[0] if chosen else None

    def _total_pages(self):
        if not self.result: return 0
        n = int(self.size.get())
        return (self.result.subnet_count+n-1)//n

    def _update_nav(self):
        last = self._total_pages()
        enabled = [self.result is not None and self.page>1,
                   self.result is not None and self.page>1,
                   self.result is not None and self.page<last,
                   self.result is not None and self.page<last]
        for btn, name, can in zip(self.nav_buttons, ('first','previous','next','last'), enabled):
            self._set_button_state(btn, can, name)
        self._set_button_state(self.jump_button, bool(last), 'jump')
        state = 'normal' if last else 'disabled'
        self._set_button_state(self.copy_selected_button, bool(last), 'copy')
        self._set_button_state(self.copy_page_button, bool(last), 'copy_page')
        if not (self.export_thread and self.export_thread.is_alive()):
            self._set_button_state(self.export_button, bool(last), 'export')

    def calculate(self):
        if self.export_thread and self.export_thread.is_alive():
            messagebox.showwarning('提示', '请先完成或取消导出。', parent=self)
            return
        self.result = None
        self._set_locator_state(False)
        self.table.delete(*self.table.get_children())
        for field in self.fields.values(): field.set('—')
        self.page_status.set('暂无计算结果')
        try: self.result = calculate(self.net.get(), self.target.get(), preview_limit=0)
        except InputError as err:
            self.status.set('输入错误：'+str(err))
            self.status_label.configure(style='Warn.TLabel')
            self._update_nav()
            return
        r = self.result
        for k, v in dict(network=str(r.network), start=str(r.start_address), end=str(r.end_address),
                         count=f'{r.subnet_count:,}', capacity=f'{r.addresses_per_subnet:,}').items():
            self.fields[k].set(v)
        self.status.set('输入地址已规范化到所属网络。' if r.normalized else '计算完成。')
        self.status_label.configure(style='Success.TLabel')
        self.show_page(1)
        self._set_locator_state(True)

    def show_page(self, page):
        if not self.result or not 1 <= page <= self._total_pages(): return
        self.page = page
        self.page_entry.set(str(page))
        data = page_subnets(self.result.network, self.result.target_prefix, page, int(self.size.get()))
        self.table.delete(*self.table.get_children())
        for index, subnet in data:
            self.table.insert('', 'end', values=(str(index), subnet),
                              tags=('even' if index % 2 else 'odd',))
        self.page_status.set(f'共 {self.result.subnet_count:,} 项 · 第 {page:,} / {self._total_pages():,} 页')
        self._update_nav()

    def show_last(self): self.show_page(self._total_pages())

    def change_size(self): self.show_page(1)

    def jump(self):
        s = self.page_entry.get().strip()
        if not s.isascii() or not s.isdecimal() or len(s) > 42 or not 1 <= int(s) <= self._total_pages():
            messagebox.showwarning('页码错误', f'请输入 1 至 {self._total_pages():,} 之间的页码。', parent=self)
            self.page_entry.set(str(self.page))
            return
        self.show_page(int(s))

    def _key_select_all(self, _event=None):
        """选中当前页全部子网，不生成其他页面的数据。"""
        items = self.table.get_children()
        if items:
            self.table.selection_set(items)
        return 'break'

    def _key_copy(self, _event=None):
        if self.table.selection():
            self.copy_selected()
        return 'break'

    def copy_selected(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showinfo('提示', '请先选中子网。', parent=self); return
        self._copy([self.table.item(item, 'values')[1] for item in selected])

    def copy_page(self):
        if not self.result: return
        self._copy([self.table.item(item, 'values')[1] for item in self.table.get_children()])

    def _copy(self, lines):
        self.clipboard_clear()
        self.clipboard_append('\n'.join(lines))
        self.update_idletasks()
        self.status.set(f'已复制 {len(lines)} 个子网。')
        self.status_label.configure(style='Success.TLabel')

    def request_export(self):
        if not self.result or (self.export_thread and self.export_thread.is_alive()):
            return
        r = self.result
        span = self._choose_export_range(r.subnet_count)
        if span is None:
            return
        start, end = span
        count = end - start + 1
        oversized = count > XLSX_MAX_RECORDS
        if oversized and not messagebox.askyesno(
            '超出 Excel 限制',
            f'本次选中的 {count:,} 个子网超出 Excel 单工作表最多 '
            f'{XLSX_MAX_RECORDS:,} 条的限制。\n\n'
            '如需继续保存选定范围，只能使用 TXT 格式。是否继续？',
            parent=self
        ):
            return

        # Windows 另存为窗口允许用户直接选择文件类型。
        # 由于界面组件只返回路径而不返回选中的筛选器，需要根据
        # 最终扩展名识别格式，并在写入前完成校验。
        filters = [('文本文件 (*.txt)', '*.txt')] if oversized else [
            ('Excel 工作簿 (*.xlsx)', '*.xlsx'),
            ('文本文件 (*.txt)', '*.txt'),
        ]
        default_format = 'txt' if oversized else 'xlsx'
        selected = filedialog.asksaveasfilename(
            parent=self,
            title='导出 IPv6 子网',
            defaultextension='.' + default_format,
            filetypes=filters,
            initialfile='IPv6Subnets.' + default_format,
        )
        if not selected:
            return
        path = Path(selected)
        try:
            fmt = determine_export_format(path, oversized)
        except ValueError as err:
            messagebox.showerror('格式错误', str(err), parent=self)
            return

        lower, upper = estimate_export_range(r.network, r.target_prefix, fmt, count, start - 1)
        disk_hint = format_size_range(lower, upper)
        if count > 100_000:
            if not messagebox.askyesno('确认完整导出',
                f'将导出序号 {start:,}～{end:,}，共 {count:,} 个子网。\n'
                f'预计占用磁盘空间约 {disk_hint}（范围估算），\n'
                '实际大小取决于地址长度、压缩格式及文件内容。\n'
                '数据量较大，导出可能耗时较长。\n\n是否继续导出？',
                parent=self):
                return
        if path.exists() and not messagebox.askyesno(
            '覆盖确认', f'文件已存在，是否覆盖？\n{path}', parent=self
        ):
            return
        try:
            usage = shutil.disk_usage(path.parent)
            # 额外预留少量磁盘空间，不计入显示的容量估算。
            reserve = max(256 * 1024**2, usage.total // 100)
            required = upper + reserve
            if required > usage.free and not messagebox.askyesno(
                '磁盘空间提醒',
                f'可用空间约 {usage.free/1024**3:.2f} GiB。\n'
                f'预计文件大小约 {disk_hint}，另需预留安全空间。\n'
                '磁盘空间可能不足，是否仍尝试导出？',
                parent=self
            ):
                return
        except OSError:
            pass
        self._start_export(path, fmt, r, start, end)

    def _start_export(self, path, fmt, result, start, end):
        self.export_stop = threading.Event()
        self.progress_dialog = tk.Toplevel(self)
        dialog = self.progress_dialog
        dialog.title('正在导出子网')
        dialog.geometry('520x190')
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        frame=ttk.Frame(dialog, padding=18)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text=f'正在导出至：{path.name}').pack(anchor='w')
        self.export_label=tk.StringVar(value=f'0 / {end-start+1:,} 项 (0.00%)')
        ttk.Label(frame, textvariable=self.export_label).pack(anchor='w', pady=(12, 8))
        self.progress=ttk.Progressbar(frame, mode='determinate', maximum=10000)
        self.progress.pack(fill='x')
        ttk.Button(frame, text='取消导出', command=self.cancel_export).pack(pady=(12, 0))
        dialog.protocol('WM_DELETE_WINDOW', self.cancel_export)
        self._set_button_state(self.export_button, False, 'export')
        def update(done, total):
            # 工作线程仅写入同步数据结构，不直接操作界面组件。
            with self._export_lock:
                self._export_progress = (done, total)
        def worker():
            try:
                report=export_all(path, result.network, result.target_prefix, fmt,
                                  stop=self.export_stop, progress=update, start=start, end=end)
                outcome=('ok',report)
            except ExportCancelled:
                outcome=('cancel',None)
            except Exception as exc:
                outcome=('error',str(exc))
            with self._export_lock:
                self._export_outcome=outcome
        self._export_lock=threading.Lock()
        self._export_progress=(0,end-start+1)
        self._export_outcome=None
        self.export_thread=threading.Thread(target=worker, daemon=False)
        self.export_thread.start()
        self.after(100, self._poll_export)

    def _poll_export(self):
        with self._export_lock:
            done,total=self._export_progress
            outcome=self._export_outcome
        if not self.winfo_exists(): return
        self.progress['value']=int(done*10000//total)
        self.export_label.set(f'{done:,} / {total:,} 项 ({done*100/total:.2f}%)')
        if outcome is None:
            self.after(100,self._poll_export)
            return
        if self.progress_dialog.winfo_exists():
            self.progress_dialog.grab_release()
            self.progress_dialog.destroy()
        self._set_button_state(self.export_button, True, 'export')
        kind, payload=outcome
        if kind=='ok':
            self.status.set(f'导出成功：共 {payload.rows:,} 项，保存至 {payload.path}')
            self.status_label.configure(style='Success.TLabel')
            messagebox.showinfo('导出完成', f'已导出 {payload.rows:,} 项。\n保存位置：{payload.path}', parent=self)
        elif kind=='cancel':
            self.status.set('导出已取消，未保留未完成文件。')
            self.status_label.configure(style='Hint.TLabel')
        else:
            self.status.set('导出失败。')
            self.status_label.configure(style='Warn.TLabel')
            messagebox.showerror('导出失败', str(payload), parent=self)

    def cancel_export(self):
        if self.export_stop: self.export_stop.set()
        self.export_label.set('正在取消并清理临时文件，请稍候…')

    def on_close(self):
        if self.export_thread and self.export_thread.is_alive():
            messagebox.showinfo('正在导出', '请先取消导出，并等待临时文件清理完成。', parent=self)
            self.cancel_export()
            return
        self.destroy()


if __name__=='__main__':
    App().mainloop()
