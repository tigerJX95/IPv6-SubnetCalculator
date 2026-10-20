# IPv6SubnetCalculator V1.9

## 🐛 双语一致性修订

- 修复简体中文模式下文件类型仍显示 File Folder，统一显示“文件夹”；文件类型、大小、日期和列名跟随应用语言。
- 第三方组件概览分别显示对应语言，许可原文保留。
- 修复动态标签、状态及提示中残留的中文标点。
- 补充主界面、菜单、弹窗、错误、进度、帮助、文件列表与双向切换回归。


## ✨ 清单与规划 TXT 保存

- 子网清单新增保存菜单：原始输入、有效去重 CIDR、检查报告。
- 空闲空间与 CIDR 整理支持保存完整 CIDR 清单或规划报告，报告使用保存时的界面语言。
- 原始输入保留编辑区注释、空行及原文；纯 CIDR TXT 可重新导入。
- 覆盖前确认，临时文件成功写入后才替换目标；失败保留原文件。

## ✨ 规划结果继续检查

- 完整空闲或整理结果可通过图标送回子网清单，自动执行校验与关系检查。
- 替换已有输入前确认，默认“否”；任务忙碌或确认期间来源变化时保留当前工作。
- 空闲明细截断时禁用完整 CIDR 保存与回流，报告仍保留全部空闲地址范围和精确统计。

## 🐛 状态与文档

- 保存对话框关闭后复核输入与结果，避免保存失效快照。
- 新操作适配中英文、浅深主题及最小窗口，并提供悬停提示。
- 更新双语 README、离线帮助与实际界面截图。

## 📦 下载

从 Releases 的 Assets 直接下载 `IPv6SubnetCalculator_V1.9.exe`。标签：`v1.9`。

---

## 🐛 Bilingual Consistency Revision

- Fixed File Folder appearing in Chinese file dialogs. Folder/type labels, sizes, dates and headers now follow the application language.
- Localized the component overview while preserving original license texts.
- Fixed Chinese punctuation remaining in assembled labels and messages.
- Added coverage for pages, menus, dialogs, errors, progress, help, file lists and live language switching.

## ✨ Save List and Planning Text

- Subnet List adds a save menu for original input, valid deduplicated CIDRs and check reports.
- Free Space and Aggregation save complete CIDR lists or planning reports. Reports use the interface language at save time.
- Original input retains editor comments, blank lines and user text; CIDR TXT can be reimported.
- Overwriting requires confirmation. Temporary-file writes replace the destination only on success, preserving existing files after failure.

## ✨ Continue Checking Planning Results

- Send complete free/aggregated CIDRs back to Subnet List for automatic validation and relationship checks.
- Replacing existing input defaults to No. Busy tasks and changed source results preserve current work.
- Truncated free-space details disable complete CIDR saving and transfer; reports retain all free address intervals and exact counts.

## 🐛 State and Documentation

- Revalidates input and result snapshots after save dialogs to reject stale output.
- New actions support both languages, themes and minimum window size with tooltips.
- Updated bilingual READMEs, offline help and actual application screenshots.

## 📦 Download

Download `IPv6SubnetCalculator_V1.9.exe` directly from Assets on Releases. Tag: `v1.9`.
