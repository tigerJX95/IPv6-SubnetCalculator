# IPv6SubnetCalculator V1.2 验证记录 / Validation Record

日期 / Date: 2026-10-18

V1.2 基于 V1.1 增加关于窗口、离线帮助、许可文本阅读及法律责任说明。以下为本次 Linux 实际运行结果；Windows 自动、人工与长时间使用验收仍需本机完成。

V1.2 adds About, offline help, license reading and legal notices to V1.1. The results below are from actual Linux runs. Windows automated, manual and extended-session acceptance remain pending.

## 环境 / Environment

| 项目 / Item | 记录 / Record |
|---|---|
| 程序 / Application | V1.2 |
| 系统 / OS | Linux-6.18.55-x86_64-with-glibc2.39, x86_64, Qt offscreen |
| Python | 3.12.14 |
| PyQt6 / Qt | 6.11.0 / 6.11.2 |
| Linux 单文件产物 / Onefile | PyInstaller 实际构建并运行 / built and executed |
| 运行源码与资源指纹 / Fingerprint | `5cedaa2a94a8d535cc3c70ff86d6e0c02b97b2052c37946b42633251dd394df8` |
| Windows EXE | 本环境未构建或运行 / not built or run here |

## 自动检查 / Automated Checks

| 项目 / Check | 结果 / Result |
|---|---|
| 完整回归 / Full regression | 238 项通过 / passed |
| 新增回归 / Added regression | 11 项：5 项文档／版本／指纹 + 6 项界面流程 / 5 content/version/fingerprint and 6 UI-flow tests |
| 关于入口 / Entry | 图标、F1、Esc、单窗口复用、阅读位置保留 / icon, shortcuts, reuse and retained reading position |
| 计算状态 / Work state | 打开关于不改变方案／分页／选择；关闭主程序同时关闭关于 / work state retained; child dialog closes with main window |
| 离线文档 / Offline documents | 四页及六份组件／许可文档正常读取，许可原文一致 / four pages and six documents loaded; original license text preserved |
| 主题与链接 / Themes and links | 浅深色、最小窗口、链接颜色及仅主动 HTTPS 跳转通过 / themes, minimum size, link colors and user-activated HTTPS links |
| 异常恢复 / Recovery | 缺失／空白／非 UTF-8 文档给出提示，其他文档可继续读取 / missing, empty and invalid UTF-8 text handled |
| 源码自检 / Source self-check | 100 轮通过，含关于四页、全部许可、方案往返、最大地址空间和后台导出 / 100 cycles passed |
| 单文件自检 / Onefile self-check | 相同检查通过，版本及指纹与源码一致 / same checks passed, matching version and fingerprint |
| 既有核心 / Existing core | 前缀组合、最大空间、定位、复制、方案保存、地址工具、TXT／XLSX、取消保护均通过 / core and file workflows passed |

源码和打包程序均通过 `about_help_licenses_legal_offline` 检查。自检使用临时设置与文件，不写系统剪贴板；完整回归中的剪贴板测试会恢复原数据。浅深色真实 Qt 截图已生成并检查。

Both source and onefile passed the offline About/help/license/legal check. Self-checks use temporary settings/files and do not write the clipboard; full clipboard tests restore original data. Actual Qt previews were generated and inspected.

## 性能样本 / Performance Samples

| 项目 / Item | 本次测量 / This run |
|---|---:|
| 最大地址空间计算 / Full-space calculation | 0.009699 ms |
| 最大空间末页 200 条 / Final page | 0.547538 ms |
| 末地址定位 / Final-address lookup | 0.005362 ms |
| TXT 100,000 条 / rows | 0.88199 s |
| XLSX 20,000 条 / rows | 0.23837 s |

性能数据只描述本次机器和负载，不代表相对旧版提速或 Windows 性能承诺。计算／分页／定位为重复测量中位数。内存测量只覆盖 Python 分配，不含 Qt 原生或完整进程内存。事件循环采样包含窗口创建和主动主题切换，样本不足不能证明无卡顿；短时循环不替代 Windows 显示缩放和至少 30 分钟日常使用验收。

Measurements describe this host/load, not a speedup or Windows guarantee. Memory covers Python allocations only. Event-loop samples include setup and scripted theme changes; insufficient samples do not prove absence of stalls. Short loops do not replace Windows scaling and a 30-minute normal-use check.

## Windows 本地验证 / Local Verification

覆盖源码后运行 `build.cmd`，生成 `dist/IPv6SubnetCalculator_V1.2.exe`；再运行 `verify.cmd`，查看 `verification/SUMMARY.md` 和 `summary.json`。人工项目见 [Windows 验收清单](WINDOWS_ACCEPTANCE.md)。

After replacing source, run `build.cmd`, followed by `verify.cmd`, and review the reports and Windows acceptance checklist. Releases users download the EXE directly; no ZIP is required to run it.
