# 2026-04-29 mention 修补后的卷级审查包自动刷新

## 背景

`AIF-003` 在上一轮已缓解一半：

- `review volume-self` 写入后会自动刷新 `reviews/<volume-id>-review-packet.md`

但 mention hygiene 相关写入口仍会让卷级审查包过期，尤其是：

- `entity mention-apply`
- `entity mention-tag-apply`
- `entity mention-adopt`
- `world mention-adopt`

## 适用规则

- 当前执行入口：`docs/roadmap.md`
- 长期痛点跟踪：`docs/tracking/ai-friction-tracker.md`
- 架构护栏：
  - `export.py` 是 review-packet 生成与写文件的 canonical owner
  - `entity.py` / `world.py` 只负责调用 export helper，不复制 Markdown 生成逻辑
  - 不新增平行状态文件

## 目标模块

- `src/story_harness_cli/commands/export.py`
- `src/story_harness_cli/commands/entity.py`
- `src/story_harness_cli/commands/world.py`
- `tests/smoke/test_entity_command.py`
- `tests/smoke/test_world_command.py`

## 计划改动

1. 在 `export.py` 提供按 `chapterId` 刷新对应卷级审查包的 helper。
2. mention 相关写入口成功修改正文或建档后，自动刷新所属卷的 `reviews/<volume-id>-review-packet.md`。
3. 命令输出显式返回刷新结果，避免调用方再猜测是否需要补导出。

## 验证方式

1. `tests.smoke.test_entity_command`
2. `tests.smoke.test_world_command`
3. 相关全量 smoke 回归
