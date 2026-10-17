# V0.8 开发说明 / Development Notes

## 运行与构建 / Run and Build

安装 Python 3.10 或更新版本后，在项目根目录执行：

With Python 3.10 or newer installed, run from the project root:

```console
python -m pip install -r requirements.txt
python main.py
```

Windows 下运行 `build.cmd`，会安装固定版本的界面依赖和 PyInstaller，生成 `dist/IPv6SubnetCalculator_V0.8.exe`。构建需要联网下载依赖；生成后的程序离线运行，不要求目标电脑安装 Python。EXE 的架构取决于所用 Python 的架构，建议使用 Windows x64 Python。

On Windows, `build.cmd` installs the pinned interface dependencies and PyInstaller, then creates `dist/IPv6SubnetCalculator_V0.8.exe`. Building requires internet access to download dependencies. The resulting application works offline without Python on the target computer. Its architecture follows the Python interpreter used; Windows x64 Python is recommended.

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

`build.cmd` 会将项目与第三方许可嵌入程序，并在 `dist/IPv6SubnetCalculator_V0.8_Licenses/` 输出可直接阅读的副本。发布程序时附带该目录，并提供与 EXE 对应版本的完整源码及构建材料（包括 `build.cmd`、`requirements.txt`、资源和开发说明）。源码可放在同一 Release 的源码附件中；确保该 Release 对应正确的提交和标签，不要仅链接到持续变化的主分支。

`build.cmd` embeds project and third-party license files in the application and also writes readable copies to `dist/IPv6SubnetCalculator_V0.8_Licenses/`. Include that folder with the binary release and provide the complete matching application source and build materials, including `build.cmd`, `requirements.txt`, assets, and these instructions. A source archive can accompany the same Release; use the matching commit and tag rather than linking only to a changing main branch.

程序包含的第三方组件仍须按各自许可履行源码、版权和再分发义务。完整源码的提供范围包括适用许可证要求的依赖源码；仅附上项目的 Python 文件或上游主页链接并不自动满足所有第三方二进制分发条件。组件版本及获取入口见 `THIRD_PARTY_NOTICES.md`，发布时应保留所用版本的依赖源码及构建信息。

Bundled third-party components retain their own source, attribution, and redistribution obligations. The source offer must also cover dependency source where required by the applicable licenses; providing only the application's Python files or an upstream home-page link does not automatically satisfy all third-party binary distribution conditions. Versions and upstream entry points are listed in `THIRD_PARTY_NOTICES.md`. Retain the dependency sources and build information for the versions actually shipped.
