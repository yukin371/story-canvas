## 背景

- `demo-urban-occult-long` 正在按卷一前半顺序回补到商业连载可读长度。
- `chapter-001`、`chapter-002` 已完成回补，当前下一目标为 `chapter-003`。

## 目标

- 在不改变 `chapter-003` 既有剧情方向、章节落点和第四章承接关系的前提下，将正文扩写到商业最低线以上。
- 强化废庙布控、借火仪轨、夺印冲突、父线抬升和“临牌上岗”的阶段性兑现感。
- 维护 `outline.yaml` 中 `scenePlans` 与正文段落边界一致。

## 影响范围

- `projects/demo-urban-occult-long/chapters/chapter-003.md`
- `projects/demo-urban-occult-long/outline.yaml`
- `projects/demo-urban-occult-long/README.md`
- `docs/roadmap.md`
- `tests/smoke/test_demo_urban_occult_long_sample.py`

## 风险

- retro 分析命令仍可能把 `project.yaml` 的 `activeChapterId` 拉回旧章节，需要在验证后确认 live context。
- 旧章不跑 `chapter suggest / review apply / projection apply / context refresh`，避免自动链路误写 canon。

## 验证

1. `PYTHONPATH=src python -m story_harness_cli chapter analyze --root projects/demo-urban-occult-long --chapter-id chapter-003`
2. `PYTHONPATH=src python -m story_harness_cli review chapter --root projects/demo-urban-occult-long --chapter-id chapter-003`
3. `PYTHONPATH=src python -m story_harness_cli review scene --root projects/demo-urban-occult-long --chapter-id chapter-003 --scene-index 2`
4. `PYTHONPATH=src python -m story_harness_cli review scene --root projects/demo-urban-occult-long --chapter-id chapter-003 --scene-index 3`
5. `PYTHONPATH=src python -m story_harness_cli doctor --root projects/demo-urban-occult-long`
6. `PYTHONPATH=src python -m story_harness_cli stats --root projects/demo-urban-occult-long`
7. `PYTHONPATH=src python -m story_harness_cli export --root projects/demo-urban-occult-long --format markdown --output projects/demo-urban-occult-long/manuscript.md`
