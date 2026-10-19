# 第三方组件 / Third-Party Components

以下组件用于界面及打包运行环境，其版权和许可由各上游项目持有。本项目自有代码及资源的许可见根目录 `LICENSE` 和 `NOTICE`；本文件不改变第三方组件的许可。

These components provide the interface and packaged runtime. Their copyright and licenses belong to their respective upstream projects. The license of project-authored code and assets is stated in the root LICENSE and NOTICE files. This notice does not change third-party licenses.

| 组件 / Component | 版本 / Version | 上游许可说明 / Upstream license information |
|---|---|---|
| PyQt6 | 6.11.0 | GNU GPL v3 / Riverbank commercial license; [upstream](https://www.riverbankcomputing.com/software/pyqt/intro) |
| Qt 6 runtime (`PyQt6-Qt6`) | 6.11.2 | LGPL v3 notice supplied by the installed wheel; individual Qt modules and third-party components retain their respective notices; [upstream](https://www.qt.io/licensing/) |
| PyQt6-sip | 13.13.0 | SIP license notice supplied by the installed wheel; [upstream](https://www.riverbankcomputing.com/software/sip/) |

随包保存的上游许可文本见 `docs/licenses/`。Windows 构建脚本也会收集已安装发行包的元信息，并把这些许可文本加入产物。组件安装包的完整说明及实际采用的授权方式应与发布配置保持一致。

Upstream license texts are retained in `docs/licenses/`. The Windows build also collects installed distribution metadata and includes these license texts. Full component notices and the applicable licensing arrangements should remain consistent with the release configuration.


## Qt 中文标准控件资源 / Chinese Standard-Widget Catalog

`assets/qtbase_zh_CN.qm` 为 PyQt6-Qt6 6.11.2 随附的 Qt 社区中文翻译，保留上游许可；本发行采用模块许可规则中的 LGPL-3.0-only 选项。说明见 `docs/licenses/Qt_Translations_NOTICE.txt`，对应上游 TS 源文件及许可规则保存在源码包 `docs/qttranslations/`。该资源不适用项目自有图标的版权声明。

The unmodified catalog comes from PyQt6-Qt6 6.11.2. This distribution uses the LGPL-3.0-only option in the Qt module license rule. Notices, upstream translation source and module rule are retained as described above.
