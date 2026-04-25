## 背景

- `demo-urban-occult-long` 正按卷一前半顺序回补到商业连载可读长度。
- `chapter-001` 到 `chapter-007` 已完成回补，当前最后一个短章目标为 `chapter-008`。

## 目标

- 在不改变 `chapter-008` 既有剧情方向、章节落点和第九章承接关系的前提下，将正文扩写到商业最低线以上。
- 强化戏台借寿流程、后台押签逻辑、顾算盘隔帘施压和“连夜转去旧批发市场”的因果链。
- 维护 `outline.yaml` 中 `scenePlans` 与正文段落边界一致。

## 影响范围

- `projects/demo-urban-occult-long/chapters/chapter-008.md`
- `projects/demo-urban-occult-long/outline.yaml`
- `projects/demo-urban-occult-long/README.md`
- `docs/roadmap.md`
- `tests/smoke/test_demo_urban_occult_long_sample.py`

## 风险

- retro 分析命令仍可能把 `project.yaml` 的 `activeChapterId` 拉回旧章节，需要在验证后恢复 live context。
- 旧章不跑 `chapter suggest / review apply / projection apply / context refresh`，避免自动链路误写 canon。
- 本章要把第三单元案抬到制度层，但不能提前写穿 `chapter-009` 的仓库总账与杜魁灭口，因此本轮只补戏台现场、后台账簿和市场交接线索，不改变第九章的揭示顺序。

## 验证

1. `PYTHONPATH=src python -m story_harness_cli chapter analyze --root projects/demo-urban-occult-long --chapter-id chapter-008`
2. `PYTHONPATH=src python -m story_harness_cli review chapter --root projects/demo-urban-occult-long --chapter-id chapter-008`
3. `PYTHONPATH=src python -m story_harness_cli review scene --root projects/demo-urban-occult-long --chapter-id chapter-008 --scene-index 2`
4. `PYTHONPATH=src python -m story_harness_cli review scene --root projects/demo-urban-occult-long --chapter-id chapter-008 --scene-index 3`
5. `PYTHONPATH=src python -m story_harness_cli doctor --root projects/demo-urban-occult-long`
6. `PYTHONPATH=src python -m story_harness_cli stats --root projects/demo-urban-occult-long`
7. `PYTHONPATH=src python -m story_harness_cli export --root projects/demo-urban-occult-long --format markdown --output projects/demo-urban-occult-long/manuscript.md`
