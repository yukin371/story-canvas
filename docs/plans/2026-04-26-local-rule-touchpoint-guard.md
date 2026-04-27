# 本地规则触点提醒

> 日期: 2026-04-26
> 状态: 已实施
> 关联当前入口: `docs/roadmap.md`
> 关联前置方案:
> - `docs/plans/2026-04-26-agent-rule-lifecycle.md`
> - `docs/plans/2026-04-26-pr-governance-enforcement.md`

## 1. 背景

仓库已经具备：

- 文档层规则生命周期
- PR 模板
- CI 级 PR 描述校验

但开发进行中仍然缺少一层本地提醒，导致很多规则要到 commit 或 PR 阶段才显式暴露。

## 2. 目标

在本地 `pre-commit` 阶段增加“规则触点提醒”，做到：

1. 根据 staged files 提示本次改动 likely 受哪些规则约束
2. 对明显需要文档同步但尚未同步的情况给出 warning
3. 不引入高误报的硬阻断

## 3. 实施范围

- 新增 `scripts/check_rule_touchpoints.py`
- 在 `.githooks/pre-commit` 中调用该脚本
- 增加 smoke test
- 同步贡献与治理文档

## 4. 设计原则

- 只做 rule hint 和 doc-sync warning，不做复杂静态分析
- 只依赖 Python stdlib
- 输出要直接映射到仓库已有 rule source：
  - `AGENTS.md`
  - `docs/ARCHITECTURE_GUARDRAILS.md`
  - `MODULE.md`
  - 工程治理文档

## 5. 触点规则

- `commands/` 变更：提醒检查命令注册、I/O 边界、命令层 owner
- `services/` 变更：提醒检查纯函数、不变量、输出结构
- `protocol/` 变更：提醒检查文件协议、schema、兼容性
- `AGENTS / governance / CI / hooks / PR template` 变更：提醒同步治理文档与模板口径

同时对下列情况发 warning：

- `commands/` 变更但未见 `commands/MODULE.md` 或 `docs/` 变更
- `services/` 变更但未见 `services/MODULE.md` 或 `docs/` 变更
- `protocol/` 变更但未见 `protocol/MODULE.md` 或 `docs/` 变更
- 治理资产变更但未见 `docs/ENGINEERING_GOVERNANCE.md` / `AGENTS.md` / `CONTRIBUTING.md` 同步

## 6. 验证

- `python -m unittest tests.smoke.test_rule_touchpoints`
- `PYTHONPATH=src python -m unittest discover -s tests`
- `git diff --check -- .githooks/pre-commit scripts/check_rule_touchpoints.py tests/smoke/test_rule_touchpoints.py CONTRIBUTING.md docs/ENGINEERING_GOVERNANCE.md docs/plans/2026-04-26-local-rule-touchpoint-guard.md`
