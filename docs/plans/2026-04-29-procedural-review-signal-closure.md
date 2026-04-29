# 职业法庭题材评审信号收口计划

> 日期: 2026-04-29
> 状态: implementation

## 背景

`projects/demo-climate-court-20260429` 的真实写作链路中，第一章《停雨申请》包含临时禁令、紧急异议、连带担保、限水损失、原始日志提交期限和接管链路异常等职业法庭悬疑压力，但 `review chapter` 仍把 `conflictTension` 打到低分。问题不是正文缺少张力，而是内置评审信号过窄，偏向通用追逐/威胁/背叛词。

同轮还暴露两个分析器负担：

- 已建档的 `worldbook` 引用被 `chapter analyze` 自动注册为 `inferred::...` character，污染 `entities.yaml`。
- `state_tags_for_paragraph` 会把 `没有离开` 识别为 `离开`。

## 适用规则

- 当前执行入口: `docs/roadmap.md` Track 2 工作流闭环稳定化与真实样例回归。
- 架构护栏: `services/` 只做纯业务逻辑；文件 I/O 保持在 commands/protocol。
- Owner: `services/story_review.py` 负责章节评分，`services/analyzer.py` 负责章节实体识别，`utils/text.py` 负责关键词匹配。
- 兼容性: 不新增 CLI 参数，不改变 YAML 文件协议；只扩展现有分析/评审信号。
- 痛点追踪: 本轮适用 AIF-005，并新增真实链路暴露的分析/题材信号痛点。

## 计划改动

1. 扩展评审关键词，让法律/程序/公共风险类张力能被 `plotMomentum`、`characterPressure`、`conflictTension` 识别。
2. 让 `chapter analyze` 在解析 `@{...}` 时优先对齐 `worldbook` 已建档条目，避免把势力/地点/物件推断成 character。
3. 增加状态关键词否定窗口，避免“没有离开/未受伤”等否定句生成状态候选。
4. 增加 smoke 测试覆盖职业法庭张力、worldbook 引用解析和否定状态词。
5. 回写 `docs/tracking/ai-friction-tracker.md`。

## 验证方式

- `python -m unittest tests.smoke.test_review_chapter`
- `python -m unittest tests.smoke.test_chapter_auto_register tests.smoke.test_keywords`
- 对 `projects/demo-climate-court-20260429` 重跑 `chapter analyze`、`context refresh`、`review chapter`、`review scene`。

## 追加验证记录

- `review chapter` 复评后为 `86/100 strong`，程序 / 证据 / 公共后果类张力已进入评分。
- `review scene --scene-index 1` 复评后为 `75/100 solid`，无问号的物证悬念已进入一幕钩子识别。
- `review preflight --volume-id volume-001` 已不再混入旧低分 scene review，也不再出现 worldbook faction 建档缺口。
- `review volume-self-template` 的 contract risk 归因已从误归 `characterContinuity` 修正为 `conflictEscalation`，并能为单章卷补 review-packet 证据锚点。
- 独立编辑代理的结构化 `editor-input` 已通过 `review volume-self --editor-input` 写入，自动刷新 `reviews/volume-001-review-packet.md`。
- `repairCoverage` 已能合并 root 自审弱项与独立编辑弱项，`workflow status --volume-id` 可直接提示“卷级闭环 / 爽点兑现 / 伏笔与回收节奏”等 editor 发现的问题。

## 新增未收口风险

- `volumeStructureCheck` 当前仍未消费 `commercialPositioning.releaseCadence` 或 `PRD.md` 中的“测试用三章首卷 / 第一卷程序胜负”目标，因此会把 outline 中当前存在的 1/1 章误视为 closure 前提已满足。
- 该问题已转入 `docs/tracking/ai-friction-tracker.md` 的 `AIF-010`，后续应在 preflight 层收口，而不是继续依赖独立编辑代理兜底。
