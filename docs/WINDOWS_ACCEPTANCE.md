# V1.9 Windows 验收 / Windows Acceptance

V1.9 增加清单／规划 TXT 保存与结果回流。需要在 Windows 中验证语言切换、显示缩放及打包资源，既有功能验收继续保留。

V1.9 adds list/planning TXT saves and protected result transfer. Verify switching, DPI and packaged resources on Windows alongside existing workflows.

## 自动检查 / Automated Checks

1. 在源码根目录运行 `build.cmd`，构建当前版本。/ Run `build.cmd` from the source root.
2. 运行 `verify.cmd`，等待结束。/ Run `verify.cmd` and wait for completion.
3. 查看 `verification/SUMMARY.md` 和 `verification/summary.json`，保留报告。/ Review and retain both reports.

源码程序与 EXE 会分别运行同一组隔离检查。报告应显示正确版本、相同源码／资源指纹、各阶段通过及 `windows_automated_checks: passed`。导出样本为 100,000 条 TXT 与 20,000 条 XLSX。源码回归还覆盖 8,385 种合法前缀组合、随机网段、150 轮连续界面操作，以及导出失败恢复。

The source application and executable run the same isolated checks. Reports should show the expected version, matching source/resource fingerprints, passed stages, and `windows_automated_checks: passed`. Export samples use 100,000 TXT rows and 20,000 XLSX rows. Source regression additionally covers 8,385 valid prefix pairs, seeded random networks, 150 continuous UI-operation cycles, and export-error recovery.

自动检查会连续打开／关闭窗口、切换主题、调整窗口大小和最小化恢复，Windows 上可能看到快速闪动；这是测试脚本的主动操作，普通 EXE 启动不执行这些动作。请在检查期间避免手动操作这些窗口。完整回归包含剪贴板功能测试，结束时恢复检查前的剪贴板数据。

Automated checks open/close windows, switch themes, resize and minimize/restore. Rapid visible changes on Windows are scripted actions; normal EXE startup does not perform them. Avoid interacting with test windows during the run. The full regression suite includes clipboard tests and restores the original clipboard data when it finishes.

## 人工检查 / Manual Checks

| 场景 / Scenario | 验收内容 / Expected behavior | 结果 / Result |
|---|---|---|
| 中英切换 / Languages | 地球入口位置、两语言浅深主题、错误／悬停／弹窗／表格／帮助即时更新；保留结果、页码、选择、定位、清单、规划及关于阅读状态 / Verify all translated surfaces and retained work | 待验收 / Pending |
| 重启与兼容 / Restart and compatibility | 重启恢复语言；中文名称备注及方案跨语言保存一致；后台任务完成采用当前语言；标准文件选择器输入文件名不变 / Verify persistence, data compatibility and asynchronous completion | 待验收 / Pending |
| 方案拖放 / Plan drops | 中文路径 JSON 拖到标题、输入框、编辑区和表格；确认／取消及未保存的保存／不保存／取消；坏文件、多文件、文件夹和 TXT 明确拒绝；不改源文件，不额外执行计算或导出；后台任务时阻止 / Check whole-window drops, transaction safety and busy handling | 待验收 / Pending |
| 输入提示 / Input feedback | 两种主题测试网络、目标前缀、地址工具、定位、范围、父网段及清单错误；红框、警示图标、加粗原因，编辑后恢复 / Verify visible errors and recovery in both themes | 待验收 / Pending |
| 中文弹窗 / Chinese dialogs | 英文 Windows 显示语言下检查打开／保存、覆盖、未保存、错误、导出确认、文件浏览和右键菜单；所有标准按钮为中文 / Check standard dialog text/buttons with English Windows display language | 待验收 / Pending |
| Windows 环境 / Environment | 记录 Windows 版本、Python 架构、显示缩放比例 / Record Windows version, Python architecture and display scaling | 待验收 / Pending |
| 独立启动 / Portable startup | EXE 在未安装 Python 的 Windows 机器上启动；路径含空格或中文时资源完整 / Launch on Windows without Python, including paths with spaces or Unicode | 待验收 / Pending |
| 显示与主题 / Display and themes | 在常用缩放比例及最小窗口下查看四个页面、详情和导出弹窗；内容可读、无异常黑底、提示完整 / Check all four pages and dialogs at normal scaling and minimum size | 待验收 / Pending |
| 状态保留 / State retention | 定位、选择后切换主题／标签及最小化恢复，页码、范围和滚动位置符合预期；重启记住主题 / Verify navigation, selections, scrolling and saved theme | 待验收 / Pending |
| 计算边界 / Calculation boundaries | 默认示例、原前缀等于目标前缀、`::/0 → /128`、单地址 `/128` 及非法输入均正确 / Check default, equal prefixes, full space, single address and invalid input | 待验收 / Pending |
| 摘要复制 / Summary copying | 两种主题复制到记事本，检查网络、目标前缀、范围、精确容量和用途提示；编辑输入后复制旧摘要，重算后更新；非法重算禁用 / Paste in Notepad in both themes, verify exact data and guidance, edited-input snapshot behavior, valid update and invalid-input disabling | 待验收 / Pending |
| 计算方案 / Calculation plans | 中文名称备注、最大空间末页、多选和范围高亮往返；损坏文件保留当前工作；文件锁定保存失败保留原文件；关闭和打开前保存／放弃／取消均正确 / Unicode metadata, maximum-space views, selections, corruption, locked files and unsaved prompts | 待验收 / Pending |
| 子网清单 / Subnet lists | UTF-8／BOM 中文文件路径、错误行号、规范化与去重复制、重复／包含／相邻计数；5,000 条与海量关系明细上限；取消和退出安全；两种主题及最小窗口正常 / Check Unicode import, exact counts, bounded details, clipboard, cancellation, closing and themes | 待验收 / Pending |
| 空闲空间与整理 / Planning | 检查空清单、完全占用、重复包含、越界拒绝、精确容量、整理覆盖不变、明细截断禁用复制、取消退出、浅深色透明关于图标 / Check empty/full occupancy, overlap, rejection, exact counts/coverage, bounded-copy protection, cancellation and transparent icon | 待验收 / Pending |
| 关于与许可 / About and licenses | 顶部图标／F1 打开；四页完整；七份许可文档离线可读；版本正确；两种主题与缩放正常；Esc 关闭；不改变当前计算与方案 / Verify entry, pages, seven offline documents, version, themes/scaling, Esc and retained calculation/plan | 待验收 / Pending |
| 地址格式 / Address formats | 转换大写、展开、全零、全一和 IPv4 映射地址；逐项及全部粘贴到记事本，二进制完整 128 位 / Verify case, expansion, zero/max/mapped addresses, individual/all copy and exact 128-bit binary | 待验收 / Pending |
| 双网段关系 / Network relationships | 检查相同、双向包含、相邻、独立、主机位规范化与非法输入；复制报告包含双方范围、精确重叠和间隔数 / Check all relationships, normalization, invalid inputs and complete report copying | 待验收 / Pending |
| 文件与 Excel / Files and Excel | 中文路径保存成功；Excel 可打开；超长序号完整；覆盖已被 Excel 占用的文件时明确报错且原文件保留 / Verify Unicode paths, workbook opening, exact long indices and locked destinations | 待验收 / Pending |
| 取消与退出 / Cancellation and exit | 导出中取消或关闭程序，正常结束并清理临时文件；失败后可以重新导出 / Verify cleanup and retry after cancellation, close and errors | 待验收 / Pending |
| 持续使用 / Extended session | 至少一次 30 分钟日常计算、翻页、定位、复制和导出使用，记录卡顿、崩溃或资源异常 / Record any hangs, crashes or resource anomalies during a 30-minute normal-use session | 待验收 / Pending |

测试文件建议放在临时目录，保留原文件副本用于覆盖与取消检查。报告中记录实际机器的耗时；Linux 自动检查及短时操作循环不计作 Windows 人工或长时间稳定性验收。

Use a temporary test folder and keep copies of originals for overwrite/cancellation checks. Record timings from the actual machine. Linux checks and short operation loops are recorded separately from Windows manual and extended-session acceptance.


## 导出专项 / Export Acceptance

- [ ] 中文 XLSX：表头“序号”“IPv6 子网”，工作表“IPv6子网”；英文为“No.”“IPv6 Subnet”，工作表“IPv6 Subnets”。在实际 Excel 中打开确认。
- [ ] 从第 100 项开始导出，确认保留实际序号及对应 CIDR；完整 IPv6 空间的末两项序号保留全部数字。
- [ ] 在保存文件选择器中切换语言再开始，文件使用最终开始时的语言。
- [ ] 大范围导出期间切换语言，文件内部语言一致，完成提示使用当前界面语言。
- [ ] TXT 中英文结果一致，每行一个 CIDR，可重新导入；取消导出保留原文件并清理临时文件。
- [ ] 最小窗口和两种主题下，页签滚动按钮悬停分别为中文或英文。

Check actual Excel opening, both header languages and sheet names, non-first ranges and exact large indices. Switch languages in the picker and during export; verify task-start file language and current-language feedback. Reimport TXT, cancel an export and inspect tab-scroll tooltips in both themes.


## V1.8 示例 / Examples

- [ ] 打开 `PlanningNetworks_EN.txt`，确认首行是英文 Parent network，五条网段及规划结果与中文样例一致。
- [ ] 英文清单和方案示例的注释、名称、备注使用英文；切换语言不修改已导入内容。
- [ ] README 中英文规划截图显示英文注释。

Open the English examples and compare matching CIDRs and results. Confirm switching languages preserves their original text and the README planning image uses English comments.


## V1.8 地址范围 / Address Ranges

- [ ] 范围 `2026:1015:abcd::1`～`2026:1015:abcd::ff`：255 个地址，精确 CIDR 清单；单地址为 `/128`，完整 IPv6 空间为 `::/0`，精确计数为 2^128。
- [ ] 非法／反向地址定位正确字段，修改后清除错误并禁用旧结果操作。
- [ ] 两主题、最小窗口及中英文切换下可阅读、复制并保留结果。
- [ ] 发送至空清单自动检查；已有内容时“否”保留原文，“是”替换并检查；忙碌时不覆盖。

Check inclusive bounds, exact counts, invalid-order recovery, copy/report language, minimum-size access and safe transfer to existing/busy lists.


## V1.9 文本保存与回流 / Text Output and Transfer

- [ ] 中英文、两主题：保存菜单文案、悬停提示及启用状态正确。
- [ ] 原始输入保留空行、注释与中文内容；有效 CIDR 文件可重新导入，报告包含错误行及精确数量。
- [ ] 空闲与整理结果分别保存清单及报告；空闲明细截断时只能保存报告，无空闲结果仍可保存报告。
- [ ] 取消保存／拒绝覆盖保留原文件；文件占用或权限失败后可重试，临时文件清理。
- [ ] 保存窗口期间切换语言，报告采用保存时语言；修改输入、父网段或来源结果后拒绝旧快照。
- [ ] 规划回流默认“否”；确认后替换并自动检查；取消及忙碌时保留当前工作。

Verify output content, reimport, incomplete/empty results, overwrite and failure recovery, dialog-time changes, save-time language and protected planning transfer on Windows.


## V1.9 双语审计修订 / Bilingual Revision

- [ ] 简体中文模式：导出／打开／保存等文件选择器中，普通文件夹类型为“文件夹”，其他类型、大小单位及日期不受 Windows 显示语言影响。
- [ ] English 模式：Folder、文件类型与日期均使用英文展示。
- [ ] 窗口保持打开时来回切换，目录、选中文件、筛选项和输入文件名不丢失。
- [ ] 关于中的程序信息、帮助、法律说明和组件概览对应当前语言，许可证原文不变。
- [ ] 文件不存在提示、保存／放弃／取消确认及输入框右键菜单语言一致。

Verify these cases on Windows in both OS display languages where available; Linux offscreen and simulated native-type strings do not replace Windows acceptance.
