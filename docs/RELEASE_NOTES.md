# IPv6SubnetCalculator V1.4

## ✨ 两项规划功能

- 新增父网段空闲空间：根据已有占用清单计算占用并集、空闲地址数量及最简空闲 CIDR，避免重复扣减。
- 新增等价 CIDR 整理：移除重复／已覆盖网段并精确合并，地址覆盖集合保持不变。
- 两项功能共用清单输入，后台执行、支持取消，提供完整结果及报告复制，不修改原始输入。

## 🐛 规划与复制保护

- 非法记录阻止整次规划；空闲计算同时拒绝不完全位于父网段内的记录。
- 空闲 CIDR 明细最多 5,000 条，总数及全部连续空闲范围不截断；明细截断时禁用完整 CIDR 复制。
- 修改输入使旧结果失效；修改父网段只清空对应空闲结果。
- 继续保持原方案格式兼容及后台任务退出保护。

## 🎨 图标、说明与下载

- 关于图标去掉浅蓝底纹，改为透明、随主题调整颜色的线条图标，保留悬停提示与 F1。
- 明确条数、总行数与字节大小的区别：1 MiB 为 1,048,576 字节。
- 更新双语文档、离线帮助及 V1.4 实际浅深色界面截图。
- 从 Releases 直接下载 `IPv6SubnetCalculator_V1.4.exe`；标签使用 `v1.4`。

---

## ✨ Two Planning Features

- Adds parent-network free space: exact occupied union, free address counts and minimal free CIDRs without double-counting overlaps.
- Adds equivalent CIDR aggregation: removes duplicate/covered networks and merges precisely without changing coverage.
- Both share list input, run in a cancellable worker and provide result/report copying without rewriting input.

## 🐛 Planning and Copy Protection

- Invalid entries reject planning; free-space checks also reject entries outside or broader than the parent.
- Free CIDR details are capped at 5,000 while totals/all free intervals stay exact. Complete-CIDR copying is disabled when details are truncated.
- Editing input invalidates old results; editing the parent clears only free-space results.
- Retains plan-format compatibility and orderly worker shutdown.

## 🎨 Appearance, Guidance and Downloads

- Replaces the tinted About tile with a transparent theme-aware line icon, retaining its tooltip and F1.
- Clarifies entries, physical lines and byte size: 1 MiB is 1,048,576 bytes.
- Updates bilingual/offline guidance and actual V1.4 light/dark previews.
- Download `IPv6SubnetCalculator_V1.4.exe` from Releases directly; use tag `v1.4`.
