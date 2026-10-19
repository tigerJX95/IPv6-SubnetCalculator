# IPv6SubnetCalculator V1.4 验证记录 / Validation Record

日期 / Date: 2026-10-19

V1.4 新增父网段空闲空间与等价 CIDR 整理，并将关于图标改为透明线条样式。
V1.4 adds parent-network free-space calculation, equivalent CIDR aggregation and a transparent About icon.

## 环境 / Environment

| 项目 / Item | 记录 / Record |
|---|---|
| 系统 / OS | Linux-6.18.55-x86_64-with-glibc2.39, x86_64, Qt offscreen |
| Python | 3.12.14 |
| PyQt6 / Qt | 6.11.0 / 6.11.2 |
| 打包 / Packaging | Linux PyInstaller onefile，已实际构建并运行 / built and executed |
| 运行源码及资源 SHA-256 / Fingerprint | `7a40afb90620d8d829edc6674b3d98489f7d126d18ce21161a4e8ef1a9ec241c` |
| Windows EXE | 本环境未构建或运行 / not built or run here |

## 自动验证 / Automated Checks

| 检查 / Check | 结果 / Result |
|---|---|
| 完整回归 / Full regression | 274 项通过 / passed |
| 新增测试 / Added tests | 17 项：10 核心 + 7 Qt 流程 / 10 core and 7 Qt workflows |
| 规划正确性 / Correctness | 60 组固定种子随机地址集合与区间／标准库聚合结果比对 / seeded oracle and stdlib comparisons |
| 边界 / Boundaries | 空占用、全占用、/0、/128、最大地址、重复与包含、主机位规范化通过 / empty/full occupancy, address extremes and normalization |
| 严格输入 / Strict inputs | 非法记录阻止规划；越界占用拒绝整次空闲计算 / invalid and out-of-parent entries rejected |
| 上限 / Limits | 5,000 条记录、1,048,576 UTF-8 字节、20,000 物理行分别校验 / entries, bytes and physical lines checked independently |
| 截断保护 / Truncation | 空闲明细最多 5,000 CIDR；总数及全部空闲范围保留；禁用不完整 CIDR 复制 / exact totals/ranges and safe copy behavior |
| 界面 / UI | 输入／父网段变化使对应结果失效；剪贴板、取消、退出等待、浅深色与透明图标通过 / invalidation, clipboard, cancellation, shutdown and themes |
| 源码与单文件 / Source and onefile | 自检均通过，版本与指纹一致；包含两项规划与原有功能 / matching version/fingerprint and planning checks |
| 原有功能 / Existing functions | 清单检查、关于、许可、地址工具、方案、最大空间、100 轮导航、TXT/XLSX 与取消保护通过 / existing workflows passed |

本版规划通过整数区间操作，不遍历 IPv6 地址。整理保持地址覆盖集合不变，不保留原始业务分配层级。
规划清单与结果不写入现有 v1 计算方案；保留工作请复制输入或报告。
空闲容量为整数精确值，可通过悬停提示或复制报告读取。

Planning operates on integer intervals without enumerating addresses. Aggregation preserves exact address coverage, not allocation hierarchy. Lists/planning results are not stored in v1 calculation plans; copy input/reports to retain work. Exact capacities are available through tooltips and reports.

## 性能样本 / Performance Samples

| 项目 / Item | 本次机器 / This run |
|---|---:|
| 5,000 条空闲计算 / free-space entries | 85.172177 ms |
| 5,000 条等价整理 / aggregation entries | 79.015111 ms |
| 5,000 条关系检查 / relationship entries | 90.610895 ms |
| TXT 100,000 条 / rows | 0.90051 s |
| XLSX 20,000 条 / rows | 0.21588 s |

前三项为五次核心运算中位数，不包含文件选择、粘贴和表格绘制。它们不是 Windows 响应保证或旧版性能对比。内存测量仅涵盖 Python 分配，不包含 Qt 原生分配和完整进程；短时自检与事件循环样本不证明不存在卡顿。
First three timings are five-sample core medians, excluding dialogs, paste and rendering. They are neither Windows guarantees nor comparisons with previous releases. Python allocation measurements exclude Qt/native memory and process RSS. Short checks do not establish absence of stalls.

## Windows 验收 / Windows Acceptance

Windows 自动、人工、缩放、Excel 打开及至少 30 分钟日常使用验收仍待本机完成。覆盖源码后运行 `build.cmd`，再运行 `verify.cmd`，查看生成的 verification 报告及 [WINDOWS_ACCEPTANCE.md](WINDOWS_ACCEPTANCE.md)。
标签使用 `v1.4`；普通用户从 Releases 直接下载 `IPv6SubnetCalculator_V1.4.exe`。

Windows automated/manual, DPI, Excel and 30-minute normal-use acceptance remains pending. Build and run verify.cmd locally. Use tag v1.4; users download the EXE directly from Releases.
