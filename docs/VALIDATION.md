# IPv6SubnetCalculator V1.5 验证记录 / Validation Record

日期 / Date: 2026-10-19

本版新增单文件方案拖放、醒目输入错误和标准弹窗中文化。V1.6 中英即时切换的设计保存在源码 docs/I18N_PLAN.md；实施以前提 V1.5 Windows 实机验收为准。本版不提供语言切换。
This release adds plan drops, visible input errors and Chinese standard dialogs. The confirmed V1.6 bilingual design is recorded; implementation follows V1.5 Windows acceptance. V1.5 has no language switch.

## 实际环境 / Actual Environment

| 项目 / Item | 结果 / Result |
|---|---|
| 应用 / Application | V1.5 |
| 系统 / OS | Linux-6.18.55-x86_64-with-glibc2.39, x86_64, Qt offscreen |
| Python | 3.12.14 |
| PyQt6 / Qt | 6.11.0 / 6.11.2 |
| 运行源码及资源 SHA-256 / Fingerprint | `d6acedfd6113c2d0d43d1aefd791f7e93d0611f4002d7ac23d91da11f306cf83` |
| Linux 单文件 / Onefile | PyInstaller 实际构建并运行；版本和源码指纹一致 / built and executed, matching version and fingerprint |
| Windows EXE | 本环境未构建或运行 / not built or run here |

## 自动验证 / Automated Verification

| 检查 / Check | 结果 / Result |
|---|---|
| 完整回归 / Full regression | 299 项通过 / passed |
| 新增回归 / Added tests | 25 项：20 项导入／提示／弹窗 + 5 项错误信息与字段定位 / 20 UI and 5 error/field checks |
| 方案拖放 / Plan drops | 中文路径、大写扩展名、输入框／编辑区／表格实际 Qt 事件、确认取消与未保存流程通过 / Unicode paths, extensions, Qt events and transaction decisions |
| 文件保护 / File protection | 坏 JSON、多文件、文件夹、远程链接、不支持格式和不存在路径拒绝；失败／取消保留当前状态，不修改源文件 / strict rejection and state/source protection |
| 同路径及变化 / Same-path and changes | 先保存再导入同一路径恢复新保存内容；确认期间文件变坏再次拒绝 / revalidation after confirmation |
| 生命周期 / Lifecycle | 后台忙碌时暂缓；关闭后不执行待处理导入；不接受仅移动的拖放操作 / busy/close handling and no source-file moves |
| 错误提示 / Feedback | 两主题字段红框、警示图标、具体错误及编辑后清除；地址工具、定位与范围恢复通过 / visible errors and recovery |
| 中文标准控件 / Chinese standards | 实际是／否、保存／不保存／取消按钮与保守默认项；非原生中文文件选择；菜单、字节单位与 JSON 类型中文 / actual dialogs, menus, size units and MIME descriptions |
| 文件访问错误 / File access | 中文原因、原路径及错误码；Windows 共享冲突消息映射通过 / localized reasons with paths and codes |
| 源码及单文件 / Source and onefile | 自检全部通过，均含中文资源、共用导入及错误恢复 / all self-checks passed |
| 原有功能 / Existing functions | 计算、地址工具、方案、清单关系、空闲／聚合、100 轮导航、TXT／XLSX 和取消保护通过 / existing workflows passed |
| 预览 / Previews | 浅深色实际 Qt 运行截图更新；不向程序添加截图功能 / actual captures, no screenshot feature added |

## 性能样本 / Performance Samples

| 项目 / Item | 本机记录 / This host |
|---|---:|
| 核心计算 / Calculation | 0.009363 ms |
| 5,000 条关系检查 / Relationship check | 92.586503 ms |
| 5,000 条空闲计算 / Free space | 83.355432 ms |
| 5,000 条整理 / Aggregation | 80.882225 ms |
| TXT 100,000 条 / rows | 0.87324 s |
| XLSX 20,000 条 / rows | 0.22514 s |

上述数据为本机样本，核心运算取多次中位数，不包含粘贴、文件对话框或绘制。它们不代表 Windows 响应保证或相对旧版提速。内存记录仅为 Python 分配，不含 Qt 原生分配或进程全部内存；事件循环短时样本不能证明不存在卡顿。
These are host measurements, not Windows guarantees or comparisons with earlier releases. Core medians exclude paste, dialogs and drawing. Python allocation measurements exclude Qt/native memory and process RSS; short event-loop samples do not establish absence of stalls.

## Windows 验收 / Windows Acceptance

Windows 自动／人工、资源管理器拖放、英文显示语言下的弹窗、DPI、文件占用、Excel 及至少 30 分钟日常使用验收仍待本机完成。覆盖完整源码后运行 build.cmd，再运行 verify.cmd，保留 verification 报告；人工检查见源码 docs/WINDOWS_ACCEPTANCE.md。

Windows automated/manual, Explorer drag-drop, English-OS dialogs, DPI, file locking, Excel and 30-minute normal-use acceptance remain pending. Build and run verify.cmd locally and retain reports.

正式发布使用标签 v1.5，用户从 Releases 直接下载 IPv6SubnetCalculator_V1.5.exe。V1.5 实机验收后再开始 V1.6 中英即时切换。
Use tag v1.5 and distribute the EXE directly through Releases. Proceed to V1.6 after V1.5 Windows acceptance.
