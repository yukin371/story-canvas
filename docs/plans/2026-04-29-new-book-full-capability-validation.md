# 2026-04-29 New Book Full Capability Validation

## 1. 目标模块

- `projects/new-book-validation-20260429`
- `story-harness-writing` adapter / workflow validation

## 2. 现有 owner

- 项目状态真相：Story Canvas 协议文件与 CLI 输出
- 写作方法：`story-harness-writing` skill / references
- workflow gate：`story-canvas` CLI

## 3. 影响面

- 新增一个独立验证项目
- 不修改既有项目正文
- 不修改 CLI 逻辑
- 会产生 review / projection / workflow / export 等验证产物

## 4. 适用规则

1. 当前执行入口：`docs/roadmap.md`
2. 写作规则：`docs/guides/writing-rules.md`
3. 创作流程：`docs/guides/creative-workflow.md`
4. 卷审模板：`docs/guides/volume-self-review.md`
5. adapter 规则：`.codex/skills/story-harness-writing/SKILL.md`
6. Active pain ids：`AIF-001`、`AIF-002`、`AIF-003`、`AIF-005`、`AIF-006`、`AIF-010`、`AIF-012`、`AIF-013`、`AIF-014`

## 5. 计划改动

1. 创建三章首卷新书：`雾钟档案`
2. 建立角色、世界规则、地点、势力
3. 写完 `volume-001` 的三章正文
4. 跑章节级闭环
5. 跑卷级自审与 review packet 导出
6. 记录工具问题和残留风险

## 6. 验证方式

1. `outline check`
2. `chapter analyze`
3. `chapter suggest`
4. `review apply`
5. `projection apply`
6. `context refresh`
7. `review chapter`
8. `review scene`
9. `style check/report`
10. `review preflight --volume-id`
11. `review volume-self-template`
12. `review volume-self`
13. `workflow status --volume-id`
14. `export --format review-packet`

## 7. 需要同步的文档

- 本计划
- `docs/tracking/ai-friction-tracker.md`，仅当出现新工具问题或现有痛点状态变化时更新

## 8. 2026-04-30 闭环结果

- 新书项目: `projects/new-book-validation-20260429`
- 作品名: `雾钟档案`
- 首卷: `volume-001 / 第一卷 雾钟点名`
- 章节:
  - `chapter-001` 第十三下雾钟
  - `chapter-002` 旧站缺页
  - `chapter-003` 缺页归档
- 当前结论:
  - `workflow status --volume-id volume-001` 已返回 `workflowStatus=completed`
  - `human_review_ready` gate 为 `ready`
  - 卷级 AI 自审已持久化，`closureStatus=closed`
  - `finalAllowHumanReview=true`
  - `editorAssessment.overallVerdict=pass`
- 导出产物:
  - `projects/new-book-validation-20260429/reviews/volume-001-review-packet.md`
  - `projects/new-book-validation-20260429/reviews/volume-001-review-packet.final.md`
  - `projects/new-book-validation-20260429/reviews/volume-001-self-review.draft.yaml`
  - `projects/new-book-validation-20260429/reviews/volume-001-author-fragment.json`
  - `projects/new-book-validation-20260429/reviews/volume-001-editor-pass.json`

## 9. 验证摘要

- `review preflight --volume-id volume-001`: mention action 0，world onboarding gap 0，closure checklist 4/4 pass
- `review chapter`: 三章均为 `solid`
- `review scene`: 三章九幕均不低于 `workable`
- `style report --volume-id volume-001`: 平均 19.7，仅 `chapter-001` 有轻度 `段落可读性` 扣 1 分
- `doctor`: `ok=true`，但仍有 5 条 warnings，其中三条字数 warning 来自 2000/3000 目标分叉
- `stats`: 仍错误使用最低 2000 / 推荐 3000，与 project.yaml 的 1200 / 1800 不一致

## 10. 记录的问题

- `AIF-015`: `stats` / `doctor` 字数目标与 `review preflight` 商业配置分叉。
- `AIF-016`: `scene-detect --replace` 覆盖已有三幕粒度时退化为单场景。

## 11. 接受风险

- 本轮是能力验证用三章短卷，接受部分 scene 仅为 `workable`，不继续为工具分数机械扩写。
- 不按 `stats` 当前 2000/3000 目标继续注水；以 `project.yaml` 的 1200/1800 与卷级自审结论为准。
- 独立编辑审查使用 `same_agent_fallback`，不是无上下文 subagent；该限制已写入卷审产物。
