# IPv6SubnetCalculator V1.10 审计修复验证 / Audit Fix Validation

日期 / Date: 2026-10-21。版本号保持 V1.10。 / Version remains V1.10.

## 完成状态 / Completion Status

| 项目 / Item | 结果 / Result |
|---|---|
| A01 保存冲突 / save conflicts | 已加入确认时文件快照、提交前核验、同程序提交协调、原子无覆盖新建和完整恢复输出 / implemented with documented concurrency limits |
| A02 保存状态 / saved state | 对话框期间变化不再保存旧快照；之后变化保留 dirty 状态 / fixed |
| A03 验证门禁 / verification gate | 必须提供完整、非零、匹配本次运行的结构化结果和完整自检项目 / fixed |
| D01 Qt 升级 / Qt upgrade | **未完成**：官方 PyPI 尚未提供 6.11.3 或兼容的更新发布包；保留 6.11.2 / **pending upstream wheel**, not claimed as fixed |

## 实测环境 / Actual Environment

Linux x86_64, Qt offscreen; Python 3.12.14; PyQt6 6.11.0 / Qt 6.11.2; PyInstaller 6.22.3.

源码/运行资源 SHA-256 / runtime fingerprint: `b57c74c0594eb59085b6f478c9d445194f862feccd09ca4d873ec1f83917fc0d`.

实际构建并运行 Linux 单文件程序，版本及指纹与源码一致。Windows EXE 未在本环境构建或运行。
An actual Linux onefile build was executed with matching version/fingerprint. Windows EXE was not built or run here.

## 验证结果 / Results

- 完整回归 / Full regression: **440 项通过，0 失败、0 错误、0 跳过 / passed with zero failures, errors or skips**，其中新增 25 项 / including 25 new tests.
- 源码及实际单文件程序自检各 **23 个工作流**通过 / Source and frozen checks each passed **23 workflows**.
- 翻译 / Translation: **690 条完成，0 未完成 / finished entries, none unfinished**.
- 结构化结果完整：预期测试数=实际测试数=440，运行标识、版本、指纹一致。 / Expected and actual counts, run identifier, version and fingerprint matched.
- 真实双进程竞争：新目标和同一旧版本各验证一个提交成功、另一份完整内容保留。 / Real two-process races tested for absent and existing destinations: one commit and one recoverable result.
- 模拟外部写入：新建、修改、同大小同修改时间但文件身份变化、删除、锁冲突均验证不静默覆盖。 / Controlled rival creation, modification, replacement, deletion and lock conflict checked.
- TXT、JSON 与完整 XLSX 恢复副本可读；取消保留原文件且不留下未完成恢复输出。 / TXT/JSON/XLSX recovery files verified; cancellation retained the original and cleaned incomplete output.
- 方案内容变化、确认期间目标变化、保存后新修改、中英文提示、无效类型目标均有回归。 / Snapshot changes, dialog conflicts, later edits, bilingual messages and nonregular targets covered.
- 门禁拒绝缺失/截断、零测试、部分完成、失败、旧运行标识/版本/指纹、缺少工作流的证据。 / Evidence rejection paths covered.
- 两 README 的下载仍指向 Releases 最新 EXE，已删除的菜单截图和引用未重新加入。 / Direct EXE download links and screenshot cleanup retained.

## 本机性能样本 / Host Samples

| 项目 / Item | 时间 / Time |
|---|---:|
| 核心计算中位数 / calculation median | 0.011112 ms |
| 5,000 条关系检查 / relationships | 93.134602 ms |
| TXT 100,000 条 / rows | 0.84799 s |
| XLSX 20,000 条 / rows | 0.20539 s |

样本不是 Windows 性能保证。源码自检最大事件循环采样间隔 3465.686 ms；打包程序 949.953 ms，包含同步检查步骤，不能据此证明无卡顿或长期稳定。
Host samples are not Windows performance guarantees. Event-loop samples include synchronous check work and do not establish stall-free or long-duration stability.

## 保存保护边界 / Concurrency Limits

新建目标使用原子无覆盖操作。既有文件为版本核验与协作锁，第三方应用不遵守锁时仍存在最终核验到替换间的极短竞争窗口；远程文件系统取决于服务器语义。不将该实现表述为对所有程序的强制事务锁。

New targets use atomic no-overwrite publication. Existing files use optimistic revision checks and cooperative locking. An uncooperative writer can still race in the final check-to-replace interval; network filesystems depend on server semantics. This is not a mandatory transaction lock on every application.

## Windows 验证及依赖 / Windows Verification and Dependency Status

仍须验证 Windows 命名互斥、实际文件占用、NTFS/exFAT/网络目录、DPI 和日常使用。完整解压后运行 build.cmd 生成新 EXE，再运行 verify.cmd。功能自检通过不代表 Qt 安全升级已完成。

Windows mutex/file-lock behavior, NTFS/exFAT/network paths, DPI and normal use remain pending. Extract, build the new EXE and run verify.cmd. Functional verification does not close the Qt upgrade concern.

更多说明 / Details: docs/SAVE_CONFLICTS.md, docs/DEPENDENCY_STATUS.md, docs/RELEASE_NOTES.md.
