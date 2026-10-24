# 翻译维护 / Translation Maintenance

## 文件与机制 / Files and mechanism

中文模板位于 `text()` 调用，英文译文独立维护于 `assets/i18n/app_en.ts`，运行时 Qt 加载 `app_en.qm`。`app_en.catalog.json` 记录生成时 TS/QM 的 SHA-256（TS 统一 LF 换行，QM 按原始字节），便于发现漏编译和错配；它不是数字签名或安全认证。核心计算和序列化使用原始数据。现有语言仍为简体中文和 English。

Chinese templates are marked with `text()`; English translations are maintained separately in `assets/i18n/app_en.ts`. Qt loads `app_en.qm` at runtime. `app_en.catalog.json` records the generated pair's SHA-256 (LF-normalized TS text and byte-exact QM) to detect stale or mismatched files; it is not a digital signature or authenticity mechanism. Calculations and serialization use original data. Supported languages remain Simplified Chinese and English.

## 更新 / Updating

1. 给展示模板添加 `text()` 标记，在 TS 的 App 上下文补齐译文；导出表头使用 Export 上下文。不要标记路径、正则表达式、用户备注或协议字段。
2. 保留全部格式字段、格式说明及转换标记，例如 `{0:,}`、`{1!r}`。允许调整字段顺序。不得留下空译文、unfinished 状态或重复上下文／源文条目。
3. 使用已安装的 Qt Linguist 工具编译并检查：

```console
python tools/update_translations.py --lrelease "C:\Qt\Tools\QtLinguist\lrelease.exe"
python tools/check_i18n.py --report verification/i18n.json
```

`--lrelease` 使用实际可执行文件路径；也可从 PATH 查找 `lrelease` 或 `pyside6-lrelease`。普通使用和 `build.cmd` 只使用预编译 QM，不要求安装翻译编译器，也不引入 PySide 运行依赖。`tools/build_manifest.py` 在生成构建清单之前执行翻译检查，失败即停止构建。

Add marked display templates and matching TS entries (App context; Export for workbook labels). Preserve format fields/specifiers/conversions, but reorder them when appropriate. Run the commands above using your actual Qt Linguist path. The updater stages compilation and validation before replacing QM and writing the generation record. Normal application use and builds need only the supplied compiled QM; no translation compiler or PySide runtime dependency is added. Build-manifest generation runs the checks and stops on failure.

## 检查边界 / Check scope

- 自动比对所有有效 TS 条目的 QM 译文与上下文，并检查生成记录、空／未完成译文、重复键、格式字段及英文译文残留中文（语言自称“简体中文”除外）。
- AST 扫描覆盖 core/ui/services 与入口文件中的 `text()` 导入别名、显式翻译调用和常用界面文本构造／设置方法。Qt 原生 QLineEdit 上下文使用 Qt 自带目录。注释、用户数据、许可证原文不按关键词自动改写。
- 扫描不是任意动态 Python 代码的完整证明；新增展示封装或动态生成内容仍需扩展检测规则，并做实际界面回归。动态 text() 模板会被拒绝，以便源模板可静态核对。
- 运行时格式回退只保护译文错误；源模板自身的编程错误仍需修复。操作系统未知错误及第三方原始信息不保证逐字自动翻译。

The checker compares every active TS message with QM in its context and verifies the generation record, completion, duplicate keys, format fields and residual Chinese (except the native language name). AST coverage recognizes imported text() aliases, explicit translation calls and common UI construction/setter APIs. It does not prove coverage of arbitrary dynamic Python; new wrappers and generated content require rules and UI tests. User data, parsing syntax and original licenses stay untouched. Runtime fallback handles malformed translations rather than concealing invalid source templates. Unknown external errors are not automatically machine-translated.

## V1.13 整合范围 / Integration scope

保留地址归属匹配 CIDR 输出、新增／移除／共同覆盖的最简 CIDR 输出及其保存保护；版本仍为 V1.13。Qt 安全升级仍待可安装的兼容运行库。本次不修改 GitHub 仓库。

Retains membership CIDR output, minimal added/removed/common coverage lists and save protection. Version stays V1.13. The Qt security upgrade remains pending an installable compatible runtime. No GitHub repository changes are published.
