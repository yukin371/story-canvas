# Workflow 状态机补完计划

> 日期: 2026-04-25
> 状态: 已完成
> 关联: `docs/plans/2026-04-25-workflow-minimal-slice.md`, `docs/v3-plan.md`

## 1. 目标

在现有 `workflow status` / `workflow run` 最小切片基础上，补齐 workflow 的显式状态机能力：

- `workflow advance`
- `workflow reset`
- `workflow export`
- `workflow run --resume-from <stage>`

本轮仍然只覆盖当前最小阶段集合，不引入 volume review 或 profile。

## 2. 范围

### 2.1 需要改动

- `src/story_harness_cli/services/workflow_engine.py`
- `src/story_harness_cli/commands/workflow.py`
- `src/story_harness_cli/protocol/schema.py`
- `tests/smoke/test_workflow_command.py`
- `README.md`
- `docs/PROJECT_PROFILE.md`

### 2.2 本轮不做

- volume review
- workflow profile / pack
- adapter 改走 workflow API

## 3. 状态机语义

### 3.1 决策

- `accept`: 只有当 gate 的 inferred 条件已满足时才允许推进
- `modify`: 记录反馈并保持当前 gate，不推进
- `reject`: 记录反馈并保持当前 gate，不推进

### 3.2 reset

- `reset --from-gate <stage>` 会清除该 gate 及其后续 gate 的 decision metadata 和 gate history
- reset 后 `currentStage` 回到指定 gate

### 3.3 export

- 输出当前 persisted workflow 快照
- 默认 stdout JSON
- `-o` 写文件

## 4. 验证

- `python -m unittest tests.smoke.test_workflow_command tests.smoke.test_schema`
- 必要时补跑 `tests.smoke.test_review_chapter tests.smoke.test_review_scene`

当前结果：

- `PYTHONPATH=src python -m unittest tests.smoke.test_workflow_command tests.smoke.test_schema tests.smoke.test_review_chapter tests.smoke.test_review_scene`
- 结果：`Ran 22 tests ... OK`
