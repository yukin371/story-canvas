## 背景

- 当前项目已有 `stats` 项目统计、`outline beat-*` 细纲维护、`scenePlans` 显式场景边界，以及独立的 `structure` 模板能力。
- 但对连载小说最常见的章节字数约束还没有直接可用的 CLI 检查。
- 当前结构能力也偏“已有组件”，缺少对外口径上的明确回答：项目是否已经支持三幕、五幕、节拍式大纲指导章节写作。

## 目标

1. 为 CLI 增加章节级字数统计与目标区间检查。
2. 让用户能直接看到每章是否低于 2000 字、是否达到常规 3000 字区间。
3. 明确现有大纲指导能力：`outline`、`beats`、`scenePlans`、`structure` 模板各自承担什么职责。

## 计划改动

1. 扩展 `services/stats.py`，输出更细的章节字数信息和字数目标检查。
2. 如有必要，扩展 `commands/stats.py` 参数，让用户可配置最小字数与常规目标字数。
3. 补 smoke test，覆盖章节字数检查输出。
4. 同步文档，说明现有结构化写作能力与新字数检查能力。
5. 把章节字数阈值接入 `doctor`，让项目体检直接暴露短章风险。
6. 为 `structure` 增加 scaffold 落地能力，把结构模板直接写入章节 `beats` 与 `direction`。

## 验证

```powershell
$env:PYTHONPATH='src'
python -m story_harness_cli stats --root projects/demo-urban-occult-long
python -m story_harness_cli stats --root projects/demo-urban-occult-long --min-chapter-words 2000 --target-chapter-words 3000
python -m unittest tests.smoke.test_stats -v
```

## 风险

- 若把字数约束写死在服务层，后续不同平台的章节长度偏好会不够灵活。
- 若只统计总字数，不给章节级状态，无法真正用于连载交付检查。
- 若不明确 `structure` 与 `outline beats/scenePlans` 的关系，用户仍会误以为缺少结构化写作指导。

## 执行进展

- 已完成 `stats` 的章节字数目标输出。
- 已补 `doctor` 的章节最低/建议字数诊断。
- 已补 `structure scaffold`，可把三幕 / 五幕 / 节拍模板直接落到章节 `beats` 与 `direction`。
