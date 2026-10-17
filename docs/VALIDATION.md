# IPv6SubnetCalculator V1.0 验证记录 / Validation Record

日期 / Date: 2026-10-17

V1.0 在 V0.9 基础上新增 IPv6 地址格式转换、双网段关系分析和计算摘要复制；新增独立“地址工具”标签页。本轮同时统一加大界面字体及表格行高。以下结果来自本次更新后实际运行的 Linux 源码与重新构建的同一运行指纹单文件程序。Windows 自动、人工及长时间验收尚未执行。

V1.0 adds IPv6 address conversion, two-network relationship analysis, calculation summary copying, and an independent Address Tools tab to V0.9. This update also enlarges interface text and table rows. Results below come from the updated Linux source and rebuilt matching-fingerprint onefile executable. Windows automated, manual, and extended-session acceptance remain pending.

## 🐛 Windows 测试编码修正 / Windows Test Encoding Fix

用户上传的 Windows / Python 3.14.6 日志显示：212 项中 211 项通过，源码指纹变化测试因默认 GBK 解码 UTF-8 的临时源码副本而报错。已在本环境强制 GBK 默认编码复现同一异常。修正测试文本读写为显式 UTF-8 后，25 项相关测试在 GBK 默认编码模拟下通过，并新增一项持续回归。先前仅修正 GBK 测试时，运行代码未变；本次字体调整已改变运行源码与构建指纹，因此应在 Windows 覆盖源码后重新运行 `build.cmd` 和 `verify.cmd`，其余 Windows 自动阶段尚待该次运行确认。

The supplied Windows / Python 3.14.6 log shows 211 passes out of 212 tests, with one source-fingerprint test error from decoding a temporary UTF-8 source copy using GBK. The same error was reproduced with a forced GBK default. Explicit UTF-8 test I/O fixes it; 25 related tests pass under GBK-default simulation and a permanent regression was added. The earlier GBK-only fix left runtime code unchanged. This typography update changes runtime source and its fingerprint, so rebuild and rerun `verify.cmd` on Windows after replacing the source. The remaining Windows automated stages await that run.

测试过程中的窗口快速切换来自脚本反复开关窗口、切换主题、调整大小和最小化恢复，不是本次失败原因。表格仍只加载当前页，普通 EXE 启动不执行这些测试操作。

Rapid window changes during testing come from scripted open/close, theme, resize, and minimize/restore actions. They did not cause this failure. Only the current page is loaded, and normal EXE startup does not perform these test actions.

## 字体与布局 / Typography and Layout

- 常规文字 12 pt，等宽地址／结果 12 pt，二进制 11 pt，标题 28 px；统一维护在 `ui/fonts.py`。/ 12 pt interface and monospaced text, 11 pt binary, 28 px title, centralized in `ui/fonts.py`.
- 表格默认行高 38，序号列按实际字体度量计算；详情／导出弹窗增加空间。/ Row height 38, font-metric index column sizing, and more space in detail/export dialogs.
- 三个页面在 1080×800 的两种主题下生成实际截图；900×620 下滚动／换行正常，检查四类弹窗。/ Actual screenshots of all three tabs in both themes at 1080×800; scrolling/wrapping checked at 900×620 and four dialog types inspected.
- Windows 字体渲染、显示缩放及实机可读性仍待本地验收。/ Windows font rendering, display scaling and readability remain subject to local acceptance.

## 环境 / Environment

| 项目 / Item | 本次环境 / Environment |
|---|---|
| 应用 / Application | V1.0 |
| 系统 / OS | Linux x86_64, Qt offscreen |
| Python | 3.12.14 |
| PyQt6 / Qt | 6.11.0 / 6.11.2 |
| 打包检查 / Packaging | PyInstaller onefile，字体更新后重新构建并实际运行 / rebuilt and executed after typography update |
| 运行源码与资源 SHA-256 / Runtime source/resource fingerprint | `61abb4518cf979856ed919cc7fa6f4354f5da60648a8dcaf558ffc90467ee54a` |
| Windows 自动检查 / Automated checks | 未运行 / Not run |
| Windows 人工及长时间验收 / Manual and extended-session acceptance | 待完成 / Pending |

## 自动检查 / Automated Checks

| 检查 / Check | 结果 / Result |
|---|---|
| 全部回归 / Regression | 213 项通过 / passed |
| 摘要复制新增回归 / New summary-copy regression | 8 项通过：完整内容、规范化、最大整数、不变前缀／单地址、两种主题与快照、非法重算、剪贴板失败重试及初始禁用 / 8 passed, covering content, normalization, precision, boundaries, themes, snapshots, invalid input and clipboard recovery |
| 地址工具新增回归 / New address-tool regression | 18 项通过：格式与二进制精度、映射地址、非法输入、关系方向、边界、主题、状态独立、复制重试及最小窗口 / 18 passed, covering conversion, precision, mapped notation, invalid inputs, relationships, boundaries, themes, copying, independent state and minimum window |
| GBK 默认编码模拟 / GBK-default simulation | 25 项相关测试通过，含新增指纹编码回归 / 25 related tests passed, including the new encoding regression |
| 格式转换随机样本 / Conversion roundtrips | 300 个固定种子随机地址，三种输出均无损 / 300 seeded addresses, lossless outputs |
| 关系区间交叉验证 / Relationship interval cross-check | 225 对小网段与独立整数区间算法一致 / 225 pairs match an independent integer interval oracle |
| 合法前缀组合 / Valid prefix combinations | 8,385 组，与 Python ipaddress 交叉验证 / checked against Python ipaddress |
| 随机网段 / Random networks | 固定种子 300 组 / 300 seeded cases |
| 连续界面操作 / Continuous UI operations | 回归测试 150 轮，包含定位、选择、主题、标签与窗口大小切换 / 150 regression cycles |
| 源码程序 / Source application | 100 轮自检通过，包含摘要快照 / self-check cycles passed, including summary snapshots |
| 单文件打包程序 / Onefile executable | 100 轮自检通过，包含摘要快照 / self-check cycles passed, including summary snapshots |
| 极大结果 / Maximum result | `::/0 → /128` 的末页及最后序号 `2^128` 正确；摘要完整保留 `2^128`；每页最多 200 条 / correct final page and exact summary count; at most 200 rows loaded |
| 中文路径导出 / Unicode-path exports | 源码和单文件程序均完成 TXT／XLSX 后台导出 / source and onefile passed |
| 主题与许可资源 / Theme and license resources | 图标、主题箭头、项目及第三方许可文件正常加载 / loaded successfully |
| 构建对应 / Build matching | 源码与单文件程序的版本和源码／资源指纹一致 / matching version and fingerprint |
| Windows 发布 ZIP / Windows ZIP assembly | 4 项结构与失败保护测试通过；此环境未构建 Windows EXE / four assembly tests passed; no Windows EXE built here |

摘要格式独立维护在 `core/calculation_summary.py`，不依赖 Qt、不枚举子网、不使用浮点数。界面保存最后一次成功计算的快照；编辑输入不会混入摘要，非法重算后清空并禁用复制。自检不写入系统剪贴板；完整回归覆盖剪贴板交互并恢复原数据。格式转换和关系分析复用原有校验，均不枚举地址；两项工具输入分别使结果失效，切换主题或标签不改变计算器状态。三个页面的浅深色实际截图已更新并检查。

Summary formatting is isolated in `core/calculation_summary.py`, independent of Qt, without subnet enumeration or floating-point counts. The UI retains the last successful snapshot, excludes uncalculated edits, and clears/disables copying after invalid recalculation. Self-checks leave the clipboard unchanged; regression covers clipboard interaction and restores original data. Conversion and relationship analysis reuse input validation without enumerating addresses; editing invalidates each tool independently, while theme/tab switches preserve calculator state. Actual light/dark screenshots of all three pages were updated and inspected.

Windows 发布 ZIP 测试使用临时数据验证程序和六份许可文件的收集及失败保护，不等同于 Windows EXE 运行验收。

Windows ZIP tests use temporary fixtures to check executable/license collection and failure protection; they do not constitute Windows executable acceptance.

## 🐛 异常恢复与文件保护 / Error Recovery and File Protection

- 修复默认 GBK 环境读取 UTF-8 测试源码失败；测试文本读写显式指定 UTF-8。/ Fixes GBK-default decoding failure for UTF-8 test source; test text I/O explicitly uses UTF-8.
- 剪贴板失败保留计算结果，恢复后可再次复制；计算失败后禁用摘要复制。/ Clipboard failures retain results and allow retry; failed calculation disables summary copying.
- 导出线程启动失败、未实际启动或未返回结果时恢复操作。/ Controls recover from startup exceptions, silent failures and missing worker outcomes.
- 导出写入或替换失败、取消时保留原文件并清理临时文件；覆盖关闭等待与失败重试。/ Failed/cancelled exports preserve originals and clean temporary files; close-and-wait and retry are covered.
- 发布 ZIP 缺少输入或写入失败时，保留已有 ZIP 并清理未完成文件。/ Missing inputs or write failures preserve existing archives and clean incomplete files.

## 📊 性能样本 / Performance Samples

| 操作 / Operation | 本次测量 / Measurement |
|---|---:|
| `::/0 → /128` 计算，无预览 / Calculation without preview | 0.023418 ms |
| 最大空间末页，每页 200 条 / Final page, 200 rows | 1.240327 ms |
| 定位最后一个 IPv6 地址 / Locate final address | 0.01153 ms |
| IPv6 格式转换，最大地址 / Conversion of maximum address | 0.026205 ms |
| 双网段关系，最大空间包含单地址 / Full-space containment analysis | 0.07318 ms |
| TXT，100,000 条 / rows | 2.26541 s |
| XLSX，20,000 条 / rows | 0.46932 s |
| 首批 1,024 条后取消，场景总耗时 / Cancellation scenario after 1,024 rows | 0.04452 s |

计算、末页和定位为五组重复测量中单次平均耗时的中位数。导出使用最大空间的前 N 条。仅描述本次机器及负载，不包含冷启动／首次字体加载，不设依赖硬件的速度门槛，也不表示相对旧版的性能提升。

Calculation, pagination and location are medians of five batch-mean samples. Exports use the first N results of the full address space. Measurements describe this machine/load, exclude cold startup/initial font loading, use no hardware-dependent speed threshold, and imply no speedup over earlier versions.

## 导出内存 / Export Memory

| 格式 / Format | 1,000 条峰值 / peak bytes | 10,000 条峰值 / peak bytes |
|---|---:|---:|
| TXT | 7,616 | 7,617 |
| XLSX | 311,361 | 340,441 |

仅记录 tracemalloc 可见的 Python 分配量，不含 Qt 原生内存或进程总内存。短时循环不能替代 Windows 30 分钟实际使用及资源观察。

These are tracemalloc-visible Python allocations, excluding Qt/native memory and total process memory. Short loops do not replace a 30-minute Windows use session and resource observation.

## 后台事件循环采样 / Background Event-loop Samples

| 运行方式 / Mode | TXT 最大观察间隔 / maximum gap | XLSX 最大观察间隔 / maximum gap |
|---|---:|---:|
| Source | 215.562 ms | 35.21 ms |
| Onefile | 168.772 ms | 38.491 ms |

采用 10 ms Qt 定时器记录实际观察间隔，含当前负载与绘制影响，不代表帧率、所有交互的响应上限或 Windows 性能承诺。

A 10 ms Qt timer samples observed intervals, including load and painting effects. These are not frame rates, bounds for every interaction or Windows performance guarantees.

## Windows 复现 / Windows Reproduction

源码目录运行 `build.cmd`，再运行 `verify.cmd`；报告位于 `verification/`。Windows 构建生成 EXE、许可文件目录及 `IPv6SubnetCalculator_V1.0_Windows.zip`。人工项目见 [Windows 验收](WINDOWS_ACCEPTANCE.md)。

Run `build.cmd` then `verify.cmd` from the source folder. Reports appear in `verification/`. Windows builds create the EXE, licenses, and Windows ZIP. See [Windows Acceptance](WINDOWS_ACCEPTANCE.md) for manual checks.
