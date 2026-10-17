# V0.9 开发说明 / Development Notes

## 运行与构建 / Run and Build

安装 Python 3.10 或更新版本后，在项目根目录执行：

With Python 3.10 or newer installed, run from the project root:

```console
python -m pip install -r requirements.txt
python main.py
```

Windows 下运行 `build.cmd`，会安装固定版本的界面依赖和 PyInstaller，生成 `dist/IPv6SubnetCalculator_V0.9.exe`。构建需要联网下载依赖；生成后的程序离线运行，不要求目标电脑安装 Python。EXE 的架构取决于所用 Python 的架构，建议使用 Windows x64 Python。

On Windows, `build.cmd` installs the pinned interface dependencies and PyInstaller, then creates `dist/IPv6SubnetCalculator_V0.9.exe`. Building requires internet access to download dependencies. The resulting application works offline without Python on the target computer. Its architecture follows the Python interpreter used; Windows x64 Python is recommended.

## 模块职责 / Module Responsibilities

| 路径 / Path | 职责 / Responsibility |
|---|---|
| `main.py` | 启动入口 / Entry point |
| `app.py`, `app_info.py` | Qt 初始化、版本和资源路径 / Qt initialization, metadata, and resource paths |
| `core/ipv6_core.py` | IPv6 计算与输入校验 / Calculations and input validation |
| `core/subnet_tools.py` | 定位、范围复制和选择统计 / Location, range copying, and selection statistics |
| `core/subnet_export.py`, `core/export_estimate.py` | 文件写入及容量估算 / File writing and size estimates |
| `core/address_usage.py`, `core/formatting.py` | 地址用途和精确数值显示 / Usage guidance and numeric formatting |
| `ui/main_window.py` | 页面及服务协调 / Page and service coordination |
| `ui/calculation_page.py` | 参数和计算摘要 / Parameters and summaries |
| `ui/results_page.py`, `ui/subnet_model.py` | 分页、定位、选择及当前页模型 / Pagination, location, selection, and current-page model |
| `ui/dialogs.py`, `ui/widgets.py` | 弹窗、图标与公共界面组件 / Dialogs, icons, and shared interface components |
| `ui/theme.py` | 浅色／深色语义配色、应用切换与偏好保存 / Light/dark semantic colors, switching, and preference storage |
| `ui/export_controller.py` | 文件选择、确认和进度窗口 / File selection, confirmations, and progress UI |
| `services/clipboard_service.py` | 剪贴板与复制失败处理 / Clipboard access and error handling |
| `services/build_info.py`, `services/release_check.py` | 构建指纹及隔离自检 / Build fingerprint and isolated self-check |
| `tools/verify.py`, `tools/performance.py`, `tools/build_manifest.py` | 源码／EXE 验证、性能测量和构建清单 / Source/EXE verification, performance measurement, and build manifest |
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

`build.cmd` 会将项目与第三方许可嵌入程序，并在 `dist/IPv6SubnetCalculator_V0.9_Licenses/` 输出可直接阅读的副本。发布程序时附带该目录，并提供与 EXE 对应版本的完整源码及构建材料（包括 `build.cmd`、`requirements.txt`、资源和开发说明）。源码可放在同一 Release 的源码附件中；确保该 Release 对应正确的提交和标签，不要仅链接到持续变化的主分支。

`build.cmd` embeds project and third-party license files in the application and also writes readable copies to `dist/IPv6SubnetCalculator_V0.9_Licenses/`. Include that folder with the binary release and provide the complete matching application source and build materials, including `build.cmd`, `requirements.txt`, assets, and these instructions. A source archive can accompany the same Release; use the matching commit and tag rather than linking only to a changing main branch.

程序包含的第三方组件仍须按各自许可履行源码、版权和再分发义务。完整源码的提供范围包括适用许可证要求的依赖源码；仅附上项目的 Python 文件或上游主页链接并不自动满足所有第三方二进制分发条件。组件版本及获取入口见 `THIRD_PARTY_NOTICES.md`，发布时应保留所用版本的依赖源码及构建信息。

Bundled third-party components retain their own source, attribution, and redistribution obligations. The source offer must also cover dependency source where required by the applicable licenses; providing only the application's Python files or an upstream home-page link does not automatically satisfy all third-party binary distribution conditions. Versions and upstream entry points are listed in `THIRD_PARTY_NOTICES.md`. Retain the dependency sources and build information for the versions actually shipped.

## V0.9 自动验证 / Automated Verification

Windows 下先运行 `build.cmd`，再运行 `verify.cmd`。验证入口执行回归测试、性能测量、源码程序检查和本次构建的 EXE 检查，将结果保存在 `verification/`，不加入 Git。

On Windows, run `build.cmd` followed by `verify.cmd`. Verification runs regression tests, performance measurements, source-application checks, and checks of the executable from this build. Reports are written to `verification/`, which is excluded from Git.

只检查源码可运行： / For source-only checks:

```console
python tools/verify.py --report-dir verification
```

指定打包程序可运行： / To include a packaged application:

```console
python tools/verify.py --exe dist/IPv6SubnetCalculator_V0.9.exe --report-dir verification
```

`summary.json` 保存环境、逐阶段结果及性能数据；`SUMMARY.md` 为简要结果，`tests.log` 保存回归日志；`source.json` 和 `executable.json` 分别记录源码与打包程序检查。源码检查通过时，未提供的 EXE 仍标记为 `not_run`。只有在 Windows 上执行且 EXE 检查通过后，`windows_automated_checks` 才标记为通过；人工验收始终独立登记，见 [Windows 验收](WINDOWS_ACCEPTANCE.md)。

`summary.json` records the environment, stage results, and performance metrics. `SUMMARY.md` is a short summary, and `tests.log` contains regression output. `source.json` and `executable.json` hold application checks. Without an executable, its stage remains `not_run`. Windows automated checks are marked passed only on Windows after a matching executable passes. Manual acceptance remains separate; see [Windows Acceptance](WINDOWS_ACCEPTANCE.md).

自检通过 `--self-check REPORT_JSON` 启动，使用临时偏好与临时导出目录，不修改正常主题设置或剪贴板。覆盖默认计算、完整 IPv6 空间末页、100 轮导航／选择、两种主题与许可资源、中文路径后台导出，以及取消后的原文件保留和临时文件清理。性能记录包括后台导出期间事件循环采样间隔，不将其解释为整个程序的帧率或响应时间上限。

The `--self-check REPORT_JSON` entry point uses temporary preferences and export files without modifying normal theme settings or the clipboard. It checks default calculations, the final page of the full IPv6 space, 100 navigation/selection cycles, both themes and license resources, background exports to Unicode paths, and cancellation cleanup. Background event-loop gaps are sampled; these samples are not a program-wide frame-rate or response-time guarantee.

构建前生成 `build_manifest.json`，记录运行源码及资源的 SHA-256 指纹，并嵌入 EXE。验证时同时核对版本和指纹，避免把同版本旧 EXE 当成本次源码产物；清单无需提交，`build.cmd` 会重新生成。

A pre-build `build_manifest.json` records a SHA-256 fingerprint of runtime source and resources and is embedded in the executable. Verification compares both version and fingerprint to detect stale executables with the same version. The generated manifest is excluded from Git and regenerated by `build.cmd`.

性能数据来自当前机器的重复测量，不设置依赖硬件的固定速度门槛。导出内存数据由 `tracemalloc` 记录，仅表示 Python 分配量，不包含 Qt 原生分配或完整进程内存。检查入口对意外的导出内存增长设置粗粒度回归保护。

Performance timings are measurements of the current machine, without fixed hardware-dependent speed thresholds. Export memory is measured with `tracemalloc` and covers Python allocations only, excluding native Qt allocations and total process memory. A coarse guard detects unexpected export-memory growth.

本轮环境与测量记录见 [V0.9 验证记录](VALIDATION.md)。 / See the [V0.9 validation record](VALIDATION.md) for this run and its environment.
