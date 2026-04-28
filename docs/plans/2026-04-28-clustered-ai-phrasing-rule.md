# `clusteredAIPhrasing` 聚合规则落地记录

> 日期: 2026-04-28
> 状态: 已完成
> 关联入口: `docs/roadmap.md`
> 关联模块:
> - `src/story_harness_cli/services/style_detector.py`
> - `src/story_harness_cli/services/story_review.py`
> - `src/story_harness_cli/services/rule_registry.py`

## 1. 目标模块

- `services/style_detector.py`
- `services/story_review.py`
- `tests/smoke/`

## 2. 现有 owner

- AI 风格单项检测 owner: `services/style_detector.py`
- 规则元数据真相源: `services/rule_registry.py`
- chapter/scene review 风险与动作收敛: `services/story_review.py`

## 3. 影响面

- `style check`
- `review chapter`
- `review scene`
- `style repair`
- `status` / workflow 间接消费的 `ruleJudgements`

## 4. 适用规则

- 当前执行入口以 `docs/roadmap.md` 为准。
- 服务层保持纯函数，不引入文件 I/O。
- `base install` 继续 stdlib-only，不引入第三方依赖。
- 不新增平行配置真相源；项目级规则启停/豁免仍归 `review-rules.yaml`。
- 新增输出优先挂在既有 `patternResults / judgements / ruleJudgements` 语义层。

## 5. 计划改动

- 新增内建聚合规则 `clusteredAIPhrasing`。
- 基于既有 pattern results 聚合“多项轻度 AI 句式/可读性信号叠加”风险。
- 把该聚合信号接入 `styleAnalysis`、`judgements`、`priorityActions`、`contractAlignment.risks`。
- 补 smoke tests，覆盖 style/review 主链。

## 6. 验证方式

- `python -m unittest tests.smoke.test_style_detector tests.smoke.test_style_command tests.smoke.test_review_chapter`
- 必要时补跑全量 `python -m unittest discover -s tests`

## 7. 文档同步

- `docs/roadmap.md`
- `docs/plans/2026-04-27-optional-ai-detection-enhancement-plan.md`
- `src/story_harness_cli/services/MODULE.md`
- `src/story_harness_cli/commands/MODULE.md`

## 8. 风险与回滚

- 风险: 聚合规则若阈值过松，会把正常修辞密集章节误判成“AI 句群叠加”。
- 回滚路径: 删除 `clusteredAIPhrasing` 聚合逻辑与 registry 条目，不影响既有单项 detector。
