## V1.13 CIDR output / CIDR 输出

Import `CoverageBaseline.txt` as the current list, open coverage comparison, and import `CoverageCandidate.txt`. Added output must match `CoverageAdded_CIDRs.txt`; removed is `2001:db8::/64`, common is `2001:db8:0:1::/64`. The saved pure CIDR list can be imported again.

将 `CoverageBaseline.txt` 导入当前清单，在覆盖比较中导入 `CoverageCandidate.txt`。新增输出应与 `CoverageAdded_CIDRs.txt` 一致，移除为 `2001:db8::/64`，共同为 `2001:db8:0:1::/64`。保存的纯 CIDR 清单可再次导入。

# 示例文件 / Examples

| 简体中文 / Chinese | English | 用途 / Purpose |
|---|---|---|
| `SubnetList.txt` | `SubnetList_EN.txt` | 子网清单校验与关系 / List validation and relationships |
| `PlanningNetworks.txt` | `PlanningNetworks_EN.txt` | 父网段空闲空间及 CIDR 整理 / Parent-network free space and aggregation |
| `OfficeNetwork.json` | `OfficeNetwork_EN.json` | 计算方案 / Calculation plan |
| `ExportPreview_ZH.xlsx` | `ExportPreview_EN.xlsx` | Excel 导出样例 / Export samples |

中英文 TXT 示例只翻译注释，CIDR 记录及顺序相同；方案示例只翻译名称和备注，计算参数及浏览状态相同。可根据阅读语言手动选用；导入内容保留原文。

The TXT pairs differ only in comments; CIDRs and their order match. Plan pairs differ only in names and notes; calculation parameters and view state match. Choose the sample language when opening a file. Imported content is preserved as written.

规划示例的注释对应 `# Parent network: 2026:1015:abcd::/48`。Excel 样例使用该网络、目标 `/64`、序号 100～104。
The English planning sample begins with `# Parent network: 2026:1015:abcd::/48`. The paired workbooks export indices 100–104 into `/64` subnets.
