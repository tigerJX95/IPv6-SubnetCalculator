# V1.13 翻译机制整合 / Translation Integration

日期 / Date: 2026-10-23

以已完成 V1.13 源码 ZIP 为基线，逐文件核对后整合；原 CIDR 输出实现和专项回归保留。此前逐条 TS/QM 测试仍保留，新增可独立运行的构建检查、源码模板覆盖检查与格式错误回退。

The completed V1.13 ZIP was compared with the working tree before integration. CIDR output features and regression tests remain. Existing per-entry catalog tests are retained and complemented by standalone build checks, source coverage checks and malformed-translation fallback.

已确认可复现的健壮性问题：错误译文使用 `{1}` 替代 `{0}` 时可能触发 IndexError；多行源文选取第二行而译文只含一行时也可能触发 IndexError。现已回退原文，并保留对无效源模板的错误报告。目录检查的缺口属于维护检查不足。本次未确认新的安全漏洞，不把潜在依赖风险写成已修复漏洞；Qt 风险状态保持待处理。

Confirmed reproducible robustness issues: a translated field `{1}` replacing `{0}` could raise IndexError, and a translated multiline message with fewer lines could also raise IndexError when a later line was selected. Both now fall back to source content; invalid source templates still raise programming errors. Catalog-check gaps are maintenance limitations. No new security vulnerability is claimed; pending native Qt risks are not marked fixed.

实现、使用方法及静态扫描边界见 [I18N_MAINTENANCE.md](I18N_MAINTENANCE.md)，最终验证记录见 [VALIDATION.md](VALIDATION.md)。下方保留既有版本检查记录。

# V1.9 双语窗口检查 / Bilingual Window Audit

日期 / Date: 2026-10-20

本次为 V1.9 的双语一致性修订，版本号保持 V1.9。检查包含简体中文、English，以及窗口打开时双向切换。实际环境为 Linux Qt offscreen；另以相反系统语言的文件类型说明进行模拟验证。Windows 实机验证单独保留。
This revision retains V1.9 and checks Chinese, English and live switching. Tests run with Linux Qt offscreen, including simulated native file-type strings in the opposite language. Windows verification remains separate.

## 本轮修复 / Fixes

1. 简体中文文件选择器中 File Folder 改为“文件夹”；文件类型、大小、日期及列名由应用语言统一展示。
2. 第三方组件概览改为对应语言的说明，修正 English 模式下的中英混排。
3. 动态组合的字段标签、关系分析状态、规划错误行号及主题无障碍说明使用完整双语模板，消除英文中的中文冒号、句号和分隔符。

1. File-list folder/type labels, sizes, dates and headers now follow the application language.
2. The component overview uses a localized document instead of mixed-language content.
3. Assembled labels, status messages, planning errors and accessible theme text use localized punctuation.

## 检查矩阵 / Coverage Matrix

| 范围 / Area | 内容 / Checks | 证据 / Evidence |
|---|---|---|
| 子网计算 / Calculation | 分组标题、字段、摘要、状态、错误、悬停及无障碍名称 / headings, fields, summary, feedback and accessibility | 双向窗口扫描及既有回归 / live scans and existing regression |
| 子网结果 / Results | 表头、前三行展示、定位模式、分页与选择统计 / headers, sample rows, locator and paging | 窗口扫描与定位／选择回归 / scans and workflow tests |
| 地址工具 / Address tools | 格式转换、双网段关系、地址范围转 CIDR 及主机位规范化提示 / all tools and normalization status | 扫描、动态模板及状态保留测试 / widget, template and state tests |
| 子网清单 / Subnet list | 校验、关系、保存菜单、报告及错误 / validation, relationships, save menus and feedback | 扫描、TXT 及错误回归 / scans and output tests |
| 空闲／整理 / Planning | 标题、按钮、提示、表头、保存和回流 / headings, actions, headers, saving and transfer | 双语扫描及完整／截断结果回归 / scans and result tests |
| 指定范围复制 / Range copy | 窗口、字段、提示与校验错误 / dialog, fields and errors | 现有及新增窗口测试 / dialog regression |
| 子网详情 / Subnet detail | 标题、范围、字段、复制与导航 / heading, values and actions | 双向窗口扫描 / live scans |
| 导出范围 / Export range | 选项、字段、错误与确认 / options, fields and validation | 双向窗口和既有导出测试 / dialog and export tests |
| 导出进度 / Progress | 大整数进度、取消提示及打开时切换 / exact counters, cancellation and live switching | 新增窗口回归 / new dialog tests |
| 文件窗口 / File pickers | 计算导出、方案打开／保存、清单导入、TXT 保存 / all five entry points | 实际 Qt 控件扫描 / actual widget scans |
| 文件列表 / File metadata | 文件夹、已支持类型、未知扩展名、大小、日期和表头 / folders, known and generic types, sizes, dates and headers | 实际文件模型与相反系统语言模拟 / filesystem and opposite-language models |
| 选择状态 / Picker state | 文件名、目录、筛选项、选中行、路径映射保持 / filename, directory, filter, selection and source paths | 打开时双向切换 / live-switch tests |
| 原生控件提示 / Qt-generated warnings | 文件不存在提示、打开时的子窗口语言 / missing-file warning | 实际弹出并关闭 Qt 提示 / actual Qt warning |
| 确认与消息 / Message boxes | 是／否、确定、保存／不保存／取消及默认按钮 / Yes/No, OK, Save/Discard/Cancel and defaults | 实际弹窗与打开时切换 / real modal tests |
| 右键菜单 / Context menus | 计算、地址、范围输入及清单编辑区 / calculation, tools, range and list editors | 当前语言实际菜单 / actual menus |
| 关于 / About | 页签、程序信息、帮助、法律说明、组件概览与许可选择 / all tabs and component summary | 双向扫描及文本检查 / live scans and document checks |
| 复制与 TXT / Reports | 当前语言报告，原始输入保留，精确统计 / localized reports, raw input and exact totals | 既有报告与文件输出回归 / report/output tests |
| Excel | No.／IPv6 Subnet／IPv6 Subnets 与中文对应，任务开始语言快照 / headers, sheet name and task-start language | 既有实际 XML 内容检查 / actual workbook XML tests |
| 翻译资源 / Catalogs | TS 与 QM 一致、占位符、源模板覆盖 / compiled catalogs, placeholders and source coverage | 自动目录回归 / catalog tests |

## 原文保留规则 / Content Preserved as Written

- IPv6、CIDR、JSON、TXT、Excel、Windows、Qt、GPL 等通用术语、协议和产品名称保留。
- 语言菜单中的“简体中文 / English”保留原生语言名称。
- 用户输入、文件名、路径、注释、方案名称和备注保留，不按关键词替换。
- 项目与第三方许可证、版权及来源声明原文保留；面向使用者的组件概览、帮助及法律说明使用对应语言。
- 本次不修改计算算法、JSON 格式及导出数据的数值含义。

Protocol/product names and native language names remain recognizable. User content, file paths and original legal/attribution texts are preserved. The UI overview and explanatory documents follow the selected language. Calculation and serialized data semantics are unchanged.

## 验证与实机边界 / Validation and Platform Scope

本轮新增 18 项双语审计测试，完整回归总数为 393 项。最终运行结果、源码／单文件指纹及环境记录见 [VALIDATION.md](VALIDATION.md)。本地 Windows 应重点复核截图中的文件夹类型、两种系统显示语言、文件占用、DPI 和连续使用；步骤见 WINDOWS_ACCEPTANCE.md。
18 new audit tests bring the regression suite to 393. See VALIDATION.md for actual results, source/frozen fingerprints and environment. Windows verification should cover native display-language combinations, file locking, DPI and extended use.


## V1.10 扩展检查 / Extended Audit — 2026-10-21

新增“分配建议”页的标签、图标悬停、容量状态、错误、表头、确认框、TXT 保存菜单及报告均加入 English 资源。双向切换保留建议快照和用户清单；用户注释不翻译。新报告在实际保存时使用界面语言。新增结果页在两主题、中英文及 900×620 下检查文字与首条候选可见性。原 V1.9 修复及其回归保留。

The Allocation page localizes labels, tooltips, capacity status, errors, table headers, confirmation, TXT menus and reports. Live switching preserves suggestions and raw user content. Reports use the language at save time. Both languages and themes are checked at 900×620, including status and candidate-row visibility. V1.9 fixes and regression coverage are retained.

英文翻译资源共 682 条完成、0 条未完成。Windows 实机验证仍按独立清单执行。
The English catalog contains 682 finished entries and no unfinished entries. Windows verification remains a separate task.

## Windows 换行兼容修正 / Newline Compatibility Fix

GitHub Actions 第 15 轮中，Ubuntu 通过，Windows 的 541 项测试仅生成记录校验失败（另跳过 1 项 POSIX 专用测试）。原因是 TS 以原始字节计算摘要，与 Windows 的 CRLF 检出冲突。现仅对 TS 换行规范化，并将 TS 标为 LF 文本、QM 标为二进制；不忽略实际译文或 QM 内容变化。新增三项回归已覆盖。

Actions run 15 passed on Ubuntu but failed the catalog-generation record check on Windows (one existing POSIX-only skip). Raw TS byte hashing conflicted with CRLF checkout. TS newline normalization and explicit Git text/binary attributes resolve the false failure while retaining translation and QM integrity checks. Three new regressions cover these cases.
