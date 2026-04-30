# 卷级 AI 自审模板

> 最后更新: 2026-04-30
> 适用对象: 作者 / 外部 AI / 审查代理
> 关联规则: [写作规则包](./writing-rules.md)
> 关联流程: [创作流程指南](./creative-workflow.md)

## 1. 目的

把“整卷写完后的 AI 自审”固定成可重复执行的结构，而不是临场自由发挥。

卷级自审发生在：

1. 一个完整卷或一个明确小故事单元完成后
2. 人工审查前
3. 导出审查材料前

当前 CLI 录入方式：

```powershell
python -m story_harness_cli review volume-self-template --root <project-root> --volume-id <volume-id> --output <template-dir-or-file>
python -m story_harness_cli review volume-self --root <project-root> --volume-id <volume-id> --input <volume-self-review.yaml>
```

建议先用 `review volume-self-template` 生成骨架。当前模板会根据 `preflight`、`volumeStructureCheck`、chapter/scene review 和 style aggregate 启发式预填 root `scores/issues/closureAssessment`，但这些字段仍是 draft，写回前需要作者或代理明确复核。

若 author / editor 结果是分片产物，当前也支持在 CLI 里合稿，而不是手工改整份文件：

```powershell
python -m story_harness_cli review volume-self-template --root <project-root> --volume-id <volume-id> --merge-input <author-fragment.json> --editor-input <editor-fragment.json> --output <draft-dir-or-file>
python -m story_harness_cli review volume-self --root <project-root> --volume-id <volume-id> --input <author-base.yaml> --editor-input <editor-fragment.json>
```

- `--merge-input`：通用局部覆盖输入，可重复传入
- `--editor-input`：只导入 `editorPass` / `editorAssessment`，适合独立编辑代理产物
- 当 `review volume-self-template` 存在 merge 输入且 `--output` 指向目录时，当前默认导出 `*.draft.yaml`
- 不带 merge 输入时，模板仍会预填 root `scores/issues/closureAssessment`，用于减少从零手写；但默认 `conclusion.closureStatus` 仍是 `not_closed`

如果当前宿主上下文污染较重，可以先用可选文本 provider 生成独立编辑 fragment：

```powershell
python -m story_harness_cli review editor-draft --root <project-root> --volume-id <volume-id> --dry-run
python -m story_harness_cli review editor-draft --root <project-root> --volume-id <volume-id> --model <model> --output reviews/<volume-id>-editor-pass.json
```

`editor-draft --dry-run` 只刷新 / 读取 review packet 并输出 clean-room prompt 与 provider request，不调用网络。真实运行需要 `--api-key` 或 `TEXT_PROVIDER_API_KEY` / `OPENAI_API_KEY`，并只写 `editorPass` / `editorAssessment` fragment；它不会直接写入卷级自审真相层。

卷级自审现在默认包含两个视角：

1. `AI 自审`
2. `独立编辑审查`

若宿主支持 subagent / 新线程 / 无上下文代理，独立编辑审查应优先走无上下文代理；若不支持，至少要切到 fresh thread，或显式记录 `same_agent_fallback`。
这里的“无上下文”指的是：不继承当前创作线程、前轮自审结论和作者自我辩护；并不意味着编辑可以脱离项目规则、评分 rubric、模板和 review packet 自由发挥。

其中 `--input` 文件必须是 JSON-compatible YAML，并遵循下方结构。
模板中的 `待填写` 只是占位值，原样提交时 CLI 会拒绝写入。
此外，卷级自审输入不能所有维度都打 `0`；`closed` 必须写明 `delivered`，`not_closed` 必须写明 `missing`。
如果声明 `allowHumanReview=true`，则最低门槛维度也必须过线，且独立编辑审查必须已完成并给出 `pass`；若 `not_closed` 或存在 `0-2` 分弱项，至少要写出一项 `issues`。
当前还要求：若存在 `0-2` 分弱项，则该弱项必须能对齐到可核对的章节或证据锚点。优先写在该维度自己的 `scores[].chapterRefs / evidenceRefs` 上；若对应 `issues[]` 已带可核对锚点，也可满足最小要求。
当前 CLI 还会对低分维度做最小联动检查：若某个 `0-2` 分维度在 `issues`、`fixAction`、`repairSuggestions` 中完全没有被覆盖，会拒绝写入。
成功写入后，可通过 `status --volume-id <volume-id>`、`workflow status --volume-id <volume-id>` 或 `export --format review-packet --volume-id <volume-id>` 直接查看 `repairCoverage` 摘要，确认弱项是否真的进入了修复清单。若 `workflow status` 仍提示未覆盖弱项，说明当前 issues / repairSuggestions 还没有把低分项翻译成可执行修稿动作。当前 `workflow status/export --volume-id` 还会附带只读 `changeRequestDrafts`，并尽量带出章节定位与 evidence，可直接作为下一轮修稿任务草案使用。

当前 `review volume-self` 成功写入后，还会自动刷新 repo-native 的卷级审查包到 `reviews/<volume-id>-review-packet.md`。如果你只是想让仓库里的最新审查包跟随卷审结果同步，通常不需要再手工补跑一次 `export --format review-packet --volume-id ...`；命令输出里的 `reviewPacketRefreshed` / `reviewPacketFile` 会直接告诉你这次是否已刷新成功。

## 2. 先判闭环，再判优劣

自审第一问不是“这卷写得好不好”，而是：

1. 这卷是否完成了一个小故事单元
2. 若没有，是卡在起、承、转还是收
3. 若只有高潮没有收束，必须判为“未闭环”

## 3. 必答问题

### 3.1 闭环判断

1. 本卷主问题是什么。
2. 本卷是否交出阶段性答案、阶段性胜负或阶段性代价。
3. 本卷结尾是否让读者感觉“这一小段故事完成了”，而不只是“更紧张了”。

### 3.2 开篇与 onboarding

1. 读者是否已经理解最低必需设定集合。
2. 核心原创概念是否已在应有节点前被讲明到最低可读程度。
3. 当前压迫结构、主角被困原因和制度逻辑是否成立。

### 3.3 结构与承接

1. 章与章之间是否自然承接。
2. 是否存在“把细纲写成正文”的段落。
3. 是否存在持续加谜、回收不足、对象过多的问题。

这里的“承接”不是要求每章都在第一段机械回顾上一章。

当前更合理的判断口径是：

1. 上一章若留下明确状态变化、追踪压力、关系余波或活跃线程，本章前几段是否给出可感知的后果或因果桥。
2. 若本章选择冷开场，只要在前几段内自然回接前章负载，也不应机械判成承接失败。
3. 工具侧 `chapterHandoffSignals` 还会看前章 direction / beat / scene goal 中的关键语义锚点是否在本章开头复现，或是否出现“那句还没散 / 从某处脱身不过半个时辰”这类直接接续句式，避免把“用物件、地点、残局自然承接”误报成缺少承接。
4. 若上一章结尾短对白 / 短句被本章开头复现，或本章 4-10 字短对白由上一章结尾近距离关键片段合成，工具会视为高置信承接；这只用于结尾窗口，不代表全章正文任意重合都可放行。
5. 单个弱语义锚点只算辅助证据，不应单独抵消承接告警；需要高置信专名锚点、多个弱锚点组合，或直接接续句式支撑。
6. 真正的风险是：上一章明明留下了负载，本章开头却像直接换了一个执行场景，读者感受不到因果延续。

### 3.4 角色与冲突

1. 主角与核心角色是否保持连续人格。
2. 对手是否具备目标、利益和行为逻辑。
3. 冲突是否逐级升级，而不是同压迫重复换皮。

### 3.5 爽点与体验

1. 本卷主爽点是什么。
2. 是否至少兑现过一次体验承诺。
3. 情绪曲线是否长期只压不扬。

### 3.6 风格与可读性

1. 是否存在高频 AI 支架句习惯。
2. 是否存在 POV 越界、元信息泄漏、方案文档腔。
3. 开篇尤其前几章是否存在手机端段落负担过重的问题。

### 3.7 独立编辑审查

1. 独立编辑必须先给出自己的问题清单，再回看工具输出和 AI 自审结论。
2. 独立编辑评分与 AI 自审评分使用同一套 10 维 rubric，避免“各自一套标准”。
3. 每个主要问题都要回答三件事：
   - 为什么工具没有稳定检出。
   - 为什么 AI 自审没有注意到。
   - 下一步该补哪条规则、哪段提示、哪次复检。

## 4. 评分维度

每项建议使用 `0-5`：

- `0-1`: 明显失败
- `2`: 风险较高
- `3`: 基本可用
- `4`: 较稳
- `5`: 明显成立

评分表：

1. 卷级闭环
2. 开篇 onboarding
3. 世界与制度逻辑
4. 章间承接
5. 角色连续性
6. 对手塑造
7. 冲突升级
8. 爽点兑现
9. 伏笔与回收节奏
10. 风格与可读性

AI 自审和独立编辑都应使用上面这 10 个维度打分，不要再发明第二套“编辑专用分表”。

## 5. 缺陷归因

每个主要问题都必须归到以下类别之一：

1. `generation_miss`
   - 生成时就没有按规则写出来
2. `self_review_miss`
   - AI 写后复看过，但没有发现
3. `tooling_miss`
   - 现有 CLI / 导出 / 审查链没有稳定暴露该问题

若一项问题跨多个来源，可以主因 + 次因，但必须指出主因。

除主因外，当前还建议每个问题补齐：

1. `whyToolingMissed`
2. `whySelfReviewMissed`
3. `optimizationAction`
4. `detectedBy`
5. `ruleIds`
6. `verificationCommands`

## 6. 输出模板

```markdown
# 卷级 AI 自审

## 1. 结论
- 闭环状态: `closed` / `not_closed`
- 是否可进入人工审查: `yes` / `no`
- 本卷最强项:
- 本卷最大风险:

## 2. 评分
| 维度 | 分数 | 结论 |
|------|------|------|
| 卷级闭环 | 0-5 | ... |
| 开篇 onboarding | 0-5 | ... |
| 世界与制度逻辑 | 0-5 | ... |
| 章间承接 | 0-5 | ... |
| 角色连续性 | 0-5 | ... |
| 对手塑造 | 0-5 | ... |
| 冲突升级 | 0-5 | ... |
| 爽点兑现 | 0-5 | ... |
| 伏笔与回收节奏 | 0-5 | ... |
| 风格与可读性 | 0-5 | ... |

低分维度建议直接补：
- `chapterRefs`
- `evidenceRefs`

## 3. 主要问题
1. 问题:
   - 证据:
   - 影响:
   - 归因: `generation_miss` / `self_review_miss` / `tooling_miss`
   - 次因: `secondaryCauses`
   - 修正动作:
   - 为什么工具没报: `whyToolingMissed`
   - 为什么自审漏看: `whySelfReviewMissed`
   - 规则 / 流程优化: `optimizationAction`
   - 已由哪些命令 / 审查发现: `detectedBy`
   - 对应规则 id: `ruleIds`
   - 复检命令: `verificationCommands`
   - 可选章节定位: `chapterRefs`
   - 可选证据引用: `evidenceRefs`

## 4. 是否闭环
- 本卷主问题:
- 已交付内容:
- 未交付内容:
- 为什么仍未闭环 / 为什么已闭环:

## 5. 修后建议
1. 先修什么
2. 再复检什么
3. 哪些风险可带入人工审查

## 6. 独立编辑审查
- 是否完成独立编辑审查: `editorPass.completed`
- 审查角色: `editor`
- 审查模式: `independent_agent` / `human_editor` / `fresh_thread` / `same_agent_fallback`
- 上下文隔离方式: `no_context_proxy` / `fresh_thread` / `human_manual` / `same_thread` / `not_available`
- 独立编辑结论: `pass` / `revise` / `block`
- 独立编辑评分: 与上方相同 10 维
- 独立编辑评语:
- 独立编辑最主要问题:
- 独立编辑改进点:
```

## 7. 判定门槛

默认进入人工审查前，应至少满足：

1. `卷级闭环` 不低于 `3`
2. `章间承接` 不低于 `3`
3. `风格与可读性` 不低于 `3`
4. 没有未处理的高优先级 POV 越界、元信息泄漏、核心设定未解释问题
5. 独立编辑审查已完成，且 verdict 为 `pass`

若闭环状态仍为 `not_closed`，即使局部章评不错，也不应进入人工终审。

## 8. 与工具的关系

1. 该模板是当前卷级自审的 canonical 口径。
2. 若问题已经能定位到具体章节，建议在 `issues` 中补 `chapterRefs`；若已经有 review packet / 片段锚点，可再补 `evidenceRefs`。
3. 当前推荐的 `evidenceRefs` 写法：
   - `chapter-001#scene-1`
   - `chapter-001#paragraph-4`
   - `chapter-001#world-rule-onboarding`
   - `chapter-002#handoff-gap`
   - `review-packet:volume-001:chapter-001`
4. 当前 CLI 会对 `chapter-xxx#paragraph-n`、`chapter-xxx#scene-n` 和已知语义锚点做存在性校验；若章节、段落、scene 或语义信号不存在，会拒绝写入。
5. 当前首批支持的语义锚点包括：
   - `world-rule-onboarding`: 当前章确实存在 world onboarding 缺口
   - `handoff-gap`: 当前章已有持久化的章间承接弱信号
6. `chapter-xxx#scene-n` 当前还要求该场景已能映射到持久化 `scene review`，这样后续 workflow / review-packet 才能稳定跳转到对应场景。
7. 后续 CLI 若新增卷级 gate、卷级 review packet、评分导出，应优先兼容本模板字段。
8. 在工具正式落地前，人工和 adapter 都按这份模板组织卷级自审输出。
9. `review volume-self-template` 的 `_templateContext` 现在还会附带 `volumeStructureCheck`，可直接看到当前卷的轻量阶段映射、引入卷 onboarding 风险、伏笔债务和卷尾收束准备度，避免卷审时只看分数不看结构职责。
10. `_templateContext` 现在还会附带证据型上下文，优先包括：
   - `chapterReviewSummaries`
   - `lowSceneReviews`
   - `styleAggregate`
   - `styleFlaggedChapters`
   - `topRuleJudgements`
   - `contractAlignmentRisks`
   - `commercialAlignmentRisks`
   - `reviewPacketRefs`
   独立编辑应优先基于这些证据切片核对，而不是只看结构摘要。
11. 当前推荐的固定复检序列是：
   - `style check --root <root> --chapter-id <chapter-id>`
   - `review chapter --root <root> --chapter-id <chapter-id>`
   - `review scene --root <root> --chapter-id <chapter-id> --scene-index <n>`
   - `style report --root <root> --volume-id <volume-id>`
   - `review volume-self-template --root <root> --volume-id <volume-id>`
   - `workflow status --root <root> --volume-id <volume-id>`
12. 一个问题只有在至少一条命令给出稳定 `ruleId`、显式 issue，或可对齐的 `evidenceRef` 时，才应记为“工具已检出”；否则应写明为什么仍算 `tooling_miss`。
