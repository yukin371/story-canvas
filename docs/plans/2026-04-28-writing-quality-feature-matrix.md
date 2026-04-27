# 写作质量痛点与解决方案功能矩阵

> 日期: 2026-04-28
> 状态: 草稿
> 关联入口: `docs/roadmap.md`
> 关联规则: `docs/guides/writing-rules.md`、`docs/guides/volume-self-review.md`
> 关联阶段文档: `docs/plans/2026-04-27-functional-improvement-phasing.md`

## 1. 目的

把本轮人工审查中最明确、最具复现价值的三类痛点，整理成可实施的功能矩阵：

1. `style/review` 中文高频 AI 句式检测
2. `style/review` POV 越界与正文元信息泄漏检测
3. 卷级流程中更显式的 `首卷复杂度预算 / 疑点回收率 / 爽点兑现` 审查信号

本文档只回答四件事：

1. 当前规则有没有写
2. 当前 CLI 有没有真正工具化
3. 现在还差什么
4. 后续应落到哪个 owner、什么输入、什么输出、什么阶段

## 2. 状态图例

| 状态 | 含义 |
|------|------|
| `规则已存在` | 已在 guide/模板中明确写入，但未必被工具消费 |
| `部分工具化` | CLI 已有相邻信号或弱替代，但不能稳定暴露该问题 |
| `未工具化` | 目前主要靠人工或外部 agent 自觉发现 |

## 3. 总体判断

| 能力簇 | 规则层 | 工具层 | 当前判断 |
|------|------|------|------|
| 中文高频 AI 句式 | `规则已存在` | `部分工具化` | 已有比喻、叙事支架、方案文档腔等检测，但还没直接抓住你点名的高频中文翻转句式 |
| POV 越界 / 元信息泄漏 | `规则已存在` | `未工具化` | guide 已明确禁止，但 CLI 目前没有稳定 detector；其中“正文出现第X章/这一卷”等元信息泄漏应作为最高置信首批项 |
| 首卷复杂度 / 疑点回收 / 爽点兑现 | `规则已存在` | `部分工具化` | 已有 onboarding、伏笔债务、卷尾收束、repairCoverage，但还缺显式预算和兑现率信号 |

## 4. 功能矩阵

| 痛点 | 人工审查中的典型表现 | 当前规则 | 当前工具覆盖 | 当前缺口 | 建议功能 | 建议落点 | 输入信号 | 输出形态 | 优先级 | 实施阶段 |
|------|------|------|------|------|------|------|------|------|------|------|
| `不是……是……` 高频翻转 | 句子反复用解释式翻转代替具体表演，读感强 AI | `writing-rules 9.2` 已列为高频风险 | `style_detector` 只抓 `simileDensity`、`narrativeFrameRepetition`、`structuredPlanBlock` 等相邻信号 | 无专门 pattern id，无法在 style/review 中稳定点名 | 新增 `contrastFlipPattern`，统计 `不是A，是B`、`不是A，不是B，是C` | `services/style_detector.py`；消费方 `story_review.py`、`style repair` | 正文句子、标点切句结果、可选 profile 阈值 | `patternResults[]` + `judgements[]` + 修文建议 | `P0` | `Phase 3D` |
| `不是……更像……`、`不像……更像……` | 高频用“换个说法”的抽象递进句，缺少动作或结果 | `writing-rules 9.2/9.3` | 仅被 `narrativeFrameRepetition` 间接覆盖一小部分 | 句型本身未被识别，复用频率不可量化 | 新增 `analogicalPivotPattern`，识别“不是/不像/更像”组合翻转 | `services/style_detector.py` | 正文句级 regex、相邻短句组合 | `patternResults[]` + `constraints[]` | `P0` | `Phase 3D` |
| `真正……的，从来都是……`、`还有什么？`、模板化追问 | 容易形成故作深沉、追问式口癖，削弱人物口吻差异 | `writing-rules 9.2` | 目前没有口癖级 detector | 无法区分“偶尔合理使用”与“频率统治正文” | 新增 `templateCatchphrasePattern`，对高风险口癖按每千字与重复句次计分 | `services/style_detector.py`；可选 `style-profiles.yaml` 白名单 | 正文句子、对白句、角色对白分布 | `patternResults[]`；对白类 evidence 需保留上下文 | `P1` | `Phase 3D` |
| “像……”连发、抽象递进与弱物理反馈 | 单章并非一条句式问题，而是整组风格习惯问题 | `writing-rules 9.1-9.3` | 已有 `simileDensity`、`narrativeFrameRepetition`、`tellingEmotion`、`hedgeAdverbs` | 缺少“句群合并判定”，导致单项都不重但整体 AI 味仍高 | 增加 `clusteredAIPhrasing` 汇总层，把多个轻度 pattern 合并成一个 review 风险 | `services/style_detector.py` + `services/story_review.py` | 现有 patternResults 聚合、章节字数、连续命中段落 | `summary`、`priorityActions`、`ruleJudgements` | `P1` | `Phase 3D` |
| POV 越界 | 当前视角人物不可能看到背后落灰、敌方动作、远处细节 | `writing-rules 8.1/8.2` 已明确禁止 | 目前只有 `chapterHandoff`、一致性、世界检查等相邻能力 | 没有 POV 检测入口，也没有 evidence 结构 | 新增 `povOverreach` 检测：识别“背后/身后/远处/另一侧”等不可见方位 + 缺少转身/观察动作；识别敌方视角硬切 | 检测 owner `services/story_review.py` 或新建轻量 `services/pov_detector.py`；输出仍归 review/style 统一语义层 | 章节正文、可选 chapter POV 配置、方位词、感知动词、动作桥接词 | `ruleJudgements[]`、`priorityActions`、`consistencySignals` 或 `styleAnalysis.extensions` | `P0` | `Phase 3A` |
| 正文元信息泄漏 | 角色直接知道“第三章”“这一卷”“提纲”“流程”这类作者侧信息 | `writing-rules 8.3/8.4` | 当前没有显式 detector | 无法阻止“章节/卷/大纲/作者”类穿帮文本进入 review 阻塞项 | 新增 `metaLeakage` 检测，首批最高优先抓 `第X章` / `这一卷` / `上一章` 这类正文层穿帮，再扩到 `提纲`、`剧情`、`读者`、`作者`、`流程` | `services/style_detector.py` 或 `services/story_review.py` | 正文句子、meta 词表、引号场景过滤 | `patternResults[]` + 高严重度 `judgements[]` | `P0` | `Phase 3A` |
| 特殊题材需要合法越例 | 主角本身是作者、正文存在“小说中的小说”、角色在讨论章节结构时，不能被一刀切误判 | 规则层目前只有“默认禁止”，没有项目级豁免协议 | `style-profiles.yaml` 只支持术语/阈值级例外，不适合跨 review/gate 豁免 | 没有统一豁免，后续 detector 越多，误报只能靠硬编码回避 | 新增项目级 `rule exemption whitelist`，按 `ruleId + scope + allowedContext` 白名单豁免，而不是黑名单放行 | 建议新建 `protocol/review_rules.py`，commands/services 统一读取 | 项目配置、章节/卷/scene scope、允许短语、允许场景标签、说明理由 | 检测结果附 `exempted=true`、`exemptionReason`；doctor/status 可显示当前活跃豁免 | `P0` | `Phase 0 / Phase 3` |
| 首卷复杂度只增不收 | 新人物、新势力、新物件、新谜题连续堆高，第一卷像纯铺垫桶 | `writing-rules 4.2/7.3`、`volume-self-review 3.3` | `review preflight --volume-id` 已有 `outline-coverage`、`intro-world-onboarding`、`foreshadow-debt`、`closure-readiness` | 没有显式“复杂度预算”视图，无法回答首卷是否超载 | 在 `volumeStructureCheck` 下新增 `complexityBudget`，统计每章新增实体/世界项/谜团与回收量，给出净增趋势 | `commands/review_support.py`，可复用 `reference_mentions`、`world check`、`foreshadow check` | 卷内章节数、实体/世界 mention plan、谜团条目、伏笔状态 | `volumeStructureCheck.checklist[]`、`summary`、`changeRequestDrafts` | `P0` | `Phase 3A` |
| 疑点回收率过低 | 前 10 章持续加谜，却几乎没有短线回收，第一卷读者只会越看越乱 | `writing-rules 4.2/7.3/10.7`、`volume-self-review 3.3` | 已有 `foreshadow-debt` 与 `repairCoverage`，但更偏台账与自审覆盖，不是“本卷读感回收率” | 不能区分“合理长线”与“首卷过量疑点净增” | 新增 `mysteryPayoffBalance`，按卷统计新增谜团数、短线解释数、已到窗未回收数、净债务 | `commands/review_support.py`；必要时补 `worldbook.mysteries` 与 chapter-level mystery cues 轻量统计 | 伏笔账本、世界谜团、chapter preflight、volume role | `volumeStructureCheck.checklist[]`、workflow 阻塞理由 | `P0` | `Phase 3A` |
| 爽点不明确、长期只压不扬 | 全卷压抑但缺爆发；读者不知道这本书的核心体验是什么 | `writing-rules 4.2/5.5`、`volume-self-review 3.5` | `story_review` 已有商业承诺、hook、局部 payoff 提示；`volume_self_review` 有 `payoffDelivery` 维度 | 仍主要依赖 AI 自评分，工具侧没有显式兑现信号 | 新增 `payoffDeliverySignals`：统计阶段性胜负、反压制、能力兑现、秘密揭晓、情绪释放等章节级命中 | 检测入口 `services/story_review.py`；卷级聚合 `commands/review_support.py` / `workflow_engine.py` | 项目 `corePromises`、卷定位、章节 review、商业 hook、高潮/结尾章节 | 章节 `analysisSignals` 扩展 + 卷级 `volumeStructureCheck` + gate draft | `P0` | `Phase 3B` |
| 首卷不是完整小故事 | 有高潮但无收束，或只有抬势没有交付感 | `writing-rules 4.2`、`volume-self-review 2/7` | 已有 `closure-readiness`、`volume-self finalAllowHumanReview`、workflow volume gate | 目前仍偏“有没有材料与自审”，还不够显式判断“是不是完整引入卷” | 在 `volumeStructureCheck` 增补 `firstVolumeClosure` 规则，联动复杂度、疑点回收、爽点兑现三项信号 | `commands/review_support.py` + `services/workflow_engine.py` | 当前卷是否第一卷、卷尾章节状态、复杂度预算、疑点回收、payoff signals | `checklist[]` + `gateDecision.blockingRules` | `P1` | `Phase 3A/3B` |
| 自审能写结论，但工具不一定能拆成修稿动作 | 人类能看出问题，AI 自审也可能承认，但 workflow 仍缺可执行整改项 | `volume-self-review` 已要求 `issues`/`repairSuggestions` | 已有 `repairCoverage` 与 `changeRequestDrafts` | 新问题若无对应 detector，就无法进入结构化修稿闭环 | 新检测一律接入 `judgements -> priorityActions -> changeRequestDrafts` 链，不只停在 summary | `services/story_review.py`、`commands/status.py`、`services/workflow_engine.py` | 新增 detector 的 judgements、章节/卷定位 | `priorityActions`、`status.reviewStatus`、`workflow.changeRequestDrafts` | `P0` | 伴随各 Phase 实施 |

## 5. 建议字段与协议落点

### 5.1 style / review 层

建议优先新增而不是平行发明新结构：

| 建议字段 | 归属 | 用途 |
|------|------|------|
| `patternResults[].id=contrastFlipPattern` | `styleAnalysis` | 高频 `不是……是……` 句式 |
| `patternResults[].id=analogicalPivotPattern` | `styleAnalysis` | `不是/不像……更像……` 翻转句 |
| `patternResults[].id=templateCatchphrasePattern` | `styleAnalysis` | `真正……的，从来都是……`、`还有什么？` 等口癖 |
| `patternResults[].id=metaLeakage` | `styleAnalysis` | 正文元信息泄漏 |
| `styleAnalysis.extensions.povOverreach` 或 `consistencySignals.povOverreach` | review 侧扩展 | POV 越界 |
| `ruleJudgements[]` | chapter/scene/volume review | 统一对外暴露高风险检测结果 |

### 5.2 卷级流程层

建议优先扩展现有 `volumeStructureCheck` 和 workflow 摘要：

| 建议字段 | 归属 | 用途 |
|------|------|------|
| `volumeStructureCheck.checklist[].id=complexity-budget` | `review preflight --volume-id` | 首卷复杂度预算 |
| `volumeStructureCheck.checklist[].id=mystery-payoff-balance` | `review preflight --volume-id` | 疑点回收率 / 净债务 |
| `volumeStructureCheck.checklist[].id=payoff-delivery` | `review preflight --volume-id` | 爽点兑现 / 压抑释放节奏 |
| `workflow.currentGateDecision.blockingRules` | `workflow status/export --volume-id` | 将上述三类风险直接转成 gate 阻塞 |
| `workflow.changeRequestDrafts[]` | `workflow status/export --volume-id` | 生成卷级整改草案，而不是只给抽象风险提示 |

### 5.3 项目级规则白名单

建议不要把“规则豁免”混进 `style-profiles.yaml`。

原因：

1. `style-profiles.yaml` 的 owner 是风格阈值、术语、语域和句式例外。
2. 你现在要豁免的是 `metaLeakage`、`povOverreach`、卷级 gate 这类跨模块规则。
3. 如果继续往 `style-profiles.yaml` 塞，会把 style profile 变成泛规则真相源，边界会变脏。

更合适的是新增一个独立的可选项目配置，例如 `review-rules.yaml`，只做“规则启停与白名单豁免”。

建议最小结构：

```json
{
  "profiles": {
    "default": {
      "enabledRules": [
        "metaLeakage",
        "povOverreach",
        "contrastFlipPattern"
      ],
      "exemptions": [
        {
          "ruleId": "metaLeakage",
          "scope": {
            "chapterIds": ["chapter-012"],
            "scenePlanIds": ["scene-3"]
          },
          "allowWhen": {
            "quotedOnly": true,
            "matchPatterns": ["第[0-9一二三四五六七八九十]+章"]
          },
          "reason": "主角在讨论自己正在写的小说章节"
        }
      ]
    }
  },
  "activeProfile": "default"
}
```

建议原则：

1. 默认全规则开启，不做大面积关闭。
2. 例外一律走白名单，不走黑名单。
3. 白名单必须绑定 `ruleId`、`scope`、`allowWhen`、`reason`。
4. 能做局部 scope 就不要做全项目豁免。
5. `doctor/status` 应显示当前项目启用了哪些豁免，避免规则被静默关掉。

结论：

- 你的判断是对的，这里白名单比黑名单更合适。
- `metaLeakage` 的第一优先级确实应先抓正文里的 `第xx章`。
- 但要留一条结构化豁免通道，处理“主角是作者/书中书/角色讨论章节结构”这类明确特例。

## 6. 实施建议

### 6.1 第一批

优先做高置信、低歧义、最容易稳定复现的问题：

1. `metaLeakage`
2. `contrastFlipPattern`
3. `analogicalPivotPattern`
4. `rule exemption whitelist`
5. `complexityBudget`
6. `mysteryPayoffBalance`

原因：

- 这几项与人工审查结论高度一致
- 不依赖复杂语义理解就能先做出可用版本
- 最容易接回 `style report`、`review chapter`、`review preflight --volume-id`

### 6.2 第二批

在第一批稳定后补：

1. `templateCatchphrasePattern`
2. `clusteredAIPhrasing`
3. `payoffDeliverySignals`
4. `firstVolumeClosure`

原因：

- 这些更依赖聚合判断
- 需要和项目定位、读者承诺、商业 hook 一起看

### 6.3 第三批

最后补相对更难、误报率更需要真实样例回灌的能力：

1. `povOverreach`
2. 角色口吻差异与对白口癖归属
3. 可选外部 AI 检测增强路径

原因：

- POV 越界很难仅靠 regex 断真伪
- 需要真实项目样例回灌后再校阈值
- 保持 base install stdlib-only，不应一开始就把外部能力做成硬依赖

## 7. 对之前审查问题的阶段性判断

从“是否已经做了相当处理、应对是否合理”来看：

1. `实体/设定/伏笔进入主链` 已有明显进展，应对方向合理。
2. `章间承接、首卷 onboarding、卷级自审、repairCoverage` 已有可用骨架，但仍是部分工具化。
3. `中文高频 AI 句式`、`POV 越界`、`正文元信息泄漏` 仍是核心空缺。
4. `首卷复杂度预算 / 疑点回收率 / 爽点兑现` 现在已有规则口径和部分邻近信号，但还没形成真正可判定的卷级 gate。

结论：

- 之前人工审查看到的大问题，并不是“完全没处理”，而是“规则先写了、基础钩子补了、但最关键的显式 detector 还没落地”。
- 当前应对方式总体合理，但还差最后一段从“口径存在”到“稳定检测并阻塞 workflow”的收口。
