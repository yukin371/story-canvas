# 场景计划自动引导落地

> 日期: 2026-04-23
> 状态: 已完成

## 目标模块

- `src/story_harness_cli/commands/outline.py`
- `src/story_harness_cli/services/story_review.py`
- `tests/smoke/test_outline_loop.py`
- `projects/demo-novel/project.yaml`
- `projects/demo-novel/outline.yaml`

## 现有 owner

- scene 候选切分 owner: `services/story_review.py`
- scenePlans CLI 维护 owner: `commands/outline.py`
- demo 样例工程状态 owner: `projects/demo-novel/*`

## 影响面

- 新增 `outline scene-detect` 子命令
- 启发式候选 scene 可转为显式 `scenePlans`
- `demo-novel` 从“仅能 heuristic scene review”升级为“显式 scene plan + 契约上下文”

## 计划改动

1. 在 `services/story_review.py` 中新增 scenePlans 检测构建函数
2. 在 `commands/outline.py` 中新增 `scene-detect`，支持安全替换已有 `scenePlans`
3. 补 smoke tests，覆盖生成、替换保护与显式评审切换
4. 回填 `projects/demo-novel/project.yaml` 的定位与故事契约
5. 为 `demo-novel` 生成显式 `scenePlans` 并回跑 `review scene`
6. 同步 roadmap / module / protocol guide 文档

## 最小范围

- 只做“候选 scene -> scenePlans”的引导，不引入 scene graph
- detect 结果必须显式标记为启发式生成
- 不改变 `review scene` 现有参数和输出结构

## 验证方式

- `python -m unittest tests.smoke.test_outline_loop tests.smoke.test_review_scene`
- `python -m unittest discover -s tests`
- `$env:PYTHONPATH='src'; python -m story_harness_cli outline scene-detect --help`
- `$env:PYTHONPATH='src'; python -m story_harness_cli review scene --root projects/demo-novel --chapter-id chapter-008 --list-scenes`
- `$env:PYTHONPATH='src'; python -m story_harness_cli review scene --root projects/demo-novel --chapter-id chapter-008 --scene-index 1`

## 需要同步的文档

- `docs/roadmap.md`
- `docs/protocol/file-layout.md`
- `src/story_harness_cli/commands/MODULE.md`
- `src/story_harness_cli/services/MODULE.md`

## 架构风险

- 如果 detect 逻辑放进 commands，会与 scene split owner 冲突
- 若 detect 直接覆盖已有 scenePlans，可能抹掉作者手工维护边界

## 重复实现风险

- 禁止新造第二套 scene 切分规则；统一复用 `story_review.py` 内的候选逻辑

## 回滚路径

- 移除 `scene-detect` 命令与 demo 样例 `scenePlans`

## 兼容性影响

- 仅新增子命令和 scene plan 元数据字段
- 旧项目不使用 `scene-detect` 也可继续沿用现有流程
