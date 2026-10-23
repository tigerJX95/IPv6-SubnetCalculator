# Qt 依赖状态 / Qt Dependency Status

核对日期 / Checked: 2026-10-23

| 项目 / Item | 状态 / Status |
|---|---|
| PyQt6 | 6.11.0 |
| PyQt6-Qt6 已发布最新 wheel / latest published wheel | 6.11.2 |
| PyQt6-sip | 13.13.0 |
| PyQt6-Qt6 6.11.3 / 6.12.0 发布包 / distributions | PyPI 官方元数据中均不存在 / absent from official PyPI metadata |
| PyQt6 绑定的 Qt 范围 / binding requirement | >=6.11.0, <6.12.0 |
| 公告建议 / advisory recommendation | 应用补丁或升级到 6.11.3 等已修复版本 / apply patches or upgrade to a fixed release such as 6.11.3 |
| D01 Qt 升级 / Qt upgrade | **未完成，等待可安装的兼容上游发布包 / pending a compatible installable upstream release** |

已同时核对 `pip index versions PyQt6-Qt6 --index-url https://pypi.org/simple` 和官方 JSON 元数据，最新版本均为 6.11.2。Windows x64、ARM64 的最新 wheel 同样是 6.11.2。不能仅把 requirements.txt 改成尚未发布的 6.11.3，也不能把已存在 EXE 当成已升级。

Both the official PyPI index and JSON metadata report 6.11.2 as latest. Windows x64 and ARM64 wheels are also 6.11.2. requirements.txt remains installable; an unpublished version is not declared as a completed upgrade, and an existing EXE is not updated by editing dependency declarations.

方案导入仍使用 Python json.loads，应用代码未使用 QJsonDocument/QBinaryJson。尚未确认本程序存在利用链；D01 仍保留为待处理依赖风险。上游兼容包可用后，需实际安装、更新 requirements 与组件说明、重建 EXE，再完成窗口/双语/主题/导出回归。本次修复 A01、A02、A03，不宣称 D01 已关闭。

Plan import uses Python json.loads rather than QJsonDocument/QBinaryJson. No application exploit chain was established. D01 remains an open dependency concern. Once a compatible fixed wheel is available, install it, update requirements/notices, rebuild and repeat dialog, bilingual, theme and export checks. This revision addresses A01/A02/A03, not D01.

Sources:
- [Qt 原始公告 / original advisory](https://www.qt.io/blog/security-advisory-cve-2026-101201)
- [PyQt6-Qt6 官方元数据 / official metadata](https://pypi.org/pypi/PyQt6-Qt6/json)
- [PyQt6 官方元数据 / official metadata](https://pypi.org/pypi/PyQt6/json)

2026-10-23：再次检查 Qt 官方安全公告（最新 10 月 21 日）和 PyPI（PyQt6-Qt6 最新 6.11.2），仍无兼容修复 wheel。/ Rechecked official Qt security notices (latest October 21) and PyPI (PyQt6-Qt6 latest 6.11.2); a compatible fixed wheel is still unavailable.
