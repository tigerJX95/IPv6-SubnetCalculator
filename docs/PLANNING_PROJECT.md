# Planning project JSON v1 / 规划项目 JSON v1

`format`: `IPv6SubnetCalculator.planning`; integer `version`: 1.

| Field | Type / limit | Meaning |
| --- | --- | --- |
| text | string; 1 MiB UTF-8, 20,000 physical lines, 5,000 noncomment records | Original input including comments / 清单原文 |
| parent | string; 200 characters | Parent network draft / 父网段草稿 |
| prefix | string; 5 characters | Target prefix draft / 目标前缀草稿 |
| count | string; 6 characters | Requested count draft / 数量草稿 |
| tab | integer 0–4 | List result tab / 清单页签 |

Exact fields only; no duplicate keys, NUL, invalid Unicode, nonfinite JSON constants or unsupported versions. File input is capped at 7 MiB to allow JSON escaping of the bounded source text. CIDR correctness is checked when running analysis, not when saving a draft. Derived results are never persisted or trusted. Calculation JSON v1 remains compatible and separate.

仅保存输入；恢复后重新运行清单检查、空闲空间计算及分配建议。使用顶部图标手动保存，关闭不会自动保存或提示规划项目未保存。文件写入沿用 V1.10 冲突保护与恢复文件机制。
