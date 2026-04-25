# 商业连载评审接入

## 背景

- `commercialPositioning` 已进入正式 schema，也已被 `init` 和 `doctor` 读取。
- 但在本轮之前，`review chapter` / `review scene` 还没有把商业连载目标真正纳入评分与回顾输出。
- 如果 review 不读取商业蓝图，项目仍然会停留在“能初始化、能校验，但不能按商业目标回顾”的半闭环状态。

## 目标

1. 让 `review chapter` 输出商业连载对齐结果。
2. 让 `review scene` 输出一幕级商业对齐结果。
3. 让章节加权评分可读取 `commercialPositioning.targetPlatform`。
4. 补齐长篇商业样例与 review smoke tests，证明功能已进入基线。

## 范围

- 更新 `src/story_harness_cli/services/story_review.py`
- 更新 `tests/smoke/test_review_chapter.py`
- 更新 `tests/smoke/test_review_scene.py`
- 更新 `tests/smoke/test_demo_urban_occult_long_sample.py`
- 同步 `services/MODULE.md`、`docs/roadmap.md`、评审与流程文档

## 验证

```powershell
$env:PYTHONPATH='src'
python -m py_compile src/story_harness_cli/services/story_review.py
python -m unittest tests.smoke.test_review_chapter tests.smoke.test_review_scene tests.smoke.test_demo_urban_occult_long_sample -v
python -m unittest discover -s tests
python -m story_harness_cli review chapter --root projects/demo-urban-occult-long --chapter-id chapter-001
python -m story_harness_cli review scene --root projects/demo-urban-occult-long --chapter-id chapter-001 --scene-index 1
```
