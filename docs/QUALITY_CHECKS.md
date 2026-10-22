# 自动质量检查 / Automated quality checks

推送到 `main` 或向 `main` 提交 PR 时，GitHub Actions 自动运行以下检查。也可以在 Actions → Quality checks → Run workflow 手动运行（工作流合并到默认分支后可见）。

Checks run on pushes to `main` and pull requests targeting `main`. After the workflow reaches the default branch, it can also be started from Actions → Quality checks → Run workflow.

| 检查 / Check | 内容 / Coverage | 失败条件 / Failure |
|---|---|---|
| Python static checks | Ruff 检查语法、未定义名称及会阻止执行的错误 / syntax, undefined names and execution errors | 任一所选规则违规 / any selected-rule violation |
| Regression tests (ubuntu-latest) | 完整 unittest 测试及程序自检 / full unittest suite and application self-check | 测试或自检失败 / test or self-check failure |
| Regression tests (windows-latest) | 相同测试在 Windows 运行 / the same checks on Windows | 测试或自检失败 / test or self-check failure |
| Dependency vulnerability audit | 检查 requirements.txt 中固定版本的 Python 分发包 / audit pinned Python distributions | 已知漏洞或扫描错误 / a known vulnerability or audit error |

## 查看结果 / Reading results

在 PR 的 Checks 页面或仓库 Actions 页面点击具体任务，展开失败步骤查看文件、行号和错误。测试日志、自检 JSON（若已生成）及依赖扫描 JSON 保留 7 天，可从运行页面的 Artifacts 下载。错误会保留为失败，不自动跳过历史测试，也不把扫描错误当作通过。

Open a check in the PR Checks tab or repository Actions page, then expand the failed step. Test logs, self-check JSON (when generated) and dependency-audit JSON are available as artifacts for seven days. Failures remain failures; historical tests are not automatically excluded and audit errors do not count as success.

配置仅使用只读仓库权限，不需要密钥或额外服务账号。Action 使用固定提交，检查工具在 `requirements-ci.txt` 中固定版本。取消同一分支的旧运行，避免重复消耗。

The workflow uses read-only repository permissions and needs no secrets or additional service account. Actions are pinned to commits, and check tools are pinned in `requirements-ci.txt`. A newer run cancels an older run on the same ref.

## 本地运行 / Running locally

在项目虚拟环境中运行 / Run in a project virtual environment:

```sh
python -m pip install -r requirements.txt -r requirements-ci.txt
python -m ruff check .
python -m unittest discover -s tests -v
python main.py --self-check verification-source.json
python -m pip_audit --disable-pip --no-deps -r requirements.txt
```

无显示服务器的 Linux 先设置 `QT_QPA_PLATFORM=offscreen`。Windows 与 CI 使用 Python 3.12；CI 也统一启用 UTF-8。应用自检会执行后台导出等实际操作，输出到临时目录。

On headless Linux, set `QT_QPA_PLATFORM=offscreen`. CI uses Python 3.12 and UTF-8 on both systems. Application self-checks exercise operations such as background export in temporary directories.

## 检查边界 / Limits

- 这套配置提供通过／失败结果，不产生 SonarQube 的 A～E 评级。Ruff 当前只启用 `E9`、`F63`、`F7`、`F82`，不代表已完成全部风格、复杂度或安全审计。
- pip-audit 的“未发现已知漏洞”只针对其漏洞数据库所覆盖的 Python 分发包，不能证明 Qt 内嵌原生库安全；[Qt 依赖状态](DEPENDENCY_STATUS.md) 中的待处理项仍需单独跟进。
- 离屏自动测试不能替代 Windows 实际窗口、DPI、剪贴板、文件关联与长时间运行检查。
- 新增工作流不等于启用合并限制。若要强制合并前通过检查，需要在仓库规则中另外选择这些检查。

These checks produce pass/fail results rather than SonarQube A–E ratings. The selected Ruff rules do not constitute a full style, complexity or security audit. pip-audit cannot establish the security of all native libraries bundled with Qt; the open concerns in [dependency status](DEPENDENCY_STATUS.md) remain separate. Headless tests do not replace manual desktop checks. Requiring successful checks before merging is a separate repository-rule setting.
