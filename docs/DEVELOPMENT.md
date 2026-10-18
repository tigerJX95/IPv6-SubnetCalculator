# V1.2 开发说明 / Development Notes

## 运行与构建 / Run and Build

安装 Python 3.10 或更新版本后，在项目根目录执行：

With Python 3.10 or newer installed, run from the project root:

```console
python -m pip install -r requirements.txt
python main.py
```

Windows 下运行 `build.cmd`，会安装固定版本的界面依赖和 PyInstaller，生成 `dist/IPv6SubnetCalculator_V1.2.exe`。构建需要联网下载依赖；生成后的程序离线运行，不要求目标电脑安装 Python。EXE 的架构取决于所用 Python 的架构，建议使用 Windows x64 Python。

On Windows, `build.cmd` installs the pinned interface dependencies and PyInstaller, then creates `dist/IPv6SubnetCalculator_V1.2.exe`. Building requires internet access to download dependencies. The resulting application works offline without Python on the target computer. Its architecture follows the Python interpreter used; Windows x64 Python is recommended.

可选运行 `python tools/package_release.py` 生成 `dist/IPv6SubnetCalculator_V1.2_Windows.zip`，包含 EXE、项目 `LICENSE`／`NOTICE` 及第三方许可文件。Windows 用户默认直接下载 EXE；ZIP 仅为可选归档，源码包单独提供。发布前运行 `verify.cmd` 检查本次 EXE。

Optionally run `python tools/package_release.py` to create `dist/IPv6SubnetCalculator_V1.2_Windows.zip`, containing the EXE, project LICENSE/NOTICE, and third-party license files. Publish the EXE as the default Windows download; the ZIP is optional and source is provided separately. Run `verify.cmd` before publishing to check the executable from this build.

## 模块职责 / Module Responsibilities

| 路径 / Path | 职责 / Responsibility |
|---|---|
| `main.py` | 启动入口 / Entry point |
| `app.py`, `app_info.py` | Qt 初始化、版本和资源路径 / Qt initialization, metadata, and resource paths |
| `core/calculation_plan.py` | 方案数据格式及校验 / Plan schema and validation |
| `services/plan_storage.py` | 有限 JSON 读写及原子替换 / Bounded JSON I/O and atomic replacement |
| `ui/plan_controller.py` | 方案保存、打开、另存为及恢复 / Save, open, Save As and restore |
| `core/ipv6_core.py` | IPv6 计算与输入校验 / Calculations and input validation |
| `core/address_conversion.py`, `core/network_relations.py` | 格式转换与双网段关系，复用输入校验 / Address conversion and network relations, reusing input validation |
| `core/calculation_summary.py` | 计算快照转纯文本摘要，不依赖 Qt / Pure-text calculation snapshot formatting, independent of Qt |
| `core/subnet_tools.py` | 定位、范围复制和选择统计 / Location, range copying, and selection statistics |
| `core/subnet_export.py`, `core/export_estimate.py` | 文件写入及容量估算 / File writing and size estimates |
| `core/address_usage.py`, `core/formatting.py` | 地址用途和精确数值显示 / Usage guidance and numeric formatting |
| `ui/main_window.py` | 页面及服务协调 / Page and service coordination |
| `ui/address_tools_page.py` | 独立地址工具界面 / Independent address tools UI |
| `ui/calculation_page.py` | 参数和计算摘要 / Parameters and summaries |
| `ui/results_page.py`, `ui/subnet_model.py` | 分页、定位、选择及当前页模型 / Pagination, location, selection, and current-page model |
| `ui/dialogs.py`, `ui/widgets.py` | 弹窗、图标与公共界面组件 / Dialogs, icons, and shared interface components |
| `ui/fonts.py` | 全局、等宽与二进制字体集中配置 / Central interface, monospaced, and binary font settings |
| `ui/theme.py` | 浅色／深色语义配色、应用切换与偏好保存 / Light/dark semantic colors, switching, and preference storage |
| `ui/export_controller.py` | 文件选择、确认和进度窗口 / File selection, confirmations, and progress UI |
| `services/clipboard_service.py` | 剪贴板与复制失败处理 / Clipboard access and error handling |
| `services/build_info.py`, `services/release_check.py` | 构建指纹及隔离自检 / Build fingerprint and isolated self-check |
| `tools/verify.py`, `tools/performance.py`, `tools/build_manifest.py` | 源码／EXE 验证、性能测量和构建清单 / Source/EXE verification, performance measurement, and build manifest |
| `ui/about_dialog.py` | 关于窗口、离线文档阅读及主题显示 / About window and offline document readers |
| `services/about_content.py` | 文档白名单、版本信息与资源读取 / Document allowlist, runtime information and loading |
| `docs/about/` | 内置使用说明和法律责任文本 / Embedded usage and legal text |
| `tools/package_release.py` | 整理 EXE 与许可文件，原子写入 Windows 发布 ZIP / Collect the EXE and licenses and atomically write the Windows release ZIP |
| `services/export_service.py` | 后台线程、进度、取消及完成通知 / Worker lifecycle, progress, cancellation, and completion |

`core` 不依赖 Qt。界面仅加载当前页；不能把 IPv6 的全量子网数量作为 Qt 表格行数。跨线程计数信号使用 Python 对象以保留大整数。窗口退出需先等待导出线程完成，不能强制终止正在写文件的线程。

`core` has no Qt dependency. The table loads only the current page; never use the entire IPv6 subnet count as a Qt row count. Cross-thread counters use Python objects to preserve large integers. Closing waits for export completion or cancellation; do not forcibly terminate a thread writing files.

## 检查 / Checks

```console
python -m unittest discover -s tests -v
```

Qt 界面测试使用实际控件与事件。无显示服务器的 Linux 环境可设置 `QT_QPA_PLATFORM=offscreen`。计算、范围、导出和精度测试与界面测试分别维护，未保留失效的 Tk 控件测试。

Qt tests exercise actual widgets and events. On headless Linux, set `QT_QPA_PLATFORM=offscreen`. Calculation, range, export, and precision checks are maintained separately from interface tests; obsolete Tk widget tests are not retained.

## 主题 / Themes

`ThemeManager` 使用 `QSettings('IPv6SubnetCalculator', 'Preferences')` 保存 `appearance/theme`，默认浅色。设置存储在当前用户配置中，不写入源码目录；偏好无法保存时仍允许本次切换并显示反馈。测试使用临时 INI 文件，不修改用户偏好。

`ThemeManager` stores `appearance/theme` using `QSettings('IPv6SubnetCalculator', 'Preferences')`, defaulting to light. Settings are per-user and do not write to the source folder. A preference write failure still allows the current switch and reports that it was not saved. Tests use a temporary INI file.

主题仅通过统一样式表设置控件颜色，不混用全局 `setPalette`。计算页滚动视口和内容明确设置背景，定位高亮从当前主题读取；主题变化只刷新显示，不重建计算结果或重置选择。原生系统文件选择器和窗口标题栏由操作系统绘制。

Widget colors come from one stylesheet, without mixing in global `setPalette`. Calculation scroll contents and viewport have explicit backgrounds; range highlighting reads the active theme. Switching refreshes appearance without rebuilding results or resetting selections. Native file dialogs and window title bars are drawn by the operating system.

## 发布源码与许可 / Source and License Distribution

项目自有内容采用 `GPL-3.0-or-later`；根目录 `LICENSE` 保存未经修改的 GPLv3 正文，`NOTICE` 明确许可版本、范围与无担保声明。第三方许可文件独立保留。

Project-authored content uses `GPL-3.0-or-later`. The root `LICENSE` contains the unmodified GPLv3 text; `NOTICE` identifies the versions, scope, and lack of warranty. Third-party license files are retained separately.

`build.cmd` 会将项目与第三方许可嵌入程序，并在 `dist/IPv6SubnetCalculator_V1.2_Licenses/` 输出可直接阅读的副本。该目录可作为独立许可附件保留；EXE 已嵌入许可文件。发布时提供与 EXE 对应版本的完整源码及构建材料（包括 `build.cmd`、`requirements.txt`、资源和开发说明）。源码可放在同一 Release 的源码附件中；确保该 Release 对应正确的提交和标签，不要仅链接到持续变化的主分支。

`build.cmd` embeds project and third-party license files in the application and also writes readable copies to `dist/IPv6SubnetCalculator_V1.2_Licenses/`. Retain that folder as an optional standalone license attachment; licenses are also embedded in the EXE. Provide the complete matching application source and build materials, including `build.cmd`, `requirements.txt`, assets, and these instructions. A source archive can accompany the same Release; use the matching commit and tag rather than linking only to a changing main branch.

程序包含的第三方组件仍须按各自许可履行源码、版权和再分发义务。完整源码的提供范围包括适用许可证要求的依赖源码；仅附上项目的 Python 文件或上游主页链接并不自动满足所有第三方二进制分发条件。组件版本及获取入口见 `THIRD_PARTY_NOTICES.md`，发布时应保留所用版本的依赖源码及构建信息。

Bundled third-party components retain their own source, attribution, and redistribution obligations. The source offer must also cover dependency source where required by the applicable licenses; providing only the application's Python files or an upstream home-page link does not automatically satisfy all third-party binary distribution conditions. Versions and upstream entry points are listed in `THIRD_PARTY_NOTICES.md`. Retain the dependency sources and build information for the versions actually shipped.

## V1.2 自动验证 / Automated Verification

Windows 下先运行 `build.cmd`，再运行 `verify.cmd`。验证入口执行回归测试、性能测量、源码程序检查和本次构建的 EXE 检查，将结果保存在 `verification/`，不加入 Git。

On Windows, run `build.cmd` followed by `verify.cmd`. Verification runs regression tests, performance measurements, source-application checks, and checks of the executable from this build. Reports are written to `verification/`, which is excluded from Git.

只检查源码可运行： / For source-only checks:

```console
python tools/verify.py --report-dir verification
```

指定打包程序可运行： / To include a packaged application:

```console
python tools/verify.py --exe dist/IPv6SubnetCalculator_V1.2.exe --report-dir verification
```

`summary.json` 保存环境、逐阶段结果及性能数据；`SUMMARY.md` 为简要结果，`tests.log` 保存回归日志；`source.json` 和 `executable.json` 分别记录源码与打包程序检查。源码检查通过时，未提供的 EXE 仍标记为 `not_run`。只有在 Windows 上执行且 EXE 检查通过后，`windows_automated_checks` 才标记为通过；人工验收始终独立登记，见 [Windows 验收](WINDOWS_ACCEPTANCE.md)。

`summary.json` records the environment, stage results, and performance metrics. `SUMMARY.md` is a short summary, and `tests.log` contains regression output. `source.json` and `executable.json` hold application checks. Without an executable, its stage remains `not_run`. Windows automated checks are marked passed only on Windows after a matching executable passes. Manual acceptance remains separate; see [Windows Acceptance](WINDOWS_ACCEPTANCE.md).

自检通过 `--self-check REPORT_JSON` 启动，使用临时偏好与临时导出目录，不修改正常主题设置或剪贴板。覆盖默认计算、完整 IPv6 空间末页、100 轮导航／选择、两种主题与许可资源、中文路径后台导出，以及取消后的原文件保留和临时文件清理。性能记录包括后台导出期间事件循环采样间隔，不将其解释为整个程序的帧率或响应时间上限。

The `--self-check REPORT_JSON` entry point uses temporary preferences and export files without modifying normal theme settings or the clipboard. It checks default calculations, the final page of the full IPv6 space, 100 navigation/selection cycles, both themes and license resources, background exports to Unicode paths, and cancellation cleanup. Background event-loop gaps are sampled; these samples are not a program-wide frame-rate or response-time guarantee.

构建前生成 `build_manifest.json`，记录运行源码及资源的 SHA-256 指纹，并嵌入 EXE。验证时同时核对版本和指纹，避免把同版本旧 EXE 当成本次源码产物；清单无需提交，`build.cmd` 会重新生成。

A pre-build `build_manifest.json` records a SHA-256 fingerprint of runtime source and resources and is embedded in the executable. Verification compares both version and fingerprint to detect stale executables with the same version. The generated manifest is excluded from Git and regenerated by `build.cmd`.

性能数据来自当前机器的重复测量，不设置依赖硬件的固定速度门槛。导出内存数据由 `tracemalloc` 记录，仅表示 Python 分配量，不包含 Qt 原生分配或完整进程内存。检查入口对意外的导出内存增长设置粗粒度回归保护。

Performance timings are measurements of the current machine, without fixed hardware-dependent speed thresholds. Export memory is measured with `tracemalloc` and covers Python allocations only, excluding native Qt allocations and total process memory. A coarse guard detects unexpected export-memory growth.

本轮环境与测量记录见 [V1.2 验证记录](VALIDATION.md)。 / See the [V1.2 validation record](VALIDATION.md) for this run and its environment.

## V1.2 发布范围 / Release Scope

V1.2 增加顶部关于入口，以及程序信息、离线帮助、许可原文和法律责任四页；延续本地计算方案保存与恢复。IPv6 子网导入与多网段规划保留在 V1.x 路线中；双网段关系分析延续既有功能。程序版本、EXE、Windows ZIP、源码包及发布说明统一使用 V1.2。异常与错误处理相关条目统一使用 🐛。

V1.2 adds the top-bar About entry and four pages for application information, offline help, license texts and legal notices, while retaining calculation-plan persistence. Subnet import and multi-network planning remain on the V1.x roadmap; two-network relationship analysis is retained. The application, EXE, Windows ZIP, source archive, and release notes use V1.2 consistently. Error-handling and bug-fix entries use 🐛.

发布说明草稿见 [V1.2 更新说明](RELEASE_NOTES.md)。实际验证记录见 [验证记录](VALIDATION.md)，其中 Windows 人工和长时间验收仅在实际完成后更新。

See [V1.2 Release Notes](RELEASE_NOTES.md). The [Validation Record](VALIDATION.md) tracks actual checks; update Windows manual and extended-session acceptance only after those checks have been performed.

## 计算摘要复制 / Calculation Summary Copying

`CalculationPage.set_result()` 根据成功计算的不可变结果生成摘要快照；输入编辑不改变快照，计算失败清空快照并禁用图标。页面通过信号交给主窗口调用统一 `ClipboardService`。摘要格式维护在 `core/calculation_summary.py`，不枚举子网，不使用浮点数。自检验证快照与最大整数，不更改系统剪贴板；剪贴板交互由 Qt 回归测试覆盖。

`CalculationPage.set_result()` formats an immutable successful-result snapshot. Input edits leave it unchanged; calculation failure clears it and disables the action. A signal lets MainWindow invoke the shared `ClipboardService`. Formatting lives in `core/calculation_summary.py`, without subnet enumeration or floating-point counts. Self-checks validate snapshots and maximum counts without touching the clipboard; Qt regression tests cover clipboard interaction.

## 地址工具 / Address Tools

格式转换复用 `validate_ipv6_address()`；完整展开明确生成 8 组十六进制，避免 Python 版本对 IPv4 映射尾部的显示差异。压缩表示沿用当前 Python `ipaddress`，IPv4 映射地址可能显示点分十进制尾部。关系分析复用 `calculate(..., preview_limit=0)` 的 CIDR 校验和规范化，以整数边界及 `subnet_of()` 判断，不遍历地址。间隔统计不含两段自身，首尾不环绕。

Conversion reuses `validate_ipv6_address()`. Expanded output explicitly generates eight hexadecimal groups to avoid Python-version differences for IPv4-mapped tails. Compressed notation follows the host Python `ipaddress` and may use a dotted-decimal mapped tail. Network analysis reuses `calculate(..., preview_limit=0)` for validation/normalization and uses integer bounds and `subnet_of()` without enumeration. Gap counts exclude both networks and boundaries never wrap.

输入编辑仅使对应工具结果失效。全部复制经过统一 `ClipboardService`。三个标签页共享主题但独立保留数据状态。参考：[Python ipaddress 文档](https://docs.python.org/3.12/library/ipaddress.html)。

Input edits invalidate only the corresponding tool. All copying uses `ClipboardService`. The three tabs share themes while retaining independent data. Reference: [Python ipaddress documentation](https://docs.python.org/3.12/library/ipaddress.html).

## 🐛 Windows 验证编码与窗口切换 / Verification Encoding and Window Switching

测试中读写源码、JSON 和 TXT 均明确指定 UTF-8，不依赖 Windows 默认区域编码。新增 GBK 默认编码回归，覆盖源码指纹变化场景；不要仅靠设置 `PYTHONIOENCODING` 修复文件编码，该设置仅影响标准流。

Test reads/writes of source, JSON and TXT explicitly use UTF-8 instead of the Windows locale default. A GBK-default regression covers source fingerprint modification. `PYTHONIOENCODING` controls standard streams and does not replace explicit file encodings.

完整回归会反复创建／关闭窗口、切换主题、改变窗口大小及最小化恢复；Windows 上可见快速闪动是这些自动操作的结果。表格始终只加载当前页，不会为巨量 IPv6 结果创建全量行。普通 EXE 启动不执行这些测试操作。自动回归在临时目录修改源码副本，不修改实际项目源码。

The full suite repeatedly creates/closes windows, switches themes, resizes, and minimizes/restores. Rapid visible changes on Windows result from those automated actions. The table loads only the current page even for huge IPv6 result sets. Normal EXE startup does not execute these tests. Fingerprint tests modify temporary source copies, not the working project.

## 字体 / Typography

`ui/fonts.py` 集中配置界面字体 12 pt、等宽文本 12 pt、密集二进制文本 11 pt 及标题 28 px。页面、数据模型、公共值标签和悬停提示使用统一配置；弹窗继承应用字体。序号列宽使用实际字体度量，表格默认行高 38。小窗口中计算页和工具页使用滚动、长文本换行。

`ui/fonts.py` centralizes 12 pt interface text, 12 pt monospaced text, 11 pt dense binary text, and the 28 px title. Pages, the data model, shared value labels, and tooltips use these settings; dialogs inherit the application font. Index-column sizing uses font metrics, with a default row height of 38. Calculation and Address Tools use scrolling/wrapping in smaller windows.

## V1.2 方案文件 / Plan Files

`core/calculation_plan.py` 定义格式与校验；`services/plan_storage.py` 负责有大小上限的 UTF-8 JSON 读写及原子替换；`ui/plan_controller.py` 协调文件选择、未保存提示和界面恢复。保存后只在参数、名称或备注变化时提示未保存，浏览变化仅随下一次保存记录。

The core defines schema/validation, the storage service handles bounded UTF-8 JSON and atomic replacement, and PlanController coordinates dialogs, unsaved prompts and restoration. Only parameter/name/note changes trigger unsaved prompts; view changes are captured on the next save.

方案格式见 [PLAN_FORMAT.md](PLAN_FORMAT.md)。方案保存恢复、异常保护与最大空间恢复均独立测试；`--self-check` 也包含临时中文路径的方案往返。

See [PLAN_FORMAT.md](PLAN_FORMAT.md). Dedicated tests cover restoration, failures and maximum-space plans; self-check includes a temporary Unicode-path roundtrip.

## 关于窗口资源 / About Resources

`services/about_content.py` 维护文档白名单与运行版本信息，`ui/about_dialog.py` 维护布局与阅读交互，`docs/about/USAGE.md` 和 `LEGAL.md` 可独立更新。`build.cmd` 将 `docs/about/` 与许可文件一并嵌入 EXE；这些文档也纳入构建指纹，自检逐项读取内容，避免源码与发布程序内容不一致。只有用户主动点击 HTTPS 上游链接时才调用系统浏览器。

The content service owns the document allowlist and runtime versions; the dialog owns presentation. The usage/legal documents can be maintained separately. The build embeds them alongside licenses, includes them in the source/resource fingerprint, and verifies their contents through the packaged self-check. Only user-activated HTTPS links open the system browser.
