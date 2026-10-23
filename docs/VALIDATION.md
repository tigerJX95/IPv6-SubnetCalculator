## V1.13 — 2026-10-23

- 完整回归 541 项通过，包含原 CIDR 输出 17 项专项测试和本次新增 27 项翻译与异常测试。/ 541 regression tests passed, retaining 17 CIDR-output tests and adding 27 translation/error tests.
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
