# V0.9 Windows 验收 / Windows Acceptance

V1.0 的验收范围为核心功能完整、Windows 实机稳定性、性能和打包程序验证。V0.9 提供自动验证入口；实际 Windows 验收结果由本机运行和人工确认记录。IPv6 子网导入及规划仍属于 V1.x。

V1.0 requires complete core functionality plus Windows stability, performance, and packaged-application validation. V0.9 provides repeatable automated checks; actual Windows results come from running them on Windows and completing the manual checks. Subnet import and planning remain V1.x work.

## 自动检查 / Automated Checks

1. 在源码根目录运行 `build.cmd`，构建当前版本。/ Run `build.cmd` from the source root.
2. 运行 `verify.cmd`，等待结束。/ Run `verify.cmd` and wait for completion.
3. 查看 `verification/SUMMARY.md` 和 `verification/summary.json`，保留报告。/ Review and retain both reports.

源码程序与 EXE 会分别运行同一组隔离检查。报告应显示正确版本、相同源码／资源指纹、各阶段通过及 `windows_automated_checks: passed`。导出样本为 100,000 条 TXT 与 20,000 条 XLSX。源码回归还覆盖 8,385 种合法前缀组合、随机网段、150 轮连续界面操作，以及导出失败恢复。

The source application and executable run the same isolated checks. Reports should show the expected version, matching source/resource fingerprints, passed stages, and `windows_automated_checks: passed`. Export samples use 100,000 TXT rows and 20,000 XLSX rows. Source regression additionally covers 8,385 valid prefix pairs, seeded random networks, 150 continuous UI-operation cycles, and export-error recovery.

自动检查可能连续打开和关闭测试窗口，请在检查期间避免手动操作这些窗口。完整回归包含剪贴板功能测试，结束时恢复检查前的剪贴板数据。

Automated checks open and close test windows; avoid interacting with them during the run. The full regression suite includes clipboard tests and restores the original clipboard data when it finishes.

## 人工检查 / Manual Checks

| 场景 / Scenario | 验收内容 / Expected behavior | 结果 / Result |
|---|---|---|
| Windows 环境 / Environment | 记录 Windows 版本、Python 架构、显示缩放比例 / Record Windows version, Python architecture and display scaling | 待验收 / Pending |
| 独立启动 / Portable startup | EXE 在未安装 Python 的 Windows 机器上启动；路径含空格或中文时资源完整 / Launch on Windows without Python, including paths with spaces or Unicode | 待验收 / Pending |
| 显示与主题 / Display and themes | 在常用缩放比例及最小窗口下查看两页、详情和导出弹窗；内容可读、无异常黑底、提示完整 / Check both pages and dialogs at normal scaling and minimum size | 待验收 / Pending |
| 状态保留 / State retention | 定位、选择后切换主题／标签及最小化恢复，页码、范围和滚动位置符合预期；重启记住主题 / Verify navigation, selections, scrolling and saved theme | 待验收 / Pending |
| 计算边界 / Calculation boundaries | 默认示例、原前缀等于目标前缀、`::/0 → /128`、单地址 `/128` 及非法输入均正确 / Check default, equal prefixes, full space, single address and invalid input | 待验收 / Pending |
| 文件与 Excel / Files and Excel | 中文路径保存成功；Excel 可打开；超长序号完整；覆盖已被 Excel 占用的文件时明确报错且原文件保留 / Verify Unicode paths, workbook opening, exact long indices and locked destinations | 待验收 / Pending |
| 取消与退出 / Cancellation and exit | 导出中取消或关闭程序，正常结束并清理临时文件；失败后可以重新导出 / Verify cleanup and retry after cancellation, close and errors | 待验收 / Pending |
| 持续使用 / Extended session | 至少一次 30 分钟日常计算、翻页、定位、复制和导出使用，记录卡顿、崩溃或资源异常 / Record any hangs, crashes or resource anomalies during a 30-minute normal-use session | 待验收 / Pending |

测试文件建议放在临时目录，保留原文件副本用于覆盖与取消检查。报告中记录实际机器的耗时；Linux 自动检查及短时操作循环不计作 Windows 人工或长时间稳定性验收。

Use a temporary test folder and keep copies of originals for overwrite/cancellation checks. Record timings from the actual machine. Linux checks and short operation loops are recorded separately from Windows manual and extended-session acceptance.
