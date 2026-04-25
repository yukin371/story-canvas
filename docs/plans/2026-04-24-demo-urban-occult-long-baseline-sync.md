## 背景

- `demo-urban-occult-long` 在 2026-04-24 完成 `chapter-005` 到 `chapter-008` 的商业化回补。
- 当前残留问题不在正文，而在样例 README、仓库 roadmap、smoke test 基线和 `project.yaml.activeChapterId` 运行态未完全同步。

## 目标

- 把 `demo-urban-occult-long` 的说明文档更新到最新基线。
- 把 smoke test 断言更新到 `chapter-008` 回补后的真实结果。
- 恢复样例项目默认活动章节到 `chapter-012`，避免 retro review/analyze 残留运行态。

## 约束

- 不改 CLI 接口、不改评分逻辑、不改样例剧情方向。
- 所有 `.yaml` 继续保持 JSON-compatible。
- 只同步已验证通过的事实，不写推测性结论。

## 计划改动

1. 更新 `projects/demo-urban-occult-long/README.md`
2. 更新 `docs/roadmap.md`
3. 更新 `tests/smoke/test_demo_urban_occult_long_sample.py`
4. 恢复 `projects/demo-urban-occult-long/project.yaml` 的 `activeChapterId`
5. 运行 `doctor`、`stats`、目标 smoke test、全量测试复核

## 验证方案

- `PYTHONPATH=src python -m story_harness_cli doctor --root projects/demo-urban-occult-long`
- `PYTHONPATH=src python -m story_harness_cli stats --root projects/demo-urban-occult-long`
- `PYTHONPATH=src python -m unittest tests.smoke.test_demo_urban_occult_long_sample -v`
- `PYTHONPATH=src python -m unittest discover -s tests`

## 风险

- `chapter analyze` / `review` 会改写 `project.yaml.activeChapterId`，验证结束后需复查并恢复到 `chapter-012`
- 文档与测试若继续使用旧基线，会让“商业长篇已收口”这一事实在仓库内出现冲突
