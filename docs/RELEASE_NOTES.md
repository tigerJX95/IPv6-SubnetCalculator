# IPv6SubnetCalculator V1.0

## 📖 核心功能版

V1.0 整合离线 IPv6 子网计算与结果操作，提供从输入网络、查看摘要、浏览定位到复制和导出的完整核心流程。

## 🆕 相较 V0.9 新增

- **IPv6 地址格式转换**：新增“地址工具”页，支持压缩／小写规范化、固定 8 组完整展开及 128 位二进制，逐项和全部复制均使用图标与悬停提示。
- 支持 IPv4 映射的 IPv6 输入；二进制分组显示、连续复制，保留前导零。
- **双网段关系分析**：输入两个 CIDR，识别相同、A 包含 B、B 包含 A、相邻或完全独立；展示规范化网络、精确重叠／间隔地址数，并可复制含双方起止地址的报告。
- 相邻按地址范围首尾相接判断，不误判为一定可合并。主机位规范化会明确提示。
- 两项工具分别维护状态，编辑输入立即清空该工具旧结果；切换页面或主题保留状态，不改变子网结果及选择。

- **计算摘要复制**：计算页“网络计算摘要”右上角增加复制图标，悬停显示用途说明。
- 一次复制规范化网络、源／目标前缀、起止地址、网络总容量、子网数量、每个子网容量、新增位数，以及地址类型、部署提示与规范参考。
- 数量保留完整整数，即使 `::/0 → /128` 也不会截断或转换为近似值；生成摘要无需枚举子网。
- 复制内容始终对应最后一次成功计算；编辑输入后需重新计算。首次未计算或计算失败时入口禁用，剪贴板失败可直接重试。

## 🎨 字体与阅读体验

- 常规界面文字从 10 pt 提升至 12 pt，覆盖标签、说明、分页、定位、弹窗和悬停提示。
- 地址、输入框及结果等宽文本从 11 pt 提升至 12 pt；二进制文本从 10 pt 提升至 11 pt，标题增大。
- 表格行高从 32 调整至 38，序号列宽按实际字体宽度计算；详情与导出弹窗增加显示空间。
- 最小窗口仍支持滚动及长文本换行，保留浅深色主题、图标操作和悬停提示。

## ✨ 核心功能

- 支持 `/0`～`/128` IPv6 网络、主机位规范化、常用目标前缀及精确容量计算。
- 提供地址类型、用途与部署限制提示，保留特殊地址的数学划分能力。
- 按页加载结果，支持四种定位方式、跨页范围高亮、选择统计、范围复制和子网详情。
- 支持全部或指定范围导出为 TXT／Excel，提供容量估算、后台进度和取消操作。
- 通过文本保存超过 15 位的 Excel 序号，保留完整数字。
- 提供 PyQt6 三标签页界面、浅色／深色主题、自动保存的主题选择，以及图标和悬停提示。

## 🐛 异常与错误处理

- 修复中文 Windows 默认 GBK 编码下，验证脚本读取 UTF-8 源码时出现 `UnicodeDecodeError` 的问题；测试文本读写统一指定 UTF-8，并增加 GBK 默认编码回归。

- 统一网络、前缀、分页、序号与范围参数检查，提供明确反馈。
- 导出线程启动失败或异常结束时恢复操作，并支持重试。
- 失败或取消时保留原文件并清理临时文件；关闭程序时等待导出停止和清理。

## 📦 下载与使用

下载 `IPv6SubnetCalculator_V1.0_Windows.zip`，解压后运行其中的 EXE，无需安装 Python。包内包含项目与第三方许可文件。默认示例网络为 `2026:1015:abcd::/48`。

## 📄 开源许可

项目自有代码及资源采用 **GPL-3.0-or-later**；第三方组件保留各自的版权与许可。

---

## 📖 Core Feature Release

V1.0 brings together offline IPv6 calculations and result operations into a complete core workflow, from entering a network and reviewing its summary to browsing, locating, copying, and exporting subnets.

## 🆕 New Since V0.9

- **IPv6 format conversion:** The new Address Tools tab provides compressed/lowercase normalized form, fixed eight-group expanded hexadecimal form, and 128-bit binary, with individual/copy-all icons and hover tooltips.
- Accepts IPv4-mapped IPv6 inputs. Binary display groups bits while copying preserves all 128 consecutive bits, including leading zeros.
- **Two-network analysis:** Classifies two CIDRs as equal, A containing B, B containing A, adjacent, or independent. Shows normalized networks and exact overlap/gap counts, and copies a report including both address ranges.
- Adjacency means directly contiguous ranges and does not imply they form one CIDR. Host-bit normalization is reported explicitly.
- Both tools retain independent state. Editing inputs clears only the corresponding result; tab/theme switches preserve results and calculator selections.

- **Calculation summary copying:** A copy icon with a hover tooltip appears at the top right of the Calculation page's network summary.
- Copies the normalized network, source/target prefixes, start/end addresses, total capacity, subnet count, per-subnet capacity, added bits, address type, deployment guidance, and standards reference.
- Preserves full integer counts even for `::/0 → /128`, without enumerating subnets.
- Uses the last successful calculation; edited inputs require recalculation. Disabled before calculation or after an invalid recalculation. Clipboard failures allow an immediate retry.

## 🎨 Typography and Readability

- Increases interface text from 10 pt to 12 pt across labels, notes, navigation, dialogs, and tooltips.
- Increases monospaced inputs/address/results text from 11 pt to 12 pt, binary from 10 pt to 11 pt, and enlarges the title.
- Increases table row height from 32 to 38, sizes the index column using font metrics, and provides more space in detail/export dialogs.
- Retains scrolling and text wrapping at minimum window size, alongside both themes, icons, and hover tooltips.

## ✨ Core Features

- Supports IPv6 networks from `/0` to `/128`, host-bit normalization, common target prefixes, and exact capacity calculations.
- Provides address-type, usage, and deployment guidance while preserving mathematical subnetting for special-purpose addresses.
- Loads results by page, with four location modes, range highlights across pages, selection statistics, range copying, and subnet details.
- Exports all subnets or an index range to TXT/Excel with size estimates, background progress, and cancellation.
- Stores Excel indices exceeding 15 digits as text to preserve their full values.
- Provides a PyQt6 three-tab interface, light/dark themes, saved theme preferences, icons, and tooltips.

## 🐛 Error Handling and Recovery

- Fixes `UnicodeDecodeError` in verification on Windows systems using GBK as the default encoding. Test text I/O now explicitly uses UTF-8, with a GBK-default regression case.

- Validates networks, prefixes, pages, indices, and ranges with clear feedback.
- Restores controls and permits retries after export startup failures or abnormal completion.
- Preserves originals and removes temporary files after failure or cancellation; closing waits for export cancellation and cleanup.

## 📦 Download and Usage

Download `IPv6SubnetCalculator_V1.0_Windows.zip`, extract it, and run the EXE. Python is not required. The package includes project and third-party license files. The default example network is `2026:1015:abcd::/48`.

## 📄 License

Project-authored code and assets use **GPL-3.0-or-later**. Third-party components retain their own copyrights and licenses.
