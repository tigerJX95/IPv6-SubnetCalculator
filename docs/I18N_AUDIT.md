# V1.9 双语窗口检查 / Bilingual Window Audit

日期 / Date: 2026-10-20

本次为 V1.9 的双语一致性修订，版本号保持 V1.9。检查包含简体中文、English，以及窗口打开时双向切换。实际环境为 Linux Qt offscreen；另以相反系统语言的文件类型说明进行模拟验证。Windows 实机验收单独保留。
This revision retains V1.9 and checks Chinese, English and live switching. Tests run with Linux Qt offscreen, including simulated native file-type strings in the opposite language. Windows acceptance remains separate.

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
