## 背景

- 当前任务是继续回补 `demo-urban-occult-long` 卷一前半章节，使其更接近商业网站连载单章长度与强度。
- `chapter-001` 已回补到最低字数线并通过章节/场景评审；下一目标为 `chapter-002`。

## 目标

- 在不改变 `chapter-002` 既有方向、案件骨架与结尾钩子的前提下，将正文扩写到商业最低线以上。
- 强化职业流程、旧城隍巷夜债规则、父亲旧案压力和单元案推进感。
- 维护 `outline.yaml` 中 `scenePlans` 与正文段落边界一致。

## 影响范围

- `projects/demo-urban-occult-long/chapters/chapter-002.md`
- `projects/demo-urban-occult-long/outline.yaml`
- `projects/demo-urban-occult-long/README.md`
- `docs/roadmap.md`
- `tests/smoke/test_demo_urban_occult_long_sample.py`

## 风险

- 复盘旧章时若运行会改写当前上下文的命令，可能把 `activeChapterId` 从当前卷末退回旧章节。
- 自动建议/投影链路对旧章仍存在叙事误判风险，因此本轮只做分析和评审，不做 retro `suggest/apply/refresh`。

## 验证

1. `PYTHONPATH=src python -m story_harness_cli chapter analyze --root projects/demo-urban-occult-long --chapter-id chapter-002`
2. `PYTHONPATH=src python -m story_harness_cli review chapter --root projects/demo-urban-occult-long --chapter-id chapter-002`
3. `PYTHONPATH=src python -m story_harness_cli review scene --root projects/demo-urban-occult-long --chapter-id chapter-002 --scene-index 2`
4. `PYTHONPATH=src python -m story_harness_cli review scene --root projects/demo-urban-occult-long --chapter-id chapter-002 --scene-index 3`
5. `PYTHONPATH=src python -m story_harness_cli doctor --root projects/demo-urban-occult-long`
6. `PYTHONPATH=src python -m story_harness_cli stats --root projects/demo-urban-occult-long`
7. `PYTHONPATH=src python -m story_harness_cli export --root projects/demo-urban-occult-long --format markdown --output projects/demo-urban-occult-long/manuscript.md`
