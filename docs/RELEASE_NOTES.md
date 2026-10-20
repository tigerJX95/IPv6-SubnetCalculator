# IPv6SubnetCalculator V1.7

## 🐛 导出国际化

- 修复英文界面导出的 Excel 仍含中文表头及工作表名的问题；英文使用 `No.`、`IPv6 Subnet`，工作表名 `IPv6 Subnets`。
- 中文导出保留“序号”“IPv6 子网”及工作表名“IPv6子网”。
- 文件使用开始导出时的界面语言；导出期间切换语言保持文件内部一致，完成提示跟随当前界面语言。
- 保留指定范围的实际序号、超长整数精度及取消后的原文件保护。

## 🌐 文字与文档

- 补齐英文容量估算范围分隔符，刷新 Qt 页签滚动按钮悬停提示。
- 检查界面、弹窗、表头与提示文字，增加翻译模板覆盖及实际 XLSX 内容回归。
- TXT 保持每行一个 CIDR，不添加标题；JSON 方案格式保持兼容。
- 更新双语 README、离线帮助及运行截图。

## 📦 下载

在 Releases 的 Assets 中直接下载 `IPv6SubnetCalculator_V1.7.exe`。标签：`v1.7`。

---

## 🐛 Localized Excel Export

- Fixed Chinese column headers and worksheet names in English Excel exports. English output uses `No.`, `IPv6 Subnet` and worksheet `IPv6 Subnets`.
- Chinese output retains its existing headers and worksheet name.
- Each file uses the interface language at export start, even if the interface language changes during export. Completion feedback uses the current interface language.
- Preserves actual indices for selected ranges, exact large integers and cancellation protection for existing files.

## 🌐 Text and Documentation

- Added the English separator for size-estimate ranges and refreshed Qt tab-scroll tooltips.
- Audited interface and dialog text, adding catalog-coverage and actual-workbook regression checks.
- TXT remains one CIDR per line without headers; JSON plans remain compatible.
- Updated bilingual READMEs, offline help and application screenshots.

## 📦 Download

Download `IPv6SubnetCalculator_V1.7.exe` directly from Assets on Releases. Tag: `v1.7`.
