# IPv6SubnetCalculator V1.6 验证记录 / Validation Record

日期 / Date: 2026-10-19

V1.6 增加简体中文与 English 即时切换、语言偏好恢复及双语离线帮助。切换更新现有控件，不重建窗口或重新计算业务数据。输入与方案数据保留原文；TXT／XLSX 文件格式及原有列名保持既有约定。
V1.6 adds live Simplified Chinese/English switching, remembered language and bilingual offline help. Existing controls are updated without rebuilding windows or recalculating data. User content stays unchanged; TXT/XLSX formats and existing column names retain their established conventions.

## 实际环境 / Environment

| 项目 / Item | 结果 / Result |
|---|---|
| 应用 / Application | V1.6 |
| 系统 / OS | Linux-6.18.55-x86_64-with-glibc2.39, x86_64, Qt offscreen |
| Python | 3.12.14 |
| PyQt6 / Qt | 6.11.0 / 6.11.2 |
| 运行源码及资源 SHA-256 / Fingerprint | `09f8b123f5aa8df5674f921cfa3068fcc8c8727a5a265aa965d02a80084f7954` |
| Linux 单文件 / Onefile | PyInstaller 实际构建和运行；版本及源码指纹匹配 / built and executed, matching version and fingerprint |
| Windows EXE | 本环境未构建或运行 / not built or run here |

## 自动验证 / Automated Verification

| 检查 / Check | 结果 / Result |
|---|---|
| 完整回归 / Full regression | 321 项通过 / tests passed |
| 本版新增 / Added in V1.6 | 22 项 i18n 回归 / i18n tests |
| 即时切换 / Live switching | 页签、输入、结果对象、选择、定位和方案状态保留；连续切换及后台完成后的语言正确 / state preservation, repeated switches and worker completion |
| 偏好恢复 / Preferences | 中英文分别经新进程恢复；无效设置回退中文；保存失败提示正确 / fresh-process restoration, invalid fallback and save failure |
| 动态内容 / Dynamic text | 状态、核心错误、字段警告、报告及工具结果按当前语言显示；原始中文用户内容和大整数保留 / current-language messages with raw user data and exact integers |
| 标准弹窗 / Standard dialogs | 新开及已打开的确认框和文件选择器跟随语言，保留文件名、筛选项和保守默认项 / current and open dialogs retain selections and defaults |
| 翻译资源 / Catalogs | 583 条完成、0 条未完成；占位符及编译 QM 与 TS 一致 / completed entries, placeholder and compiled-resource checks |
| 关于与帮助 / About and help | 所选页签及许可项保持；帮助和法律说明切换语言；第三方许可原文保留 / selected tabs and licenses preserved, original license texts unchanged |
| 两主题布局 / Layout | 最小 900 × 620、中英文及浅深色切换测试；实际 Qt 运行预览 / minimum-size tests and actual captures |
| 原有核心功能 / Existing functions | 计算、地址转换、双网段关系、方案导入保存及拖放、清单关系、空闲空间和 CIDR 整理通过 / existing workflows passed |
| 导航与导出 / Navigation and export | 100 轮导航与选择、后台 TXT／XLSX、取消保留原文件并清理临时文件 / navigation cycles and cancellation protection |
| 源码自检 / Source self-check | 16 个工作流通过 / workflows passed |
| 单文件自检 / Frozen self-check | 16 个工作流通过 / workflows passed |

## 性能样本 / Performance Samples

| 项目 / Item | 本机记录 / This host |
|---|---:|
| 核心计算 / Calculation | 0.014372 ms |
| 5,000 条关系检查 / Relationship check | 134.040174 ms |
| 5,000 条空闲计算 / Free space | 118.570567 ms |
| 5,000 条整理 / Aggregation | 115.962899 ms |
| TXT 100,000 条 / rows | 1.20982 s |
| XLSX 20,000 条 / rows | 0.28075 s |

核心运算采用多次采样的中位数，不包含粘贴、弹窗和绘制。这些是本机样本，不代表 Windows 性能保证或与旧版的提速对比。内存检查仅跟踪 Python 分配，不包含 Qt 原生分配或进程全部内存。源码自检事件循环最大间隔为 1034.314 ms，不能据此宣称界面无卡顿；短时检查也不能代替长期稳定性测试。
Core timings are medians excluding paste, dialogs and painting. These host measurements are not Windows guarantees or speed comparisons. Memory samples track Python allocations only. The source self-check observed a maximum event-loop gap of 1034.314 ms; short checks do not establish stall-free or long-term stability.

## Windows 验收 / Windows Acceptance

Windows 自动检查、实机人工验收及至少 30 分钟日常使用仍待完成。应覆盖首次启动与重启语言恢复、两主题及 DPI、窗口缩放、弹窗中途切换、中文路径、资源管理器拖放、文件占用和 Excel 打开导出文件。操作步骤见 docs/WINDOWS_ACCEPTANCE.md。
Windows automated/manual checks and at least 30 minutes of normal use remain pending. Cover language restoration, themes, DPI, resizing, switching open dialogs, Unicode paths, Explorer drops, file locking and exported workbooks.

在 Windows 使用 build.cmd 构建，再运行 verify.cmd 并保留报告。正式版本标签使用 v1.6，普通用户从 Releases 直接下载 IPv6SubnetCalculator_V1.6.exe。
Build on Windows with build.cmd, run verify.cmd and retain reports. Use tag v1.6 and distribute IPv6SubnetCalculator_V1.6.exe directly through Releases.
