## V1.14 — 2026-10-24

- 完整回归 561 项通过（原有 544 项及新增 17 项），0 失败／错误／跳过。/ All 561 regression tests passed (544 existing + 17 new), with no failures, errors or skips.
- 120 组随机占用集合与独立枚举的对齐子网对照，覆盖 /0、/128、全占用、重复／包含、主机位规范化、父网段越界、5,000 条输入及截断预览。/ 120 randomized occupied sets checked against independently enumerated aligned subnets, including /0, /128, full occupancy, duplicates, host-bit normalization, containment validation, 5,000 records and truncated previews.
- 新界面验证中英文、深浅主题、600×460 最小窗口、项目快照保留、错误显示、输入失效及 TXT 保存冲突。/ UI checks cover both languages/themes, 600×460 minimum size, snapshot isolation, errors, invalidation and TXT save conflicts.
- Ruff、pip check、TS/QM 一致性检查通过：772 条翻译、881 处源码调用、63 个文件。/ Ruff, pip check and catalog checks passed: 772 translations, 881 source calls, 63 files.
- 源码和 Linux 单文件程序各通过 31 项自检，版本和源码指纹一致；构建和验证批处理继续从 APP_VERSION 自动读取版本。/ Source and Linux one-file build each passed 31 self-checks, with matching version and source SHA-256; build.cmd and verify.cmd continue reading APP_VERSION dynamically.
- 结构化证据见 `../verification/v1.14/`。Windows EXE／实机及 GitHub 云端检查未在本轮运行；Qt 依赖保持不变，不代表已修复 Qt 漏洞。/ Evidence: `../verification/v1.14/`. Windows EXE/desktop and GitHub CI checks were not run in this iteration. Qt dependencies remain unchanged; no Qt vulnerability fix is claimed.

## V1.13 — 2026-10-23

- 修正 Windows Git 检出将 TS 换行转为 CRLF 时的生成记录误报；已验证 LF／CRLF／CR 等价，QM 字节变化仍拒绝。Windows Actions 复跑待上传修正文件。/ Fixed false stale-record failures after Windows text checkout conversion; LF/CRLF/CR checks pass and QM byte changes still fail. Windows Actions rerun is pending upload.

- 完整回归 544 项通过，包含原 CIDR 输出 17 项专项测试和30 项翻译与异常测试（含 3 项换行及二进制校验检查）。/ 544 regression tests passed, retaining 17 CIDR-output tests and 30 translation/error tests including three newline/binary integrity checks.
- 源码及 Linux 单文件程序各通过 30 项自检，版本与源码指纹一致。/ Source and Linux one-file application each passed 30 self-checks with matching version and source SHA-256.
- 762 条有效 TS/QM 翻译逐条一致；源码扫描检查 62 个文件、864 处翻译调用。/ 762 active catalog messages match QM; source coverage checks inspected 62 files and 864 translation calls.
- 覆盖 TS 漏编译、缺失／损坏 QM、空／未完成译文、重复上下文源文、格式字段变化、源码遗漏、编译失败保留原资源及译文格式回退。/ Covers stale compilation, missing/corrupt QM, empty/unfinished/duplicate entries, format-field changes, missing source translations, failed compilation preserving resources and runtime fallback.
- 原 CIDR 输出实现及专项测试文件未修改；中英文、深浅主题和最小窗口回归通过。/ Original CIDR output implementation and focused test files are unchanged; language/theme/minimum-window regression passed.
- Ruff、空白检查及 pip check 通过。/ Ruff, whitespace checks and pip check passed.
- 最终记录见 `validation/v1.13/`；Windows 构建及实机验证仍待完成，Qt 依赖不变，安全升级仍待处理。/ See `validation/v1.13/`; Windows build/desktop checks and the Qt security upgrade remain pending. Dependencies are unchanged.

# V1.12 修订验证记录 / Enhanced Revision Validation

日期 / Date: 2026-10-22

- 完整回归：492 项通过，0 失败、0 错误、0 跳过；新增 21 项清单查询与覆盖比较测试，保留原有草稿保护。
- 300 组固定种子随机集合对照验证新增、移除及交集；覆盖 /0 精确整数、边界地址、5,000 条上限、非法清单、等价拆分及重复包含。
- 界面测试覆盖双语来回切换、原始输入保留、报告失效、导入 JSON 不改变项目、损坏导入、复制、取消覆盖、保存期间输入变化及文件冲突。
- 源码与 Linux 单文件程序各通过 27 项自检，版本和源码指纹一致。
- 运行环境：Python 3.12.14、PyQt6 6.11.0、Qt 6.11.2，Linux x64。
- 实际控件截图检查了中英文、深浅主题、默认与最小窗口。截图环境临时加载 Noto Sans CJK 字体以显示中文；字体不随程序分发。
- Qt 依赖保持原基线，安全升级仍待处理。
- Windows EXE、高 DPI、系统文件窗口和本机文件占用行为仍待 Windows 验证；Linux 二进制未加入源码包。

Source SHA-256: `ef0a74d7a8f15c56823b59d803676560224ea9a0eae849c583c6ff5b79e52b75`

Structured evidence: `validation-v1.12/`.
