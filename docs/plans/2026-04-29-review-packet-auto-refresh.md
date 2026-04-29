# 2026-04-29 卷级审查包自动刷新最小切片

## 背景

根据 `docs/tracking/ai-friction-tracker.md`，`AIF-003` 的当前痛点是：

- `review volume-self` 或 mention hygiene 等卷级状态变化后，`workflow status` 可能已更新，但 `review-packet` 仍需手工重新导出。

这会让 agent 额外判断哪个文件是最新真相源，并手工补一条 `export --format review-packet --volume-id ...`。

## 适用规则

- 当前执行入口：`docs/roadmap.md`
- 长期痛点跟踪：`docs/tracking/ai-friction-tracker.md`
- 架构护栏：
  - `review.py` 负责卷审写入编排
  - `export.py` 是 `review-packet` Markdown 生成与写文件的 canonical owner
  - 不复制审查包生成逻辑，不引入新的并行状态文件
- 兼容性约束：
  - 不改变 `export --format review-packet` 的现有 CLI 行为
  - 自动刷新只作为 `review volume-self` 成功写入后的附加动作
  - `.yaml` / `.md` 仍保持 repo-native 文件协议

## 目标模块

- `src/story_harness_cli/commands/review.py`
- `src/story_harness_cli/commands/export.py`
- `tests/smoke/test_review_volume_self.py`
- 必要时：
  - `docs/tracking/ai-friction-tracker.md`
  - `docs/guides/volume-self-review.md`
  - `src/story_harness_cli/commands/MODULE.md`

## 计划改动

1. 在 `export.py` 提供卷级 `review-packet` 写文件 helper，继续复用现有 Markdown 生成逻辑。
2. 在 `review volume-self` 成功写入 `story-reviews.yaml` 后，自动刷新 repo-native 的 `reviews/<volume-id>-review-packet.md`。
3. 在命令输出中显式返回自动刷新结果，避免调用方再猜测是否需要补导出。

## 验证方式

1. `tests.smoke.test_review_volume_self`
2. `tests.smoke.test_workflow_command`
3. `python -m unittest discover -s tests`

## 需要同步的文档

- `src/story_harness_cli/commands/MODULE.md`
- `docs/guides/volume-self-review.md`
- `docs/tracking/ai-friction-tracker.md`

## 架构风险

- 若在 `review.py` 复制 `review-packet` Markdown 模板，会形成并行真相源。
- 若自动刷新路径不稳定，会让调用方仍需要猜测“最新审查包在哪”。

## 回滚路径

- 若自动刷新策略不稳，可只回退 `review volume-self` 的自动写包逻辑，保留 helper 和命令输出字段。
