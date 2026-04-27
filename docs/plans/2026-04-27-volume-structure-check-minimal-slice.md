# 卷级结构检查最小切片

> 日期: 2026-04-27
> 状态: 进行中
> 关联: `docs/plans/2026-04-26-workflow-gap-notes.md`, `docs/plans/2026-04-27-functional-improvement-phasing.md`

## 1. 目标

在不新增命令、不新增真相源的前提下，把“卷级结构模板与结构完成度审查”的最小只读信号挂进现有 CLI：

- `review preflight --volume-id`
- `review volume-self-template`
- `export --format review-packet --volume-id`

## 2. 边界

- 不新增 `workflow.yaml` 字段
- 不新增独立 `volume-structure` 命令
- 不把启发式结构判断写成硬门禁
- 只提供结构检查稿，先服务 AI 自审与人工审查

## 3. 最小输出

- `volumeStructureCheck.role`
  - `intro-volume`
  - `standard-volume`
- `volumeStructureCheck.phaseAssignments`
  - 按章节顺序给出 `opening / build / turn / climax / close` 的轻量阶段映射
- `volumeStructureCheck.checklist`
  - `outline-coverage`
  - `intro-world-onboarding`
  - `foreshadow-debt`
  - `closure-readiness`
- `volumeStructureCheck.summary`
  - `passCount`
  - `riskCount`
  - `missingCount`

## 4. 规则来源

- 第一卷 / 引入卷需要更明确的 onboarding 与结构职责
- 卷级闭环不应只看单章通过，还要看整卷是否具备基本收束与兑现
- 现有工具已经有 mention / foreshadow / world onboarding 信号，应优先复用，而不是再造平行输入

## 5. 验证

- `tests/smoke/test_review_preflight.py`
- `tests/smoke/test_review_volume_self.py`
- `tests/smoke/test_export_spec.py`
