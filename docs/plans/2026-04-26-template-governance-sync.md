# 模板治理链路同步

> 日期: 2026-04-26
> 状态: 已实施
> 关联当前入口: `docs/roadmap.md`
> 关联前置方案:
> - `docs/plans/2026-04-26-agent-rule-lifecycle.md`
> - `docs/plans/2026-04-26-pr-governance-enforcement.md`
> - `docs/plans/2026-04-26-local-rule-touchpoint-guard.md`

## 1. 背景

真实仓库已经具备：

- `AGENTS.md` 中的规则生命周期与“适用规则”
- 本地 `pre-commit` 规则触点提醒
- CI 对 PR 描述的治理校验

但模板套件和 bootstrap playbook 仍停留在旧版本，存在：

- 治理模板缺少规则生命周期
- workflow 模板缺少 PR body 校验
- hook 模板引用脚本，但模板目录中没有对应脚本模板
- 没有 PR 模板资产

## 2. 目标

把真实仓库已落地的治理链路回灌到模板与初始化文档，确保新仓库 bootstrap 后默认具备：

1. 适用规则口径
2. 本地规则触点提醒
3. PR 模板
4. PR body CI 校验

## 3. 实施范围

- 更新 `docs/templates/ENGINEERING_GOVERNANCE.template.md`
- 更新 `docs/templates/COMMIT_POLICY.template.md`
- 更新 `docs/templates/git-hooks/pre-commit.template.sh`
- 更新 `docs/templates/workflows/governance.template.yml`
- 新增 `docs/templates/pull_request_template.template.md`
- 新增 `docs/templates/scripts/*`
- 更新 `docs/templates/README.md`
- 更新 `docs/AI_REPO_BOOTSTRAP_PLAYBOOK.md`

## 4. 验证

- `git diff --check -- docs/templates docs/AI_REPO_BOOTSTRAP_PLAYBOOK.md docs/plans/2026-04-26-template-governance-sync.md`
- 搜索确认模板中已包含 `Applicable Rules`、PR governance、rule touchpoints
