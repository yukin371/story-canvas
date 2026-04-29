# 2026-04-29 卷级 workflow 命令队列提示

## 背景

`AIF-005` 记录了真实卷级闭环需要调用方手动串联 `status/context/outline/review/workflow/export` 多条命令的问题。现有 `workflow status --volume-id` 已能判断 gate，但 `nextActions` 仍偏抽象，agent 需要自行翻译成下一条 CLI。

## 适用规则

- 当前执行入口：`docs/roadmap.md`
- 长期痛点跟踪：`docs/tracking/ai-friction-tracker.md`
- 架构护栏：
  - `workflow status/export --volume-id` 仍保持只读推断，不写入新的 volume workflow 状态文件
  - 命令队列只是派生提示，不成为新的真相源
  - 文件 I/O 仍在 commands 层，服务层保持纯推断

## 目标模块

- `src/story_harness_cli/commands/workflow.py`
- `tests/smoke/test_workflow_command.py`
- `src/story_harness_cli/commands/MODULE.md`
- `docs/tracking/ai-friction-tracker.md`

## 计划改动

1. 给卷级 workflow payload 增加 `orchestrationPlan`。
2. `orchestrationPlan.suggestedCommands` 按当前 gate 输出下一组可执行 CLI。
3. 不自动执行命令，不写 `workflow.yaml`，避免把只读状态提升成新的状态源。

## 验证方式

1. `python -m unittest tests.smoke.test_workflow_command`
2. 如资源允许，补跑全量 `python -m unittest discover -s tests`
