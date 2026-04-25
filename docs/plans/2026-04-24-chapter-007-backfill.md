## 背景

- `demo-urban-occult-long` 正按卷一前半顺序回补到商业连载可读长度。
- `chapter-001` 到 `chapter-006` 已完成回补，当前下一目标为 `chapter-007`。

## 目标

- 在不改变 `chapter-007` 既有剧情方向、章节落点和第八章承接关系的前提下，将正文扩写到商业最低线以上。
- 强化封街押解、纸马路线、名帖税号、寿银票簿和戏台前置运账之间的因果链。
- 维护 `outline.yaml` 中 `scenePlans` 与正文段落边界一致。

## 影响范围

- `projects/demo-urban-occult-long/chapters/chapter-007.md`
- `projects/demo-urban-occult-long/outline.yaml`
- `projects/demo-urban-occult-long/README.md`
- `docs/roadmap.md`
- `tests/smoke/test_demo_urban_occult_long_sample.py`

## 风险

- retro 分析命令仍可能把 `project.yaml` 的 `activeChapterId` 拉回旧章节，需要在验证后恢复 live context。
- 旧章不跑 `chapter suggest / review apply / projection apply / context refresh`，避免自动链路误写 canon。
- 本章承担第三单元案立案和向戏台交棒的任务，若新增情节改变“为什么不拦纸马、为什么先盯戏台、顾字线索如何出现”，会直接影响 `chapter-008`，因此本轮只补过程密度与决策压力，不改变结果。

## 验证

1. `PYTHONPATH=src python -m story_harness_cli chapter analyze --root projects/demo-urban-occult-long --chapter-id chapter-007`
2. `PYTHONPATH=src python -m story_harness_cli review chapter --root projects/demo-urban-occult-long --chapter-id chapter-007`
3. `PYTHONPATH=src python -m story_harness_cli review scene --root projects/demo-urban-occult-long --chapter-id chapter-007 --scene-index 2`
4. `PYTHONPATH=src python -m story_harness_cli review scene --root projects/demo-urban-occult-long --chapter-id chapter-007 --scene-index 3`
5. `PYTHONPATH=src python -m story_harness_cli doctor --root projects/demo-urban-occult-long`
6. `PYTHONPATH=src python -m story_harness_cli stats --root projects/demo-urban-occult-long`
7. `PYTHONPATH=src python -m story_harness_cli export --root projects/demo-urban-occult-long --format markdown --output projects/demo-urban-occult-long/manuscript.md`
