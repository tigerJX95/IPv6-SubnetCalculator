# IPv6SubnetCalculator V1.3

## ✨ 子网清单导入与关系检查

- 新增“子网清单”页，支持粘贴或导入 UTF-8 TXT／CIDR，保留原始行号，逐行显示规范化和错误。
- 精确统计重复、包含及相邻关系；重复和包含均属于重叠，相邻不代表一定能够合并。
- 支持复制有效、规范化、去重后的 CIDR，以及包含错误记录、精确总数与有限关系明细的报告。
- 后台检查可取消；支持最多 5,000 条、1 MiB、20,000 个物理行。关系明细最多 1,000 对，总数不截断。

## 🐛 状态与异常处理

- 错误行不参与关系分析，并明确提示结果仅覆盖有效项。
- 输入修改后清空旧结果并禁用复制；取消、读取失败或线程异常可恢复操作。
- 主程序退出时等待清单检查取消完成，保留现有计算与导出退出保护。
- 保持计算方案格式兼容，清单内容不写入方案 JSON。

## 📸 文档与下载

- 使用 V1.3 实际运行界面更新浅色与深色截图，并标明截图版本。
- 更新中英文说明与内置帮助，下载链接统一使用 Releases 最新版入口。
- 直接下载 `IPv6SubnetCalculator_V1.3.exe` 后运行；Git 标签使用 `v1.3`。

---

## ✨ Subnet List Import and Relationship Checks

- Adds Subnet List: paste or import UTF-8 TXT/CIDR files, retaining original line numbers, normalized CIDRs and validation errors.
- Counts duplicate, containment and adjacency pairs exactly. Equality and containment represent overlap; adjacency does not guarantee aggregation.
- Copies valid normalized/deduplicated CIDRs or reports with errors, exact totals and bounded relationship details.
- Runs cancellable background checks for up to 5,000 entries, 1 MiB and 20,000 physical lines. Details are capped at 1,000 pairs without truncating totals.

## 🐛 State and Error Handling

- Excludes invalid lines from relationships and states that results cover valid entries only.
- Clears stale results after input changes; supports recovery after cancellation, read errors and worker failures.
- Waits for list-check cancellation before closing, retaining existing export/plan protections.
- Keeps the existing plan format compatible; list data is not saved in plan JSON.

## 📸 Documentation and Downloads

- Replaces light/dark previews with actual V1.3 interfaces and labels the screenshot version.
- Updates bilingual documentation/offline help and uses the latest Releases download entry.
- Download and run `IPv6SubnetCalculator_V1.3.exe` directly. Use the tag `v1.3`.
