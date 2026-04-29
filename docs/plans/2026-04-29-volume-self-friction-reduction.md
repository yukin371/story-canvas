# 2026-04-29 卷级自审减负与 editor 导入最小切片

## 背景

根据 `docs/tracking/ai-friction-tracker.md`，当前最重的两个 AI 实施痛点是：

1. `AIF-001` 卷级自审输入手工负担过重
2. `AIF-002` 多代理 editor 结论无法直接导入卷审

真实流程已经证明：

- `review volume-self-template`
- `review volume-self`
- `workflow status --volume-id`

这条卷级链路本身成立，但 agent 仍需要手工拼装大段输入并手动抄录独立 editor 结论。

## 适用规则

- 当前执行入口：`docs/roadmap.md`
- 长期痛点跟踪：`docs/tracking/ai-friction-tracker.md`
- 架构护栏：
  - `commands/` 负责 CLI 编排、参数解析、文件 I/O
  - `services/` 负责卷级自审的纯归一化/校验逻辑
  - 不引入新的并行真相源
- 兼容性约束：
  - 不破坏现有 `review volume-self` 参数
  - 新增字段/参数应保持增量兼容
  - `.yaml` 文件仍必须为 JSON-compatible

## 目标模块

- `src/story_harness_cli/commands/review.py`
- `src/story_harness_cli/services/volume_self_review.py`
- 必要时：
  - `src/story_harness_cli/protocol/schema.py`
  - `tests/smoke/test_review_volume_self.py`
  - `tests/smoke/test_workflow_command.py`

## 计划改动

1. 为卷级自审增加“更接近可提交”的 draft 生成能力，尽量复用已有 chapter/scene/style/preflight 证据自动填更多字段，而不是只给全空模板。
2. 为 `review volume-self` 增加 editor 结构化输入导入/合并能力，允许把独立 editor 结果作为独立文件注入，减少手工搬运。
3. 保持现有 CLI 真相源不变：最终仍由 `review volume-self` 做统一校验与持久化。

## 验证方式

1. smoke tests 覆盖：
   - 生成 draft 后不再是全 0 / 全占位
   - 通过 editor 输入文件合并后能成功写入卷审
2. 用临时项目验证：
   - `review volume-self-template` 或新增 draft 入口
   - `review volume-self --input ... --editor-input ...`
   - `workflow status --volume-id`

## 需要同步的文档

- `src/story_harness_cli/commands/MODULE.md`
- `src/story_harness_cli/services/MODULE.md`
- `docs/tracking/ai-friction-tracker.md`
- 必要时 `docs/guides/volume-self-review.md`

## 架构风险

- 若把 editor 导入逻辑散落到多个命令，会形成新的平行卷审入口。
- 若 draft 生成直接绕开现有 `volume_self_review.py` 结构，会让模板、校验和最终写入口径分叉。

## 重复实现风险

- 不能再发明一套“代理专用卷审格式”；必须与现有 `review volume-self` 结构兼容。
- 不能把 editor verdict 持久化成另一份并行状态文件。

## 回滚路径

- 本轮优先做增量参数和字段补全。
- 若 draft 自动填充质量不稳，可单独回退自动填充逻辑，保留 editor 导入能力。
