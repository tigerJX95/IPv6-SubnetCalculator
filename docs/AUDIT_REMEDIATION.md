# V1.10 审计修复说明 / Audit Remediation

## 简体中文

版本号统一保留 V1.10。本次源码修复 A01、A02、A03：

- 🐛 保存冲突保护应用于方案、清单/规划 TXT 和批量 TXT/XLSX 导出，使用确认时文件快照、提交前版本核验和同程序提交协调；新目标采用原子无覆盖新建。
- 🐛 检出冲突时不覆盖目标，完整输出另存同目录恢复文件并显示路径；取消清理未完成文件。符号链接、目录等非普通目标拒绝覆盖。
- 🐛 方案保存期间内容变化会拒绝旧快照，保存后新修改仍保持未保存状态。
- 🐛 验证门禁改用结构化 unittest 结果和本次运行标识，拒绝缺失、截断、零测试、部分运行及旧证据；要求全部自检工作流完成。
- 🌐 冲突与恢复消息同步提供中英文，更新日志完整记录以上内容；原有菜单截图清理保留。
- ⏳ **Qt 升级未完成**：官方 PyPI 最新 wheel 仍为 6.11.2，无 6.11.3 分发包；保留可安装依赖，不虚报升级完成。详见 docs/DEPENDENCY_STATUS.md。

440 项测试通过，源码及实际 Linux 单文件各通过 23 项自检；Windows 实机验收仍待完成。既有文件的协作锁不强制约束所有第三方应用，最终极短竞争窗口及网络文件系统限制见 docs/SAVE_CONFLICTS.md。

## English

All changes retain V1.10. This revision addresses A01, A02 and A03:

- 🐛 Plan, list/planning TXT and bulk TXT/XLSX saves carry approval-time file revisions into commit, coordinate cooperating processes and use atomic no-overwrite creation for absent targets.
- 🐛 Detected conflicts retain the destination and complete recovery output, reporting its path. Cancellation cleans incomplete files. Nonregular targets such as links/directories cannot be overwritten.
- 🐛 Plan changes during dialogs invalidate old snapshots; later edits remain dirty.
- 🐛 Verification requires structured unittest evidence with the current run identifier and all self-check workflows, rejecting missing, truncated, zero-test, partial or stale results.
- 🌐 Conflict/recovery messages and release notes are bilingual. Menu-only screenshots remain removed.
- ⏳ **Qt upgrade remains pending**: official PyPI still provides 6.11.2 as latest, with no 6.11.3 distribution. Installable requirements are retained without claiming an upgrade. See docs/DEPENDENCY_STATUS.md.

All 440 tests passed. Source and actual Linux onefile each passed 23 workflows. Native Windows acceptance remains pending. Cooperative locks do not force every third-party writer to comply; final race-window and network-filesystem limits are documented in docs/SAVE_CONFLICTS.md.
