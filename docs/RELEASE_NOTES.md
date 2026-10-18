# IPv6SubnetCalculator V1.1

## ✨ 计算方案保存与恢复

- 新增本地 JSON 计算方案，保存网络、目标前缀、方案名称及备注。
- 打开后重新计算，恢复每页条数、页码、定位范围、当前页选择及标签页。
- 保存／打开入口使用图标和悬停提示，支持 Ctrl+S／Ctrl+O，另存为 Ctrl+Shift+S；未保存的参数、名称或备注更改支持保存、放弃或取消。
- 页码和序号以十进制文本保存，支持最大 IPv6 地址空间；不枚举或保存海量子网。
- 延续 12 pt 界面和数据字体、浅深色主题、地址格式转换及双网段关系分析。

## 🐛 文件与工作保护

- 拒绝损坏 JSON、不支持的版本、重复字段、超限文件及越界浏览位置，保留当前工作。
- 写入成功后才替换目标文件，失败保留原方案并清理临时文件。
- 修改计算输入后须重新计算再保存，避免保存不一致的参数和结果。

## 📦 下载与使用

在 Releases 的 Assets 中直接下载 `IPv6SubnetCalculator_V1.1.exe`，下载后运行，无需安装 Python。默认示例网络为 `2026:1015:abcd::/48`。

## 📄 许可

项目自有代码和资源使用 GPL-3.0-or-later，第三方组件保留各自许可。

---

## ✨ Save and Restore Calculation Plans

- Adds local JSON plans with a network, target prefix, name, and notes.
- Recalculates on opening and restores page size, page, locator range, current-page selection, and active tab.
- Uses save/open icons and hover tooltips, with Ctrl+S/Ctrl+O and Ctrl+Shift+S for Save As. Unsaved parameter/name/note changes support save, discard, or cancel.
- Stores pages and indices as decimal strings for exact full-space IPv6 support, without enumerating or saving huge subnet lists.
- Retains 12 pt interface/data fonts, both themes, address conversion, and two-network analysis.

## 🐛 File and Work Protection

- Rejects malformed JSON, unsupported versions, duplicate fields, oversized files, and invalid view state while retaining current work.
- Replaces files only after successful writing; failures preserve originals and clean temporary files.
- Requires recalculation after parameter edits to prevent inconsistent saved state.

## 📦 Download and Usage

Download `IPv6SubnetCalculator_V1.1.exe` directly from Releases Assets and run it. Python is not required. Default network: `2026:1015:abcd::/48`.

## 📄 License

Project-authored code/assets use GPL-3.0-or-later; third-party components retain their licenses.
