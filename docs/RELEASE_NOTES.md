## ✨ V1.13 CIDR 输出与翻译维护

- 地址归属查询支持复制及保存匹配网段 CIDR：规范化、去重，按最长前缀优先排列，保留包含项；原报告仍保留原始行号及重复记录。
- 覆盖比较可分别选择新增、移除、共同覆盖，生成精确覆盖结果的最简 CIDR 清单，支持复制及 TXT 保存后重新导入。
- 显示所选类别的 CIDR 条数。空结果不生成空清单；超过 5,000 条时禁用纯 CIDR 输出，完整地址范围报告仍可保存。
- 修改输入立即清除结果；保存期间切换类别或重新计算会中止旧结果保存。沿用现有覆盖确认及保存冲突保护。
- 同步中英文界面及离线说明，保留已合并的 GitHub Actions 质量检查。Qt 安全升级仍待兼容运行库发布，本版不包含 Qt 漏洞修复。

- 修正 verify.cmd 仍查找 V1.12 程序的问题；验证目标改为从 APP_VERSION 自动读取，与构建输出名称一致。

### 🌐 翻译维护与异常显示

- 新增 TS/QM 一致性检查：核对翻译条目、上下文、完成状态、重复项及格式占位符；配套生成记录可发现翻译修改后漏编译或资源不匹配。
- 新增源码翻译遗漏扫描，检查 `text()` 及其导入别名、显式翻译调用和常用界面文本入口；检查接入构建前流程，回归测试及程序自检继续验证翻译资源。
- 新增翻译编译维护脚本，先在临时目录编译并检查，再更新 QM 及生成记录；编译或检查失败时保留原 QM。
- 翻译格式错误时回退原始消息，避免因占位符错误或译文行数变化引起显示异常；嵌套错误及后台清单错误保留翻译结构，文件路径及用户输入保留原文。
- 将范围分隔符正则移出翻译目录，输入语法不参与翻译。新增维护说明及针对资源损坏、漏翻译、异常显示的回归检查。

## ✨ V1.13 CIDR Output and Translation Maintenance

- Copy or save matching CIDRs from address lookup: normalized, deduplicated and ordered by longest prefix, retaining containing networks. Reports still preserve original line numbers and duplicate records.
- Select added, removed or common coverage and produce its exact minimal CIDR list. Copy or save TXT for reimport into Subnet List.
- Show the selected CIDR count. Empty categories cannot produce empty files; results exceeding 5,000 CIDRs disable list output while complete range reports remain available.
- Editing inputs invalidates output. Changing category or recalculating during a save dialog aborts stale output; overwrite confirmation and save conflict protection still apply.
- Updated bilingual UI and offline help. Retains the merged GitHub Actions checks. The Qt security upgrade is pending a compatible runtime release; this version does not fix Qt vulnerabilities.

- Fixed verify.cmd still targeting V1.12. The verification executable name now follows APP_VERSION, matching the build output.

### 🌐 Translation Maintenance and Error Display

- Added TS/QM consistency checks for messages, contexts, completion state, duplicates and format fields. Generation records detect missing recompilation and mismatched resources.
- Added source coverage checks for `text()` aliases, explicit translation calls and common UI text setters. Checks run before building; regression tests and application self-checks also validate catalog resources.
- Added a translation maintenance script that compiles and validates in a temporary directory before updating QM and its generation record. Failed compilation or validation preserves the existing QM.
- Malformed translation formats and missing translated lines fall back to the original message. Nested exceptions and background list errors retain localized structure; filenames and user content remain unchanged.
- Removed the range-separator regular expression from the catalog so parsing syntax is not translated. Added maintenance documentation and regression checks for damaged resources, missing translations and error display.


# V1.12 清单查询与覆盖比较 / List Lookup and Coverage Comparison

- 新增地址归属查询：输入 IPv6 地址，按最长前缀优先列出清单中所有匹配网段及原始行号，保留重复及包含项。
- 新增覆盖差异比较：当前清单作为基准，与粘贴或导入的 TXT／规划项目清单比较，精确统计新增、移除和共同覆盖的地址数与全部范围；等价 CIDR 拆分不产生虚假变化。
- 两项功能位于“子网清单”顶部查询图标，使用打开窗口时的清单快照；支持复制及 TXT 报告保存，沿用保存冲突保护。输入变化后清除旧结果。
- 单份清单继续限制为 5,000 条、1 MiB、20,000 行；空清单可用于比较全部新增或移除。错误行需修正后再查询或比较。

- Added address membership lookup: list all containing networks and original line numbers, longest prefix first, including duplicates and containing entries.
- Added coverage comparison: compare the current list with pasted or imported TXT / planning project lists, with exact added, removed and common address counts and complete ranges. Equivalent CIDR splits do not create false changes.
- Open both tools from the lookup icon at the top of Subnet List. They use a snapshot from when the window opened and support copying and conflict-safe TXT report saving. Editing inputs clears old results.
- Each list retains the 5,000-record, 1 MiB and 20,000-line limits. Empty lists support all-added or all-removed comparisons. Correct invalid records before querying or comparing.

# V1.12

✨ 规划项目未保存保护 / Planning draft protection

- 关闭程序、打开其他规划项目之前，可保存、放弃或取消未保存内容。
- 新草稿显示修改标记；单独切换结果页签不触发未保存提醒。
- 保存取消、失败或发生冲突时保留工作；确认期间内容变化会中止操作。

- Save, discard or cancel planning changes before closing or replacing a project.
- Modified indicators also cover new drafts; tab navigation alone does not mark a project as modified.
- Cancelled or failed saves and save conflicts preserve current work. Changes during confirmation abort the action.

# V1.11

## ✨ V1.11 规划项目保存与恢复

- “子网清单”顶部新增打开／另存规划项目图标，分配建议页也可使用。
- 独立 JSON 保存清单原文（含注释和空行）、父网段、分配目标前缀、请求数量和结果页签；支持保存未完成的草稿。
- 恢复前验证文件并确认替换，恢复后清除派生结果，请重新检查或规划。此文件与原有“计算方案”格式分开；Ctrl+S／Ctrl+O 仍操作计算方案。
- 沿用保存冲突保护；对话框期间输入或任务变化时拒绝过期操作。已有项目修改后显示未保存状态。
- 规划项目需手动保存，退出时暂不提供规划项目自动保存或未保存确认。
- Qt 依赖维持经验证基线，安全升级仍待处理；本版功能更新不代表漏洞已修复。

## ✨ V1.11 Planning Project Save and Restore

- New open/save-as icons at the top of Subnet List remain accessible on the Allocation Suggestions tab.
- Separate JSON preserves the original list (comments and blank lines included), parent network, allocation prefix, requested count and result tab. Unfinished drafts are supported.
- Files are validated before replacement confirmation. Restoring clears derived results; run checks or planning again. This format is separate from calculation plans; Ctrl+S/Ctrl+O still operate calculation plans.
- Reuses save conflict protection and rejects stale actions when inputs or tasks change during dialogs. Changes to saved projects are marked as unsaved.
- Projects require manual saving. Closing does not yet auto-save or prompt for unsaved planning projects.
- Qt pins retain the verified baseline. The pending security upgrade is not resolved by this feature release.

---

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
