# IPv6SubnetCalculator V1.8 验证记录 / Validation Record

日期 / Date: 2026-10-20

本版新增“IPv6 地址范围转 CIDR”，包含首末地址的精确最简覆盖、精确数量、清单／报告复制及安全转入子网清单检查。同时新增英文示例，修正英文规划截图中的中文注释。
This release adds inclusive address-range conversion to minimal exact CIDRs, exact counts, list/report copying and protected transfer to Subnet List. English examples and recaptured screenshots fix Chinese sample comments in English documentation.

## 实际环境 / Environment

| 项目 / Item | 结果 / Result |
|---|---|
| 应用 / Application | V1.8 |
| OS | Linux-6.18.55-x86_64-with-glibc2.39, x86_64, Qt offscreen |
| Python | 3.12.14 |
| PyQt6 / Qt | 6.11.0 / 6.11.2 |
| 运行源码和资源 SHA-256 / Fingerprint | `d1bc306daaf337297d5b9f271593330b07e2cac773567aeae3a7a6ac8770a5fc` |
| Linux 单文件 / Onefile | 实际构建运行，版本与指纹匹配 / built and executed, matching version and fingerprint |
| Windows EXE | 本环境未构建运行 / not built or run here |

## 自动验证 / Automated Verification

| 检查 / Check | 结果 / Result |
|---|---|
| 完整回归 / Regression | 352 项通过，本版新增 16 项 / passed, including 16 new tests |
| 范围边界 / Range bounds | 单地址 `/128`、对齐范围、不对齐范围、完整 `::/0` 和精确 2^128 地址数通过 / single, aligned, unaligned and complete IPv6 ranges |
| 最简覆盖 / Minimal coverage | 80 组确定性随机范围：首末地址、连续不重叠、精确总量、相邻块不可继续精确合并；极端范围 254 条 / deterministic coverage and irreducibility checks |
| 输入错误 / Input errors | 空值、IPv4、CIDR、区域标识、非法及反向地址定位正确字段，编辑恢复 / invalid endpoints and editing recovery |
| 输入表示 / Address syntax | 空白、完整展开及 IPv4 映射 IPv6 写法通过 / whitespace, expanded and mapped IPv6 |
| 状态与复制 / State and copy | 改输入使旧结果失效；语言切换保留结果；CIDR 及当前语言报告复制通过 / invalidation, preserved state and localized reports |
| 清单衔接 / List transfer | 空清单自动检查；已有清单默认“否”；确认后替换并检查；忙碌或确认期间变化不覆盖；保留计算结果 / guarded transfer and retained calculation |
| 布局 / Layout | 中英文、两主题及 900×620 最小窗口操作可达 / both languages, themes and minimum window |
| 示例一致 / Paired examples | 中英文清单记录、关系、空闲及整理结果相同；方案参数与浏览状态相同 / matching data and planning results |
| 英文截图 / English captures | 使用英文清单及方案原文，规划注释为 Parent network；实际 Qt 重新拍摄 / language-specific source data and actual captures |
| 翻译目录 / Catalog | 607 条完成、0 未完成；TS/QM、上下文及占位符检查通过 / completed entries and compiled-resource checks |
| 源码自检 / Source check | 18 个工作流通过，含新范围工具 / workflows passed |
| 单文件自检 / Frozen check | 18 个工作流通过，含范围精确覆盖和双语结果保留 / workflows passed |
| 既有功能 / Existing functions | 计算、地址格式、关系、方案及拖放、清单规划、导航、双语导出和取消保护回归通过 / previous workflows passed |

## 性能样本 / Host Measurements

| 项目 / Item | 时间 / Time |
|---|---:|
| 核心计算中位数 / Calculation median | 0.009664 ms |
| 5,000 条关系检查 / List relationships | 89.361746 ms |
| 5,000 条空闲计算 / Free space | 80.863303 ms |
| 5,000 条整理 / Aggregation | 82.562673 ms |
| TXT 100,000 条 / rows | 0.87814 s |
| XLSX 20,000 条 / rows | 0.21464 s |

核心中位数不包含粘贴、弹窗与绘制；上述是本机样本，不是 Windows 性能保证或相对旧版提速。内存只跟踪 Python 分配，未包括 Qt 原生内存及进程全部内存。源码自检最大事件循环采样间隔为 12058.104 ms；短时自动检查不能证明无卡顿或长期稳定。
Core medians exclude paste, dialogs and drawing. These are host samples, not Windows guarantees or speed comparisons. Memory tracks Python allocations only. The source self-check observed a maximum event-loop sample gap of 12058.104 ms; short tests do not establish stall-free or long-term stability.

## Windows 验收 / Windows Acceptance

Windows 自动检查、人工操作、DPI、实际 Excel 打开、文件占用与至少 30 分钟日常使用仍待本机完成。完整解压源码后运行 build.cmd，再运行 verify.cmd 并保留报告。重点检查新范围工具、清单替换确认、两主题／语言、已有导出和拖放。清单见 docs/WINDOWS_ACCEPTANCE.md。
Windows automated/manual checks, DPI, Excel opening, file locking and 30-minute normal use remain pending. Fully extract, build and run verify.cmd; complete the acceptance checklist.

正式标签 v1.8；用户在 Releases 直接下载 IPv6SubnetCalculator_V1.8.exe。
Use tag v1.8 and distribute IPv6SubnetCalculator_V1.8.exe directly through Releases.
