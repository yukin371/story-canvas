# PR 治理门禁落地

> 日期: 2026-04-26
> 状态: 已实施
> 关联当前入口: `docs/roadmap.md`
> 关联前置方案: `docs/plans/2026-04-26-agent-rule-lifecycle.md`

## 1. 背景

上一轮已经把“开发前知晓规则、开发中遵循、PR 时审查”的口径写进：

- `AGENTS.md`
- `docs/ENGINEERING_GOVERNANCE.md`
- `.github/pull_request_template.md`

但仍然停留在文档约定层，尚未形成自动门禁。

## 2. 目标

把 PR 模板中的关键治理字段变成 CI required check，至少校验：

1. PR 描述包含 `Applicable Rules`
2. 规则字段不是空模板
3. `Review Checklist` 没有未勾选项
4. `Validation` 与 `Risks` 有实际填写

## 3. 实施范围

- 新增 `scripts/check_pull_request_template.py`
- 在 `.github/workflows/ci.yml` 增加 PR governance job
- 增加 smoke test 验证脚本行为
- 同步 `CONTRIBUTING.md` 和治理文档中的现有门禁状态

## 4. 非目标

- 不做 reviewer 数量强制
- 不做 CODEOWNERS
- 不在本轮接入 branch protection API 或远端仓库设置
- 不把开发中规则遵循自动静态分析到所有源码层

## 5. 验证

- `python -m unittest tests.smoke.test_pr_governance`
- `PYTHONPATH=src python -m unittest discover -s tests`
- `git diff --check -- .github/workflows/ci.yml scripts/check_pull_request_template.py tests/smoke/test_pr_governance.py CONTRIBUTING.md docs/ENGINEERING_GOVERNANCE.md docs/COMMIT_POLICY.md docs/plans/2026-04-26-pr-governance-enforcement.md`

## 6. 收益

- PR 模板不再只是摆设
- 评审前先暴露适用规则、验证和残留风险
- 把“不能只谈 clean code / SOLID”变成实际合并前约束
