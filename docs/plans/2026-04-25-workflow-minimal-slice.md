# Workflow 最小切片实施计划

> 日期: 2026-04-25
> 状态: 已完成（后续已由 `2026-04-25-workflow-state-machine-completion.md` 补齐完整状态机）
> 关联: `docs/v3-plan.md`, `docs/plans/2026-04-25-workflow-gap-analysis.md`

## 1. 目标

在不改变现有创作闭环语义的前提下，落地 workflow 的最小可用切片：

- 新增 `workflow.yaml`
- 新增 `workflow status`
- 新增 `workflow run --non-interactive`

本轮只做“状态显式化”和“下一步推荐”，不做交互 gate 决策。该最小切片已完成，并作为后续完整状态机的落地基础。

## 2. 范围

### 2.1 需要改动

- `src/story_harness_cli/protocol/schema.py`
- `src/story_harness_cli/protocol/files.py`
- `src/story_harness_cli/protocol/state.py`
- `src/story_harness_cli/services/workflow_engine.py`
- `src/story_harness_cli/services/__init__.py`
- `src/story_harness_cli/commands/workflow.py`
- `src/story_harness_cli/commands/__init__.py`
- `src/story_harness_cli/cli.py`
- `tests/smoke/test_workflow_command.py`
- `tests/smoke/test_schema.py`

### 2.2 本轮不做

- `workflow advance`
- `workflow reset`
- `workflow export`
- 卷级 review 聚合
- workflow profile / pack
- 宿主 adapter 对接 workflow API

## 3. 设计口径

### 3.1 workflow 状态域

新增 `workflow_progress`，落盘到 `workflow.yaml`。

最小字段：

```json
{
  "currentStage": "",
  "targetChapterId": null,
  "gateHistory": [],
  "stageResults": {},
  "updatedAt": "",
  "lastRunMode": ""
}
```

### 3.2 最小阶段集合

- `project_contract`
- `outline_ready`
- `chapter_review_ready`
- `scene_review_ready`
- `export_ready`

### 3.3 阶段推断来源

- `project_contract`: `evaluate_project_story_gate`
- `outline_ready`: `evaluate_chapter_outline_readiness`
- `chapter_review_ready`: 目标章节正文文件 + `story_reviews.chapterReviews`
- `scene_review_ready`: 目标章节正文文件 + `story_reviews.sceneReviews`
- `export_ready`: 章节 review 和 scene review 都完成

## 4. 验证

### 4.1 自动化

- `python -m unittest tests.smoke.test_workflow_command tests.smoke.test_schema`

### 4.2 手工检查

- 对无 `workflow.yaml` 的旧项目运行 `workflow status`
- 对 demo 或临时项目运行 `workflow run --non-interactive`
- 检查生成的 `workflow.yaml` 是否与推断结果一致

## 5. 风险

- workflow 阶段名称和现有 guide 的语义可能存在轻微错位
- 当前仅实现“推断与持久化”，用户可能误以为已支持完整状态机

## 6. 回滚

- 删除 `workflow` 命令组
- 删除 `workflow_progress` state domain
- 删除新增测试与本计划文档
