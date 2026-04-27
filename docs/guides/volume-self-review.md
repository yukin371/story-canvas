# 卷级 AI 自审模板

> 最后更新: 2026-04-27
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

建议先用 `review volume-self-template` 生成骨架，再回填结论与评分。

其中 `--input` 文件必须是 JSON-compatible YAML，并遵循下方结构。
模板中的 `待填写` 只是占位值，原样提交时 CLI 会拒绝写入。
此外，卷级自审输入不能所有维度都打 `0`；`closed` 必须写明 `delivered`，`not_closed` 必须写明 `missing`。
如果声明 `allowHumanReview=true`，则最低门槛维度也必须过线；若 `not_closed` 或存在 `0-2` 分弱项，至少要写出一项 `issues`。
当前 CLI 还会对低分维度做最小联动检查：若某个 `0-2` 分维度在 `issues`、`fixAction`、`repairSuggestions` 中完全没有被覆盖，会拒绝写入。
成功写入后，可通过 `status --volume-id <volume-id>`、`workflow status --volume-id <volume-id>` 或 `export --format review-packet --volume-id <volume-id>` 直接查看 `repairCoverage` 摘要，确认弱项是否真的进入了修复清单。若 `workflow status` 仍提示未覆盖弱项，说明当前 issues / repairSuggestions 还没有把低分项翻译成可执行修稿动作。当前 `workflow status/export --volume-id` 还会附带只读 `changeRequestDrafts`，并尽量带出章节定位与 evidence，可直接作为下一轮修稿任务草案使用。

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

## 5. 缺陷归因

每个主要问题都必须归到以下类别之一：

1. `generation_miss`
   - 生成时就没有按规则写出来
2. `self_review_miss`
   - AI 写后复看过，但没有发现
3. `tooling_miss`
   - 现有 CLI / 导出 / 审查链没有稳定暴露该问题

若一项问题跨多个来源，可以主因 + 次因，但必须指出主因。

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

## 3. 主要问题
1. 问题:
   - 证据:
   - 影响:
   - 归因: `generation_miss` / `self_review_miss` / `tooling_miss`
   - 修正动作:
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
```

## 7. 判定门槛

默认进入人工审查前，应至少满足：

1. `卷级闭环` 不低于 `3`
2. `章间承接` 不低于 `3`
3. `风格与可读性` 不低于 `3`
4. 没有未处理的高优先级 POV 越界、元信息泄漏、核心设定未解释问题

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
