## ✨ V1.14 空闲容量总览

- 在“子网清单”顶部查询窗口新增“空闲容量总览”页：输入父网段，一次统计父前缀至 /128 各级可分配的完整、对齐子网数量。
- 显示空闲地址数、占用并集容量、最大可用子网，以及各前缀下无法组成完整子网的零散地址数；同等大小的最大子网取地址最小者。
- 使用全部空闲范围计算，不受 5,000 条 CIDR 预览截断影响；容量使用精确整数，不枚举 IPv6 地址。每一行都是同一空闲空间的不同划分，不能跨行相加。
- 支持双语报告复制及 TXT 保存，沿用覆盖确认和文件冲突保护；修改父网段立即清除结果。基于打开窗口时的清单快照，不修改原项目，关闭后重开可使用最新清单。
- 占用清单必须全部有效且位于父网段内；空清单表示父网段全空闲。总览输入及结果不保存到规划项目 JSON，需要留存时保存报告。
- 保留 V1.13 CIDR 输出、翻译审计和跨平台换行修复。Qt 运行库保持现有版本，本次不包含 Qt 安全升级。

## ✨ V1.14 Free Capacity Overview

- Added a Free Capacity Overview tab in the Subnet List lookup window. Enter a parent network to count complete, aligned available subnets at every prefix from the parent prefix through /128.
- Shows free addresses, occupied union size, the largest available subnet and fragmented addresses that cannot form a complete subnet at each prefix. Equal-sized largest subnets use the lowest address.
- Uses complete free ranges even when the 5,000-CIDR preview is truncated. Counts are exact integers without enumerating IPv6 addresses. Rows partition the same free space differently and must not be added together.
- Copy bilingual reports or save TXT with overwrite confirmation and conflict protection. Editing the parent clears results. The list snapshot is taken when the window opens; original projects are unchanged. Reopen to use an updated list.
- All occupied records must be valid and contained within the parent; an empty list leaves the entire parent free. Overview inputs and results are not stored in planning project JSON; save the report to retain them.
- Retains V1.13 CIDR output, translation auditing and checkout newline fixes. Qt runtime dependencies are unchanged; this update does not include a Qt security upgrade.

## ✨ V1.13 查询与比较结果 CIDR 输出

- 地址归属查询支持复制及保存匹配网段 CIDR：规范化、去重，按最长前缀优先排列，保留包含项；原报告仍保留原始行号及重复记录。
- 覆盖比较可分别选择新增、移除、共同覆盖，生成精确覆盖结果的最简 CIDR 清单，支持复制及 TXT 保存后重新导入。
- 显示所选类别的 CIDR 条数。空结果不生成空清单；超过 5,000 条时禁用纯 CIDR 输出，完整地址范围报告仍可保存。
- 修改输入立即清除结果；保存期间切换类别或重新计算会中止旧结果保存。沿用现有覆盖确认及保存冲突保护。
- 同步中英文界面及离线说明，保留已合并的 GitHub Actions 质量检查。Qt 安全升级仍待兼容运行库发布，本版不包含 Qt 漏洞修复。

## ✨ V1.13 CIDR Output for Lookup and Coverage Results

- Copy or save matching CIDRs from address lookup: normalized, deduplicated and ordered by longest prefix, retaining containing networks. Reports still preserve original line numbers and duplicate records.
- Select added, removed or common coverage and produce its exact minimal CIDR list. Copy or save TXT for reimport into Subnet List.
- Show the selected CIDR count. Empty categories cannot produce empty files; results exceeding 5,000 CIDRs disable list output while complete range reports remain available.
- Editing inputs invalidates output. Changing category or recalculating during a save dialog aborts stale output; overwrite confirmation and save conflict protection still apply.
- Updated bilingual UI and offline help. Retains the merged GitHub Actions checks. The Qt security upgrade is pending a compatible runtime release; this version does not fix Qt vulnerabilities.

# 清单查询与覆盖比较 / List Lookup and Coverage Comparison

- 新增地址归属查询：输入 IPv6 地址，按最长前缀优先列出清单中所有匹配网段及原始行号，保留重复及包含项。
- 新增覆盖差异比较：当前清单作为基准，与粘贴或导入的 TXT／规划项目清单比较，精确统计新增、移除和共同覆盖的地址数与全部范围；等价 CIDR 拆分不产生虚假变化。
- 两项功能位于“子网清单”顶部查询图标，使用打开窗口时的清单快照；支持复制及 TXT 报告保存，沿用保存冲突保护。输入变化后清除旧结果。
- 单份清单继续限制为 5,000 条、1 MiB、20,000 行；空清单可用于比较全部新增或移除。错误行需修正后再查询或比较。

- Added address membership lookup: list all containing networks and original line numbers, longest prefix first, including duplicates and containing entries.
- Added coverage comparison: compare the current list with pasted or imported TXT / planning project lists, with exact added, removed and common address counts and complete ranges. Equivalent CIDR splits do not create false changes.
- Open both tools from the lookup icon at the top of Subnet List. They use a snapshot from when the window opened and support copying and conflict-safe TXT report saving. Editing inputs clears old results.
- Each list retains the 5,000-record, 1 MiB and 20,000-line limits. Empty lists support all-added or all-removed comparisons. Correct invalid records before querying or comparing.

比较方向：新增 = 对比清单 − 当前基准，移除 = 当前基准 − 对比清单，共同 = 两者交集。所有范围包含首末地址。比较仅针对覆盖集合，不比较注释、原始行顺序、父网段或分配参数；导入规划项目只提取清单原文。此窗口中的查询输入和对比清单不写入规划项目 JSON，需要保留时保存报告或单独保存原清单。

Direction: added = candidate minus baseline; removed = baseline minus candidate; common = intersection. Ranges include both endpoints. Comparison covers address sets, not comments, line order, parent networks or allocation parameters. Importing a planning project extracts only its list text. Query inputs and candidate lists in this window are not persisted in planning project JSON; save reports or retain the original lists separately.

实现 / Implementation: `core/list_inspection.py` 使用有界解析、排序并集和线性区间差集；不枚举 IPv6 地址。查询保留所有匹配记录并按前缀长度和行号排序。`ui/list_inspection_dialog.py` 复用动态翻译、剪贴板与现有 TXT 冲突保护写入。
