# IPv6SubnetCalculator V1.1 验证记录 / Validation Record

日期 / Date: 2026-10-18

V1.1 在最新 V1.0（字体及 Windows 编码修正）基础上增加本地计算方案。此记录来自 Linux 实际运行，Windows 自动、人工及长时间验收仍待本地完成。

V1.1 adds local calculation plans to the latest V1.0 typography/encoding baseline. This record comes from actual Linux runs; Windows automated, manual and extended-session acceptance remain pending.

## 环境 / Environment

| 项目 / Item | 记录 / Record |
|---|---|
| 应用 / Application | V1.1 |
| 系统 / OS | Linux-6.18.55-x86_64-with-glibc2.39, x86_64, Qt offscreen |
| Python | 3.12.14 |
| PyQt6 / Qt | 6.11.0 / 6.11.2 |
| 打包 / Packaging | Linux PyInstaller onefile，实际运行 / built and executed |
| 运行源码及资源 SHA-256 / Fingerprint | `04820ce80122c2e17f1877509e2021b00e51d781abae157485ff2e825f292dfa` |
| Windows EXE | 本环境未构建或运行 / not built or run here |

## 自动检查 / Automated Checks

| 检查 / Check | 结果 / Result |
|---|---|
| 完整回归 / Full regression | 227 项通过 / passed |
| 方案新增回归 / New plan regression | 14 项：7 项格式／存储 + 7 项界面流程 / 7 schema/storage and 7 UI-flow tests |
| 最大空间方案 / Maximum-space plan | `::/0 → /128` 末页、最后序号、定位和选择恢复准确；方案小于 2 KiB / exact restoration with a plan under 2 KiB |
| 源码自检 / Source self-check | 100 轮操作通过，含中文路径方案往返 / 100 cycles passed, including Unicode-path plan roundtrip |
| 单文件自检 / Onefile self-check | 100 轮操作通过，含中文路径方案往返 / 100 cycles passed, including plan roundtrip |
| 构建匹配 / Build match | 源码／打包程序版本和指纹一致 / matching version and fingerprint |
| 计算边界 / Calculation coverage | 8,385 对前缀、300 组随机网段及最大空间末页 / prefix pairs, seeded networks and maximum-space final page |
| 地址工具 / Address tools | 格式转换、双网段关系及复制回归通过 / conversion, relationships and copying passed |
| 主题与资源 / Themes/resources | 两种主题、图标和许可资源正常 / both themes, icons and licenses loaded |
| 后台导出 / Background exports | 中文路径 TXT 100,000 条、XLSX 20,000 条及取消保护通过 / Unicode-path exports and cancellation protection passed |

源码与单文件程序使用相同自检入口；自检使用临时偏好和文件，不更改系统剪贴板。完整回归的剪贴板测试会恢复原数据。浅深色实际截图已更新并检查。

Source and onefile use the same self-check with temporary preferences/files and no clipboard writes. Full clipboard regression restores original data. Actual light/dark previews were updated and inspected.

## 🐛 方案与文件保护 / Plan and File Protection

- 校验格式标识／版本、必需字段、类型、名称备注限额、页码、定位与当前页选择；拒绝重复 JSON 字段、非法数值、非 UTF-8 或超出 64 KiB 的文件。/ Validates schema, limits and view state; rejects duplicate fields, invalid constants, non-UTF-8 and oversized files.
- 损坏文件、文件选择取消、未保存提示选择取消时保留当前工作。/ Invalid input and cancelled open/unsaved prompts retain current work.
- 写入及原子替换失败保留原方案，清理临时文件。/ Failed writing/replacement preserves originals and removes temporary files.
- 输入参数修改后须重新计算才能保存；已保存方案 Ctrl+S 直接更新，Ctrl+Shift+S 另存为。/ Edited parameters require recalculation; Ctrl+S updates the current file, Ctrl+Shift+S saves a copy.
- 关闭与打开前仅对参数／名称／备注的未保存更改提示；翻页和选择在下次保存时记录。/ Parameter/name/note edits trigger prompts; navigation is captured on the next save.

## 性能样本 / Performance Samples

| 项目 / Item | 本次机器 / This run |
|---|---:|
| 最大空间计算 / Full-space calculation | 0.009696 ms |
| 最大空间末页 200 条 / Final page, 200 rows | 0.553953 ms |
| 末地址定位 / Locate final address | 0.005368 ms |
| TXT 100,000 条 / rows | 0.84453 s |
| XLSX 20,000 条 / rows | 0.23622 s |
| 首批后取消场景 / Cancellation scenario | 0.0093 s |

计算／翻页／定位为五组重复测量的单次平均耗时中位数。数据仅描述本次机器和负载，不代表相对旧版提速或 Windows 性能承诺。导出内存以 tracemalloc 测量，TXT 1,000／10,000 条峰值为 [7616, 7617] 字节，XLSX 为 [311361, 340441] 字节，不含 Qt 原生或总进程内存。事件循环采样不足时不能据此宣称没有卡顿；短时自动循环不替代 Windows 实际响应与 30 分钟使用验收。

Calculation/navigation/location are medians of five batch-mean samples. Results describe this machine/load, not a speedup or Windows performance guarantee. Export memory tracks Python allocations only, excluding Qt/native and process totals. Insufficient event-loop samples cannot establish absence of stalls. Short loops do not replace Windows response checks and a 30-minute use session.

## 本地验证 / Local Verification

覆盖项目源码后运行 `build.cmd`，再运行 `verify.cmd`，查看 `verification/`。Windows 用户直接从 Releases 下载 EXE；发布 ZIP 为可选归档。人工项目见 [WINDOWS_ACCEPTANCE.md](WINDOWS_ACCEPTANCE.md)，方案格式见 [PLAN_FORMAT.md](PLAN_FORMAT.md)。

After replacing source, run `build.cmd` and `verify.cmd`, then review `verification/`. The EXE is the default Releases download; ZIP is optional. See the acceptance and plan-format documents.
