# IPv6SubnetCalculator V1.5

## ✨ 导入与输入体验

- 新增单个本地 JSON 计算方案拖放，主窗口输入框、编辑区和结果表格均可接收；复用打开方案的完整校验与恢复。
- 校验通过后确认替换，保留未保存工作的保存／不保存／取消流程；不修改源文件，不额外触发计算或导出。
- 输入错误显示红框、警示图标和加粗具体原因；编辑后清除对应标记，重试重新校验。
- 计算、地址工具、定位、范围复制、导出范围、父网段和清单校验统一提示。

## 🐛 保护与中文一致性

- 拒绝多文件、文件夹、远程链接、错误扩展名及损坏方案；失败或取消保留当前工作，后台任务期间暂缓拖放导入。
- 确认、错误、警告及文件选择窗口完整中文化；内置 Qt 中文翻译，避免英文 Windows 导致标准按钮或菜单出现英文。
- 常见文件访问错误提供中文说明、路径与系统错误码。
- 确认后再次校验文件，防止同路径保存或外部修改导致恢复旧内容。
- 保持现有计算逻辑与方案格式 v1 兼容。

## 📖 文档

- 更新双语说明、离线帮助、实际运行截图与 Windows 验收项。
- 记录已确认 i18n 路线：V1.5 实机验收后进入 V1.6，同一 EXE 支持简体中文和 English 即时切换。V1.5 不包含语言切换。
- Releases 直接下载 IPv6SubnetCalculator_V1.5.exe，标签使用 v1.5。

---

## ✨ Import and Input Experience

- Adds single local JSON plan drops throughout the main window, sharing validated restoration with Open Plan.
- Confirms replacement and preserves Save/Discard/Cancel for unsaved work; no source-file changes or additional calculations/exports.
- Adds red input borders, warning indicators and bold explanations with edit/retry recovery across input workflows.

## 🐛 Protection and Chinese Consistency

- Rejects multiple files, folders, remote links, unsupported extensions and corrupt plans; cancellation/failure preserves work and active background tasks defer drops.
- Bundles Chinese Qt translations and centralizes Chinese confirmations, warnings and file browsers independently of Windows display language.
- Provides Chinese filesystem errors with original paths and system error codes; retains calculation and plan-format compatibility.

## 📖 Documentation

- Updates bilingual/offline help, actual previews and Windows acceptance.
- Records the confirmed i18n roadmap: V1.6 bilingual switching follows V1.5 Windows acceptance. V1.5 has no language switch.
- Download IPv6SubnetCalculator_V1.5.exe directly from Releases; use tag v1.5.
