# Agent 规则生命周期收口

> 日期: 2026-04-26
> 状态: 已实施
> 关联当前入口: `docs/roadmap.md`
> 目标文件:
> - `AGENTS.md`
> - `docs/ENGINEERING_GOVERNANCE.md`
> - `docs/templates/AGENTS.template.md`
> - `.github/pull_request_template.md`

## 1. 背景

当前仓库已有：

- 读文档顺序
- 边界摘要要求
- 测试与文档同步要求

但还缺少一条更具体的工作链：

1. 开发前，如何显式识别本次改动受哪些规则约束
2. 开发中，如何避免规则漂移、重复实现和“为了 clean code / SOLID 而改”
3. PR / 自审时，如何按规则复核，而不是只做抽象风格评论

## 2. 目标

把“规则”从口头原则收敛为仓库内可执行的三个阶段：

1. 开发前：先整理适用规则清单
2. 开发中：按 rule source / owner / invariant 约束实现
3. PR 前：按显式 checklist 回审

## 3. 决策

### 3.1 AGENTS 侧

在 `AGENTS.md` 中明确：

- 仓库规则优先于抽象工程口号
- `clean code` / `SOLID` 只能作为辅助观察角度，不能单独构成改动理由
- 非平凡改动前必须写出“适用规则”
- 提交前 / PR 前必须按规则清单回审

### 3.2 工程治理侧

在 `docs/ENGINEERING_GOVERNANCE.md` 中明确：

- 开发前规则发现
- 开发中规则遵循
- PR 审查清单
- 文档同步也属于 required check

### 3.3 PR 入口侧

新增 `.github/pull_request_template.md`，让 PR 描述显式包含：

- 适用规则
- 兼容性/owner/边界检查
- 验证结果
- 残留风险

## 4. 非目标

- 不把 `clean code` / `SOLID` 全盘否定
- 不引入新的流程自动化或强制 reviewer 数量
- 不新增第二套“当前执行入口”

## 5. 验证

- `git diff --check -- AGENTS.md docs/ENGINEERING_GOVERNANCE.md docs/templates/AGENTS.template.md .github/pull_request_template.md docs/plans/2026-04-26-agent-rule-lifecycle.md`
- 搜索确认 `AGENTS.md` / 工程治理 / PR 模板都出现“适用规则”与 PR 审查口径

## 6. 预期收益

- 开发前先知道规则，而不是改完再补理由
- 开发中优先遵守仓库 owner / invariant / compatibility
- PR 时能围绕明确规则审查，而不是围绕抽象风格偏好争论
