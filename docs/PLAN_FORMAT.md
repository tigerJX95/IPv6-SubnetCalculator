# V1.10 计算方案格式 / Calculation Plan Format

方案采用 UTF-8 JSON（读取兼容 BOM），格式标识 `IPv6SubnetCalculator.plan`，格式版本 `1`，上限 64 KiB。只保存参数与稀疏视图数据，不存储派生统计或子网列表。/ UTF-8 JSON (BOM accepted on read), format version 1, maximum 64 KiB, with parameters and sparse view state only.

| 字段 / Field | 内容 / Meaning |
|---|---|
| format / version | 固定标识和格式版本 / Format ID and schema version |
| network / target_prefix | IPv6 CIDR 和整数目标前缀 / IPv6 CIDR and integer target prefix |
| name / notes | 最多 80 / 2,000 字 / Up to 80 / 2,000 characters |
| view.page_size | 25、50、100 或 200 |
| view.page | 一基页码，十进制文本 / One-based page as decimal text |
| view.locator_range | null 或两个一基序号文本 / null or two one-based index strings |
| view.selected_indices | 当前页选中的唯一序号文本列表 / Unique selected index strings on the saved page |
| view.tab | 0 计算、1 结果、2 地址工具 / Calculation, Results or Address Tools |

加载时校验所有字段、版本、范围和选择位置，然后重新计算。页码及序号使用字符串以兼容其他 JSON 工具，避免大整数精度损失。打开方案不改变主题偏好或地址工具内容。/ Loading validates the complete document and recomputes results. Page/index strings avoid precision loss in other JSON tools. Opening does not change themes or Address Tools contents.

方案 JSON 与“子网清单”不同：已有 CIDR 清单请在清单页以纯文本导入。清单内容不写入方案；在清单页保存计算方案时，浏览标签记录为计算页（0），格式仍为第 1 版，兼容既有方案。空闲空间与等价整理结果也不写入方案；子网标注、收藏与多级分配规划尚未实现。/ Plan JSON is separate from Subnet List text imports. List contents are not saved in plans; saving a calculation plan from the list tab records tab 0, keeping format version 1 compatible with existing plans. Free-space and aggregation results are also excluded; annotations, favorites and multi-level allocation are not implemented.

示例 / Example: [OfficeNetwork.json](../examples/OfficeNetwork.json)。在程序中使用打开图标载入。 / Use the open icon to load it.
