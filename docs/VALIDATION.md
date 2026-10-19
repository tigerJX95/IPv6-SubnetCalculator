# IPv6SubnetCalculator V1.3 验证记录 / Validation Record

日期 / Date: 2026-10-19

V1.3 基于 V1.2 增加已有 CIDR 清单导入、逐行校验、批量关系检查和结果复制。以下为本次 Linux 实际结果；Windows 自动、人工及长时间验收仍需本机完成。

V1.3 adds existing-CIDR import, line validation, batch relationships and copying to V1.2. Results below come from actual Linux runs. Windows automated/manual/extended-session acceptance remains pending.

## 环境 / Environment

| 项目 / Item | 记录 / Record |
|---|---|
| 应用 / Application | V1.3 |
| 系统 / OS | Linux-6.18.55-x86_64-with-glibc2.39, x86_64, Qt offscreen |
| Python | 3.12.14 |
| PyQt6 / Qt | 6.11.0 / 6.11.2 |
| 打包 / Packaging | Linux PyInstaller onefile，实际构建并运行 / built and executed |
| 运行源码及资源 SHA-256 / Fingerprint | `ac9f1cccfeaab6c8d02d845a7f1711885ffe8e2172e2933616f290a91fe60509` |
| Windows EXE | 本环境未构建或运行 / not built or run here |

## 自动验证 / Automated Checks

| 检查 / Check | 结果 / Result |
|---|---|
| 完整回归 / Full regression | 257 项通过 / passed |
| 新增回归 / Added tests | 19 项：11 项核心／文件 + 8 项界面流程 / 11 core/file and 8 UI tests |
| 关系正确性 / Relations | 60 组随机清单与逐对区间判定比对；原始行号、重复、包含、相邻及最大地址空间通过 / 60 seeded list comparisons with an exhaustive interval oracle |
| 密集清单 / Dense list | 5,000 条重复输入精确统计 12,497,500 对，明细最多 1,000 对 / exact total with bounded details |
| 文件与上限 / File bounds | UTF-8／BOM／CRLF、中文路径、1 MiB／5,000 条／20,000 行上限、坏编码和空文件通过 / encoding, Unicode paths, limits and bad-file checks |
| 界面状态 / UI state | 修改输入禁用过期复制；导入失败保留已有输入与结果；失败可重试 / stale-copy prevention, failed-import preservation and retry |
| 取消与退出 / Cancel and close | 后台检查取消保留输入，关闭主窗口等待线程完成 / input retained and orderly worker completion |
| 方案兼容 / Plan compatibility | 不改变计算结果；清单独立于方案；旧方案格式 v1 继续使用 / independent list workspace and compatible plan format |
| 主题与截图 / Themes/previews | 浅深色、最小窗口、图标和实际截图已检查 / both themes, minimum size, icons and actual previews checked |
| 源码自检 / Source check | 100 轮通过，含清单后台检查与取消 / 100 cycles passed with list checks/cancellation |
| 单文件自检 / Onefile check | 相同检查通过，版本及指纹与源码一致 / same checks passed, matching version and fingerprint |
| 既有功能 / Existing functions | 关于、许可、摘要、格式转换、双网段、方案、最大空间、TXT／XLSX 及取消保护通过 / existing core/file workflows passed |

源码和打包产物均通过 `subnet_list_unicode_import_and_background_relations` 与 `subnet_list_cancel_preserves_input`。自检使用临时偏好和文件，不写系统剪贴板；完整剪贴板回归结束时恢复原数据。

Both source and onefile passed Unicode list import/background relationship analysis and cancellation/input-preservation checks. Self-checks use temporary preferences/files without clipboard writes; full clipboard tests restore the original data.

## 性能样本 / Performance Samples

| 项目 / Item | 本次机器 / This run |
|---|---:|
| 5,000 条不同 CIDR / distinct CIDRs | 123.445352 ms |
| 5,000 条重复 CIDR / duplicate CIDRs | 78.293578 ms |
| 最大地址空间计算 / Full-space calculation | 0.010526 ms |
| 最大空间末页 200 条 / Final page | 0.675131 ms |
| TXT 100,000 条 / rows | 1.16707 s |
| XLSX 20,000 条 / rows | 0.27653 s |

清单数据为五次核心检查耗时中位数，不包含文本粘贴、文件选择或表格绘制；不代表相对旧版提速或 Windows 响应承诺。其余计算／分页同样为重复测量。内存测量仅统计 Python 分配，不包含 Qt 原生或完整进程；事件循环样本不足不能证明没有卡顿，短时循环不替代 Windows 缩放与至少 30 分钟日常使用验收。

List timings are medians of five core checks, excluding paste/dialog/table rendering. They are host/load measurements, not a speedup or Windows response guarantee. Memory covers Python allocations only. Insufficient event-loop samples do not prove absence of stalls; short loops do not replace Windows scaling and a 30-minute normal-use check.

## 使用范围 / Scope

- 输入：每行一个 IPv6 CIDR；整行 # 注释与空行忽略，不支持 CSV、Excel 或行尾注释。/ One CIDR per line, ignoring blank lines and whole-line # comments; no CSV/Excel/inline comments.
- 错误行不参与关系分析，统计基于原始有效条目配对；重复输入增加关系对数。/ Invalid lines are excluded; pair counts refer to original valid entries.
- 只保留最多 1,000 对明细，总数仍精确。去重不移除被包含子网，也不合并相邻网段。/ Details are bounded; counts are exact. Deduplication does not remove contained networks or aggregate adjacent ranges.
- 清单不写入计算方案，需要保留时复制内容或报告。空闲分配、网段聚合与多级规划尚未实现。/ Lists are not stored in calculation plans. Copy them to retain work. Allocation, aggregation and multi-level planning are not implemented.

## Windows 验证 / Windows Verification

覆盖源码后运行 `build.cmd`，再运行 `verify.cmd`，查看 `verification/SUMMARY.md` 和 `summary.json`。人工验收见 [WINDOWS_ACCEPTANCE.md](WINDOWS_ACCEPTANCE.md)。发布标签使用 `v1.3`，Releases 用户直接下载 `IPv6SubnetCalculator_V1.3.exe`。

After replacing source, run build.cmd and verify.cmd and review the reports/acceptance checklist. Use the tag v1.3; Releases users download the EXE directly.
