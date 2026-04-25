## 背景

- `demo-urban-occult-long` 正按卷一前半顺序回补到商业连载可读长度。
- `chapter-001` 到 `chapter-005` 已完成回补，当前下一目标为 `chapter-006`。

## 目标

- 在不改变 `chapter-006` 既有剧情方向、章节落点和第七章承接关系的前提下，将正文扩写到商业最低线以上。
- 强化旧井口补位流程、井下送亲路规则、改债机制与“借债司”主线价值的因果链。
- 维护 `outline.yaml` 中 `scenePlans` 与正文段落边界一致。

## 影响范围

- `projects/demo-urban-occult-long/chapters/chapter-006.md`
- `projects/demo-urban-occult-long/outline.yaml`
- `projects/demo-urban-occult-long/README.md`
- `docs/roadmap.md`
- `tests/smoke/test_demo_urban_occult_long_sample.py`

## 风险

- retro 分析命令仍可能把 `project.yaml` 的 `activeChapterId` 拉回旧章节，需要在验证后恢复 live context。
- 旧章不跑 `chapter suggest / review apply / projection apply / context refresh`，避免自动链路误写 canon。
- 本章承担第二单元案正式收口，若新增情节改变“谁补位、如何截断、谁被救回、戏台钩子如何抛出”，会直接影响 `chapter-007`，因此本轮只补过程密度与代价感，不改变结果。

## 验证

1. `PYTHONPATH=src python -m story_harness_cli chapter analyze --root projects/demo-urban-occult-long --chapter-id chapter-006`
2. `PYTHONPATH=src python -m story_harness_cli review chapter --root projects/demo-urban-occult-long --chapter-id chapter-006`
3. `PYTHONPATH=src python -m story_harness_cli review scene --root projects/demo-urban-occult-long --chapter-id chapter-006 --scene-index 2`
4. `PYTHONPATH=src python -m story_harness_cli review scene --root projects/demo-urban-occult-long --chapter-id chapter-006 --scene-index 3`
5. `PYTHONPATH=src python -m story_harness_cli doctor --root projects/demo-urban-occult-long`
6. `PYTHONPATH=src python -m story_harness_cli stats --root projects/demo-urban-occult-long`
7. `PYTHONPATH=src python -m story_harness_cli export --root projects/demo-urban-occult-long --format markdown --output projects/demo-urban-occult-long/manuscript.md`
