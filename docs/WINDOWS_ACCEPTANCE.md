# V1.1 Windows 验收 / Windows Acceptance

V1.1 增加本地计算方案保存和恢复。验证范围包括核心功能、Windows 实机稳定性、性能和打包程序；实际 Windows 验收结果由本机运行和人工确认记录。IPv6 子网导入及规划仍属于 V1.x。

V1.1 adds local calculation-plan save and restore. Validation covers core functionality, Windows stability, performance, and packaged applications. Actual Windows acceptance is recorded after running the checks on Windows and completing the manual checks. Subnet import and planning remain V1.x work.

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
| Windows 环境 / Environment | 记录 Windows 版本、Python 架构、显示缩放比例 / Record Windows version, Python architecture and display scaling | 待验收 / Pending |
| 独立启动 / Portable startup | EXE 在未安装 Python 的 Windows 机器上启动；路径含空格或中文时资源完整 / Launch on Windows without Python, including paths with spaces or Unicode | 待验收 / Pending |
| 显示与主题 / Display and themes | 在常用缩放比例及最小窗口下查看三个页面、详情和导出弹窗；内容可读、无异常黑底、提示完整 / Check all three pages and dialogs at normal scaling and minimum size | 待验收 / Pending |
| 状态保留 / State retention | 定位、选择后切换主题／标签及最小化恢复，页码、范围和滚动位置符合预期；重启记住主题 / Verify navigation, selections, scrolling and saved theme | 待验收 / Pending |
| 计算边界 / Calculation boundaries | 默认示例、原前缀等于目标前缀、`::/0 → /128`、单地址 `/128` 及非法输入均正确 / Check default, equal prefixes, full space, single address and invalid input | 待验收 / Pending |
| 摘要复制 / Summary copying | 两种主题复制到记事本，检查网络、目标前缀、范围、精确容量和用途提示；编辑输入后复制旧摘要，重算后更新；非法重算禁用 / Paste in Notepad in both themes, verify exact data and guidance, edited-input snapshot behavior, valid update and invalid-input disabling | 待验收 / Pending |
| 计算方案 / Calculation plans | 中文名称备注、最大空间末页、多选和范围高亮往返；损坏文件保留当前工作；文件锁定保存失败保留原文件；关闭和打开前保存／放弃／取消均正确 / Unicode metadata, maximum-space views, selections, corruption, locked files and unsaved prompts | 待验收 / Pending |
| 地址格式 / Address formats | 转换大写、展开、全零、全一和 IPv4 映射地址；逐项及全部粘贴到记事本，二进制完整 128 位 / Verify case, expansion, zero/max/mapped addresses, individual/all copy and exact 128-bit binary | 待验收 / Pending |
| 双网段关系 / Network relationships | 检查相同、双向包含、相邻、独立、主机位规范化与非法输入；复制报告包含双方范围、精确重叠和间隔数 / Check all relationships, normalization, invalid inputs and complete report copying | 待验收 / Pending |
| 文件与 Excel / Files and Excel | 中文路径保存成功；Excel 可打开；超长序号完整；覆盖已被 Excel 占用的文件时明确报错且原文件保留 / Verify Unicode paths, workbook opening, exact long indices and locked destinations | 待验收 / Pending |
| 取消与退出 / Cancellation and exit | 导出中取消或关闭程序，正常结束并清理临时文件；失败后可以重新导出 / Verify cleanup and retry after cancellation, close and errors | 待验收 / Pending |
| 持续使用 / Extended session | 至少一次 30 分钟日常计算、翻页、定位、复制和导出使用，记录卡顿、崩溃或资源异常 / Record any hangs, crashes or resource anomalies during a 30-minute normal-use session | 待验收 / Pending |

测试文件建议放在临时目录，保留原文件副本用于覆盖与取消检查。报告中记录实际机器的耗时；Linux 自动检查及短时操作循环不计作 Windows 人工或长时间稳定性验收。

Use a temporary test folder and keep copies of originals for overwrite/cancellation checks. Record timings from the actual machine. Linux checks and short operation loops are recorded separately from Windows manual and extended-session acceptance.
