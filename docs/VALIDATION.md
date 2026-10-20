# IPv6SubnetCalculator V1.9 验证记录 / Validation Record

日期 / Date: 2026-10-20

V1.9 新增清单／规划 TXT 保存与完整规划结果回流检查。原始输入、有效去重 CIDR、检查报告及规划清单／报告分别保存；报告按实际保存时的界面语言生成，输入与纯 CIDR 保留原文。
V1.9 adds list/planning TXT saves and protected transfer of complete planning results back to Subnet List. Reports use the interface language at save time; original input and CIDRs retain their content.

## 实际环境 / Environment

| 项目 / Item | 结果 / Result |
|---|---|
| 应用 / Application | V1.9 |
| OS | Linux-6.18.55-x86_64-with-glibc2.39, x86_64, Qt offscreen |
| Python | 3.12.14 |
| PyQt6 / Qt | 6.11.0 / 6.11.2 |
| 运行源码及资源 SHA-256 / Fingerprint | `c41ccab55122031299e92e10ee5293d4d88b70ee3d1b188f185ba4f55233421f` |
| Linux 单文件 / Onefile | 实际构建运行；版本及指纹匹配 / built and executed with matching version and fingerprint |
| Windows EXE | 本环境未构建或运行 / not built or run here |

## 双语修订 / Bilingual Revision

🐛 文件窗口的类型、表头、大小及日期跟随应用语言；中文显示“文件夹”，英文显示“Folder”，不依赖操作系统语言。第三方组件概览分别使用中英文文档；修复动态标签、规范化提示及错误说明中的中文标点。用户输入、文件名、协议名称及许可证原文保持原样。详见 [双语检查记录](I18N_AUDIT.md)。

File metadata follows the application language independently of the system language. Component summaries use separate language documents. Dynamic labels, normalization notices and errors use localized punctuation. User content, filenames, protocol names and original licenses are preserved. See the [audit record](I18N_AUDIT.md).

393 项完整回归由独立 unittest discovery 运行并记录结构化 TestResult（0 失败、0 错误，65.049 秒）。原验证脚本的该轮测试日志不完整，故测试数量以此次完整独立运行及日志为准。源码与实际打包程序分别完成 21 个自检工作流，版本及运行资源指纹一致。

The complete independent unittest discovery recorded 393 tests, zero failures and zero errors (65.049 seconds). Its structured TestResult and complete log supply the regression count because the earlier verification run produced an incomplete test log. Source and actual packaged checks each passed 21 workflows with matching fingerprints.

## 自动验证 / Automated Verification

| 检查 / Check | 结果 / Result |
|---|---|
| 完整回归 / Regression | 393 项通过，含本次新增 18 项双语检查 / passed, including 18 new bilingual audit tests |
| 原始输入 / Original input | 未检查的原文可保存，保留编辑区注释、空行、中文和错误内容 / editor content retained |
| 有效网段 / Valid CIDRs | 规范化去重、跳过错误，保存 TXT 后重新导入得到相同网段 / normalization, deduplication and reimport passed |
| 检查报告 / Check report | 含错误原文、精确总数和有限明细；全错误清单仍可保存报告 / invalid entries and exact totals retained |
| 规划输出 / Planning output | 空闲与整理结果分别保存 CIDR 及报告，双语内容核对通过 / both result types and languages |
| 截断与零空闲 / Truncated and empty | 不完整／空 CIDR 禁用清单保存及回流；报告仍保留全部区间和精确统计 / no partial list output, reports retained |
| 文件保护 / File protection | 取消及拒绝覆盖保留原文件；替换失败清理临时文件；无效 Unicode 不创建输出 / atomic replacement and failure recovery |
| 对话框事务 / Dialog transactions | 输入／父网段／结果变化时拒绝旧快照；覆盖默认“否”；扩展名补全和拒绝错误扩展名 / snapshot and extension checks |
| 语言 / Language | 菜单及提示随语言切换；保存窗口中切换后报告使用保存时语言，用户内容保留 / save-time report language and raw data preservation |
| 规划回流 / Planning transfer | 确认后替换并自动检查；拒绝、忙碌或来源变化保留当前工作；计算结果保留 / guarded transfer and retained calculation |
| 布局 / Layout | 两主题、中英文、最小 900×620 下新增按钮可达 / both languages, themes and minimum window |
| 翻译资源 / Catalog | 647 条完成、0 未完成；TS/QM、上下文及占位符检查通过 / completed entries and compiled-resource checks |
| 源码自检 / Source check | 21 个工作流通过 / workflows passed |
| 单文件自检 / Frozen check | 21 个工作流通过，含文本文件和英文报告内容验证 / workflows passed, including actual text files and English reports |
| 既有功能 / Existing functions | 计算、地址范围、格式与关系、方案及拖放、清单规划、分页、双语 Excel 与取消保护回归通过 / previous workflows passed |

## 性能样本 / Host Measurements

| 项目 / Item | 时间 / Time |
|---|---:|
| 核心计算中位数 / Calculation median | 0.011646 ms |
| 5,000 条关系检查 / Relationships | 96.682932 ms |
| 5,000 条空闲计算 / Free space | 89.522787 ms |
| 5,000 条整理 / Aggregation | 77.296097 ms |
| TXT 100,000 条 / rows | 0.8984 s |
| XLSX 20,000 条 / rows | 0.25491 s |

核心中位数不含粘贴、弹窗和绘制。这些是本机样本，不是 Windows 性能保证或相对旧版提速。内存只跟踪 Python 分配，未包含 Qt 原生内存和全部进程内存。源码自检最大事件循环采样间隔为 4065.842 ms；短时检查不能证明无卡顿或长期稳定。新增有界清单／报告采用同步文本写入，慢速网络目录的响应仍需实机确认；大量子网导出继续使用后台流式写入。
Core medians exclude paste, dialogs and drawing. These are host samples, not Windows guarantees or speed comparisons. Memory tracks Python allocations only. The source self-check observed a maximum event-loop sample gap of 4065.842 ms; short checks do not establish stall-free or long-term stability. Bounded list/report writes are synchronous; slow network locations need practical testing. Bulk exports retain background streaming.

## Windows 验收 / Windows Acceptance

Windows 自动检查、人工操作、DPI、文件占用与至少 30 分钟日常使用仍待本机完成。完整解压源码后运行 build.cmd，再运行 verify.cmd，保留报告。重点检查保存菜单、两主题与语言、覆盖／取消、文件占用后重试、规划回流及已有 Excel／拖放功能。完整清单见 docs/WINDOWS_ACCEPTANCE.md。
Windows automated/manual checks, DPI, file locking and 30-minute use remain pending. Fully extract, build and run verify.cmd; complete the acceptance checklist.

正式标签 v1.9；用户从 Releases 直接下载 IPv6SubnetCalculator_V1.9.exe。
Use tag v1.9 and distribute IPv6SubnetCalculator_V1.9.exe directly through Releases.
