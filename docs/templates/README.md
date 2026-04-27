# AI Repo Bootstrap 模板套件

> 目标: 给新仓库提供一套可以直接复制、实例化、裁剪的治理模板，而不是只有原则说明

## 1. 推荐实例化顺序

1. `PROJECT_PROFILE.template.md`
2. `AGENTS.template.md`
3. 二选一:
   - `roadmap.template.md`
   - `current-execution-control.template.md`
4. `ARCHITECTURE_GUARDRAILS.template.md`
5. `MODULE.template.md`
6. `ENGINEERING_GOVERNANCE.template.md`
7. `DOCUMENT_LIFECYCLE.template.md`
8. `plan.template.md`
9. `ADR.template.md`
10. `RELEASE_CHECKLIST.template.md`
11. `COMMIT_POLICY.template.md`
12. `git-hooks/` 与 `workflows/` 下的脚本模板

## 2. 最小可用套件

如果只想先建立最低治理骨架，至少实例化:

- `PROJECT_PROFILE.template.md`
- `AGENTS.template.md`
- `roadmap.template.md` 或 `current-execution-control.template.md`
- `ARCHITECTURE_GUARDRAILS.template.md`
- `MODULE.template.md`
- `plan.template.md`
- `ADR.template.md`

## 3. 完整推荐套件

若希望后续 AI 可以稳定接手并持续开发，建议再补:

- `ENGINEERING_GOVERNANCE.template.md`
- `DOCUMENT_LIFECYCLE.template.md`
- `RELEASE_CHECKLIST.template.md`
- `COMMIT_POLICY.template.md`
- `pull_request_template.template.md`
- `git-hooks/commit-msg.template.sh`
- `git-hooks/pre-commit.template.sh`
- `workflows/governance.template.yml`
- `scripts/check_commit_message.template.sh`
- `scripts/check_commit_messages_range.template.sh`
- `scripts/check_pull_request_template.template.py`
- `scripts/check_rule_touchpoints.template.py`

## 4. 使用约束

- `roadmap` 与 `current-execution-control` 只能选一个作为当前执行真相
- `MODULE.template.md` 只给关键模块，不要全仓库铺满
- `plan.template.md` 是临时实施文档，不是永久 roadmap
- `ADR.template.md` 只记录长期边界决策
- 模板实例化后，必须替换 `TBD`、`[仓库名]`、`[owner]` 等占位符

## 5. 推荐落点

| 模板 | 推荐目标路径 |
|------|------|
| `PROJECT_PROFILE.template.md` | `docs/PROJECT_PROFILE.md` |
| `AGENTS.template.md` | `AGENTS.md` |
| `roadmap.template.md` | `docs/roadmap.md` |
| `current-execution-control.template.md` | `docs/plans/current-execution-control.md` |
| `ARCHITECTURE_GUARDRAILS.template.md` | `docs/ARCHITECTURE_GUARDRAILS.md` |
| `MODULE.template.md` | `[模块目录]/MODULE.md` 或 `[模块目录]/ARCHITECTURE.md` |
| `plan.template.md` | `docs/plans/YYYY-MM-DD-<topic>.md` |
| `ADR.template.md` | `docs/adr/ADR-XXX-<topic>.md` |
| `ENGINEERING_GOVERNANCE.template.md` | `docs/ENGINEERING_GOVERNANCE.md` |
| `DOCUMENT_LIFECYCLE.template.md` | `docs/DOCUMENT_LIFECYCLE.md` |
| `RELEASE_CHECKLIST.template.md` | `docs/releases/RELEASE_CHECKLIST.md` |
| `COMMIT_POLICY.template.md` | `docs/COMMIT_POLICY.md` |
| `pull_request_template.template.md` | `.github/pull_request_template.md` |

## 6. 为什么还提供 hooks 和 workflow 模板

只有文档规则没有自动化防线，AI 很容易在提交信息、协作者标记、CI 门禁和文档状态上反复走偏。

所以模板套件除了 Markdown，也提供:

- 本地 `commit-msg` hook
- 本地 `pre-commit` hook
- PR 模板
- GitHub workflow 治理模板
- 对应的治理脚本模板

这样仓库可以同时拥有:

- 文档层规则
- 本地提交前拦截
- CI 侧兜底检查

## 7. 写作模板补充

除治理模板外，当前仓库也开始补充“写前约束与 prompt 骨架”类模板，位置在 `docs/templates/writing/`：

- `intake-layered.template.md`
  - 第一阶段立项问答骨架
- `prompt-skeletons.template.md`
  - PRD / 大纲 / 章节 / 评审的中文优先 prompt 骨架
- `genre-overlay.template.md`
  - 类型层最小模板

这些模板服务 Story Canvas 当前工作流，不引入新的项目状态文件或平行 protocol。
