# 2026-04-29 mention 修补写后自检

## 背景

`AIF-004` 记录了真实流程里 `entity mention-tag-apply` 修补后仍需要人工读正文确认的问题。上一轮已经让 mention 修补自动刷新卷级审查包，但命令本身仍缺少写后健康信号。

## 适用规则

- 当前执行入口：`docs/roadmap.md`
- 长期痛点跟踪：`docs/tracking/ai-friction-tracker.md`
- 架构护栏：
  - 正文文件写入仍由 `commands/entity.py` 负责
  - mention 候选仍复用 `services/reference_mentions.py`
  - 坏标签识别复用 `utils/text.py`
  - 不新增平行状态文件

## 目标模块

- `src/story_harness_cli/commands/entity.py`
- `tests/smoke/test_entity_command.py`
- `src/story_harness_cli/commands/MODULE.md`
- `docs/tracking/ai-friction-tracker.md`

## 计划改动

1. `mention-tag-apply` / `mention-apply` 在写入前对替换后的正文做最小坏标签校验。
2. 命令输出新增 `postApplyCheck`，返回剩余 mention action 摘要和是否需要人工复核。
3. 用 smoke test 固化“修补后无需人工读正文才能知道是否写坏”的机器可读信号。

## 验证方式

1. `python -m unittest tests.smoke.test_entity_command`
2. 必要时补跑 status / workflow 相关 smoke，确认输出字段追加不破坏既有闭环。
