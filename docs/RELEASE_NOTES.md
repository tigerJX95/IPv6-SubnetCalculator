# V1.10 — 子网分配建议 / Subnet Allocation Suggestions

## 简体中文

### 🐛 审计修复（统一并入 V1.10）

- 🐛 A01：方案、TXT 保存与批量 TXT/XLSX 导出增加确认时文件快照及提交前冲突检测。原本不存在的目标采用原子无覆盖新建；同程序并发保存协调提交。
- 🐛 检出冲突时保留目标文件，并保留本次完整恢复输出，提示路径；取消仍清理未完成文件。拒绝覆盖目录、符号链接等非普通目标。
- 🐛 A02：修复方案保存快照与“已保存”状态不一致；对话框期间状态变化时拒绝旧保存，后续修改保留未保存标记。
- 🐛 A03：验证改用带运行标识的结构化 unittest 结果，拒绝缺失、截断、零测试、未完成、失败或旧证据；自检须完成全部约定工作流。
- 🌐 新增冲突、恢复路径及错误提示同步提供中英文。
- 📸 删除独立保存菜单截图及中英文 README 的相应引用，保留完整程序窗口截图。
- ⏳ D01 / Qt：核实官方 PyPI 最新可安装 Qt wheel 仍为 6.11.2，6.11.3 尚未发布；兼容升级暂未完成，不虚写已修复或已升级。详见 [依赖状态](DEPENDENCY_STATUS.md)。

保存保护的实际边界和恢复方法见 [保存冲突保护](SAVE_CONFLICTS.md)。

✨ 新增按目标前缀统计可分配子网数量；基于全部空闲区间计算，考虑 CIDR 对齐和碎片，不依赖被截断的空闲 CIDR 明细。
✨ 按数量生成最多 5,000 个候选网段，支持复制和 TXT 保存、完整容量报告；容量不足时不生成部分建议。
✨ 确认后将建议追加到原占用清单，保留已有内容及注释，自动重新计算剩余空闲空间。
🛡️ 追加前后检查状态快照，遵守清单原有的记录、字节与物理行限制；修改输入后清除旧建议。
🌐 新界面、提示、报告、帮助及截图同步提供简体中文和 English。保留 V1.9 双语修订。

## English

### 🐛 Audit fixes merged into V1.10

- 🐛 A01: plans, TXT saves and bulk TXT/XLSX exports retain the approval-time destination revision and check for conflicts at commit. Initially absent targets use atomic no-overwrite publication; cooperating application processes coordinate existing-file commits.
- 🐛 Conflicts preserve the destination and complete recovery output, with a reported recovery path. Cancellation still removes incomplete files. Directories, symbolic links and other nonregular targets cannot be overwritten.
- 🐛 A02: fixed saved-plan snapshot tracking. Changes during dialogs invalidate the save; later changes remain dirty.
- 🐛 A03: verification now requires structured unittest evidence bound to a run identifier. Missing, truncated, zero-test, incomplete, failed or stale evidence is rejected. Self-checks must include every required workflow.
- 🌐 Conflict and recovery messages support both interface languages.
- 📸 Removed standalone save-menu screenshots and their Chinese/English README references, retaining full application-window screenshots.
- ⏳ D01 / Qt: official PyPI still provides Qt 6.11.2 as the latest installable wheel, with no 6.11.3 distribution. The compatible upgrade remains pending; it is not reported as completed. See [dependency status](DEPENDENCY_STATUS.md).

See [save conflict protection](SAVE_CONFLICTS.md) for recovery steps and concurrency limits.

✨ Count available subnets for a target prefix using all free intervals, including alignment and fragmentation, independently of truncated free CIDR details.
✨ Generate up to 5,000 candidates on request. Copy or save CIDRs and capacity reports as TXT. Insufficient capacity produces no partial suggestions.
✨ Confirm to append candidates to the occupied list, retain existing content and comments, and recalculate remaining free space.
🛡️ Recheck snapshots around confirmation and enforce existing record, byte and physical-line limits. Input changes invalidate old suggestions.
🌐 New controls, tooltips, reports, help and screenshots support Simplified Chinese and English. V1.9 bilingual fixes are retained.

---

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
