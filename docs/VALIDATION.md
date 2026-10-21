# V1.11 验证记录 / Validation

日期 / Date: 2026-10-21

- 最终源码完整回归：457 项通过，0 失败、0 错误、0 跳过；新增规划项目专项测试 17 项。
- Source and Linux single-file build: 24 self-check workflows passed in each; version and source fingerprint match.
- 实际运行环境 / Runtime: Python 3.12.14, PyQt6 6.11.0, Qt 6.11.2, Linux x64.
- Full regression finished in 273.067 seconds. Calculation, last-page browsing, TXT/XLSX export and memory measurements are in `validation-v1.11/performance.json`.
- 草稿原文与注释、空清单、1 MiB 边界、严格字段、重复 JSON 键、坏文件、Unicode、外部新建文件冲突及恢复副本均已验证。
- 取消替换、对话框期间输入变化、忙碌保护、双语状态、两种主题和 900×620 窗口均已覆盖。另用中文字体重新检查新功能窗口布局及截图。
- 规划项目需手动保存；关闭窗口暂不自动保存或提示规划项目未保存。Ctrl+S/Ctrl+O 仍属于计算方案。
- Qt dependency pins unchanged: PyQt6 6.11.0, PyQt6-Qt6 6.11.2, PyQt6-sip 13.13.0. Pending security upgrade is NOT completed or claimed fixed.
- Windows EXE build, Windows file dialogs, high DPI rendering and manual acceptance remain pending. Linux binary is validation-only and is not included in the source archive.

Source SHA-256: `5d15cdd59ab708e00a784f54f92f9b286d432de1211500d51c0a20a94f4ef5a8`

## Windows 验收 / Acceptance

1. 完整解压，运行 `build.cmd`；确认产物名为 `IPv6SubnetCalculator_V1.11.exe`。
2. 在子网清单输入注释、清单及父网段和分配参数，点击顶部保存图标保存 JSON。
3. 修改输入，再点击顶部打开图标，取消时保留当前内容；确认时恢复原文，旧结果清空。
4. 重新计算空闲空间并生成建议，检查中英文及浅深色主题。
5. 覆盖已有项目时取消应保留原文件；冲突时检查提示及完整恢复文件。
6. 检查旧计算方案 JSON、TXT/XLSX 导出及原有快捷键仍正常。
