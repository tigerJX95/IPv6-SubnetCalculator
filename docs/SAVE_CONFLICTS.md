# 保存冲突保护 / Save Conflict Protection

## 简体中文

方案、TXT 文本和批量 TXT/XLSX 导出共用 `core/file_commit.py`。选择目标后、覆盖确认前记录规范化目标路径及文件身份、大小和纳秒时间戳；该快照传递到实际写入与提交阶段。

- 最初不存在的目标采用原子“不覆盖新建”：Windows 使用拒绝既有目标的 rename，POSIX 使用同目录硬链接发布；不支持该操作时失败，不回退到无保护 replace。
- 既有文件在提交前核对版本。应用自身的并发提交通过同会话 Windows 命名互斥量或 POSIX 文件锁协调；没有持久锁文件。
- 检出目标新建、修改、替换、删除或提交锁冲突时，停止覆盖，将本次完整 TXT/XLSX/JSON 保存为同目录 `IPv6-Recovered-*.扩展名` 并显示路径。恢复文件无法重命名时保留原临时文件并报告路径。取消和普通写入失败仍清理未完成临时文件。
- 符号链接、目录及其他非普通目标不允许覆盖。完整恢复文件不会被自动删除，使用者确认内容后自行保留或清理。
- 方案保存对话框期间如内容变化，拒绝旧快照；写入后发生的变化仍保持未保存标记。

边界：既有文件的保护是版本核验加协作锁，不是对所有第三方应用的强制事务锁。无协作写入者仍可能在最终版本核验与原子替换之间的极短窗口竞争；远程文件系统还受服务器语义影响。Windows、NTFS/exFAT、网络目录及实际占用行为须在本机验收。新建目标的原子无覆盖操作不依赖 exists 检查结果。

## English

Plans, text saves and bulk TXT/XLSX exports share core/file_commit.py. The approved normalized path, file identity, size and nanosecond timestamps are captured before overwrite confirmation and passed through writing and commit.

- Initially absent destinations use atomic no-overwrite publication: Windows rename refuses an existing target; POSIX uses a same-directory hard link. Unsupported operations fail safely without falling back to unguarded replace.
- Existing targets are version-checked immediately before commit. Cooperating commits use a same-session Windows named mutex or a POSIX file lock, without persistent lock files.
- Detected creation, modification, replacement, deletion or lock conflict stops replacement and preserves complete output as a same-directory IPv6-Recovered-* file with its real extension. If recovery renaming fails, the original temporary file is retained and reported. Cancellation and ordinary write failures clean incomplete temporary files.
- Symbolic links, directories and other nonregular targets cannot be overwritten. Complete recovery files remain until the user manages them.
- Plan changes during save dialogs invalidate the snapshot. Changes after writing retain dirty state.

Limits: existing-file protection combines optimistic version validation and cooperative locking; it is not a mandatory transaction lock on every third-party application. An uncooperative writer can still race in the very short final check-to-replace interval. Network filesystems also depend on server semantics. Windows, NTFS/exFAT, network paths and actual file locking require host acceptance. Atomic no-overwrite creation does not rely on an exists check.
