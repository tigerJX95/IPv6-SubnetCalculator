# IPv6SubnetCalculator V0.9 验证记录 / Validation Record

日期 / Date: 2026-10-17

本记录来自实际自动运行。测试环境为 Linux，Windows 自动检查及人工验收尚未完成。V0.9 聚焦迁移后稳定性与性能验证；V1.0 的 Windows 验收以目标机器报告和人工检查结果为准。

This record reports an actual automated run on Linux. Windows automated and manual acceptance remain pending. V0.9 focuses on post-migration stability and performance checks; V1.0 Windows acceptance depends on reports and manual checks from the target machines.

## 环境 / Environment

| 项目 / Item | 值 / Value |
|---|---|
| 应用 / Application | V0.9 |
| 系统 / OS | Linux x86_64 |
| Python | 3.12.14 |
| PyQt6 / Qt | 6.11.0 / 6.11.2 |
| 图形环境 / GUI backend | Qt offscreen |
| 打包检查 / Packaging check | Linux PyInstaller onedir，可执行程序真实运行 / actual frozen executable run |
| 运行源码与资源指纹 / Runtime source-resource SHA-256 | `cb428388cf18e80996adfe9ff50f254792eb95b09cab20fb4c9f21d138c855a2` |
| Windows 自动检查 / Windows automated checks | 未运行 / Not run |
| Windows 人工及长时间验收 / Windows manual and extended-session acceptance | 待完成 / Pending |

## 正确性与异常恢复 / Correctness and Recovery

| 检查 / Check | 本次结果 / Result |
|---|---|
| 自动化回归 / Regression | 182 项通过 / passed |
| 合法前缀组合 / Valid prefix pairs | 8,385 组，与 Python ipaddress 标准库交叉验证 / checked against Python ipaddress |
| 随机网段 / Random networks | 固定种子 300 组，包含主机位规范化与完整小规模划分 / 300 seeded cases |
| 连续界面操作 / Continuous UI operations | 回归中 150 轮，覆盖分页、定位、选择、主题、标签和缩放窗口 / 150 regression cycles |
| 源码及打包程序自检 / Source and frozen self-check | 各 100 轮导航／选择，均通过 / 100 cycles each, passed |
| 最大地址空间 / Maximum address space | `::/0 → /128`，末页序号 `2^128`，表格最多加载 200 条 / final index verified, at most 200 rows loaded |
| 导出失败 / Export failures | 启动异常、静默启动失败、缺少完成结果、模拟写入失败与目标替换失败均覆盖 / startup, missing outcome, write and replacement failures covered |
| 文件保护 / File protection | 失败／取消时保留原文件，清理未完成临时文件 / original retained and temporary files cleaned |
| 资源与许可 / Resources and licensing | 两套主题、SVG 箭头、图标及项目／第三方许可资源通过 / both themes and bundled resources passed |
| 中文路径 / Unicode paths | 源码和打包程序均完成中文路径 TXT／XLSX 后台导出 / source and frozen exports passed |
| 构建对应关系 / Build matching | 源码与打包程序版本及指纹一致 / matching version and fingerprint |

## 性能样本 / Performance Samples

计算、末页和定位数据为五组重复测量中“单次平均耗时”的中位数；不包含首次启动、首次字体加载或人工操作耗时。数据描述本次机器，不设固定速度通过门槛。

Calculation, pagination and location timings are medians of five batch-mean measurements. They exclude first launch, initial font loading and human input. Results describe this machine and do not use a fixed speed pass/fail threshold.

| 操作 / Operation | 本次测量 / Measurement |
|---|---|
| `::/0 → /128` 计算，关闭预览 / Calculation without preview | 0.029555 ms |
| 最大空间末页，每页 200 条 / Final page, 200-row page size | 1.967401 ms |
| 定位最后一个 IPv6 地址 / Locate the final IPv6 address | 0.015737 ms |
| TXT，100,000 条 / rows | 2.59941 s；38,470 条/秒 / rows per second |
| XLSX，20,000 条 / rows | 0.82332 s；24,292 条/秒 / rows per second |
| 首批 1,024 条后取消，场景总耗时 / Total scenario time, cancel after first 1,024 rows | 0.02409 s |

导出样本为 `::/0 → /128` 的前 N 条，地址长度和磁盘条件会影响其他网段的实际耗时。取消场景计时包含请求取消前的首批写入，并非单独的取消响应延迟。

Export samples use the first N subnets of `::/0 → /128`; other address lengths and storage conditions can change throughput. Cancellation timing includes the initial batch written before the request and is not an isolated cancellation-latency measurement.

## 导出内存 / Export Memory

| 格式 / Format | 1,000 条峰值 / peak bytes | 10,000 条峰值 / peak bytes |
|---|---:|---:|
| TXT | 7,616 | 7,617 |
| XLSX | 311,361 | 340,441 |

仅记录 `tracemalloc` 可见的 Python 分配，不含 Qt 原生内存、操作系统缓存或进程总内存；该样本用于检测意外全量列表等内存增长。30 分钟实机使用与进程资源观察仍属于 Windows 人工验收。

These figures cover Python allocations visible to tracemalloc, excluding native Qt memory, OS caches and total process memory. The sample helps detect accidental full-result materialization. A 30-minute real-machine session and process-resource observations remain part of Windows manual acceptance.

## 后台事件循环采样 / Background Event-loop Samples

| 场景 / Scenario | TXT 最大观察间隔 / max observed gap | XLSX 最大观察间隔 / max observed gap |
|---|---:|---:|
| 源码程序 / Source | 231.568 ms | 27.169 ms |
| 打包程序 / Frozen | 280.422 ms | 32.992 ms |

采用 10 ms Qt 定时器采样，记录后台导出期间实际观察到的间隔；包含当前负载和绘制影响。该指标不是帧率、所有交互的响应上限或 Windows 性能承诺。

A 10 ms Qt timer samples observed gaps during background export, including current load and painting effects. These figures are not frame rates, bounds on every interaction, or Windows performance guarantees.

## 复现与下一步 / Reproduction and Next Step

Windows 源码目录中先运行 `build.cmd`，再运行 `verify.cmd`；结果位于 `verification/`。人工检查项目见 [Windows 验收说明](WINDOWS_ACCEPTANCE.md)。

On Windows, run `build.cmd` and then `verify.cmd` from the source folder. Results are written to `verification/`. See [Windows Acceptance](WINDOWS_ACCEPTANCE.md) for manual checks.
