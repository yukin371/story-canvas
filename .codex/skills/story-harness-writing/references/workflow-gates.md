# Workflow Gates

这是 `story-harness-writing` 的 workflow 层。

它负责回答：

1. 什么时候必须跑命令
2. 哪些 gate 不能跳
3. 什么情况下不能宣称完成

## 角色分工

默认按两个角色执行：

1. `作者`
   - 负责写作、扩写、修稿、补结构
   - 负责消费 `startGuide`、chapter review、scene review、repair suggestions
2. `编辑`
   - 负责审查、评分、归因、放行判断
   - 不负责顺手继续写正文

不要把两个角色混成一个动作：

1. 作者不能在同一口气里既修稿又宣布“可进人工审查”
2. 编辑不能把“继续帮你写一版”当成审查结论
3. 卷级 `review volume-self` 默认属于编辑职责，不属于作者职责

## 单章闭环

### 写前

至少运行：

```powershell
uv run story-canvas status --root <project-dir> --chapter-id <chapter-id>
uv run story-canvas context refresh --root <project-dir> --chapter-id <chapter-id>
uv run story-canvas outline check --root <project-dir> --chapter-id <chapter-id>
```

先消费 `status.targetChapter.startGuide`，不要凭空脑补起步步骤。

起步规则：

1. 若 `startGuide.hasBodyParagraphs=false`，说明当前章仍是空白 stub；先补章节结构或每个计划 scene 的短骨架段落
2. 若 `missing-direction` / `missing-beats` 仍存在，优先执行 `structure apply` / `structure scaffold` 或显式 `outline beat-add`
3. 若只剩 `missing-scene-plans` 且 `hasBodyParagraphs=true`，才适合跑 `outline scene-detect`
4. 若 `outline check` 未通过，不要进入 `chapter analyze` / `chapter suggest`

并在动笔前确认：

1. 当前章的 `direction`、`beats`、`scenePlans`
2. 上一章的情绪落点、风险落点和未结悬念
3. 这一章准备回应什么旧问题、抬升什么新问题
4. 是否存在需要额外关注的实体、伏笔、世界规则

不要做的事：

1. 不要把 skill 自己想出来的步骤覆盖 `startGuide`
2. 不要对空白章节直接跑 `outline scene-detect`
3. 不要把占位稿、说明稿、空 PRD 当成真实写作材料

### 写后

至少运行：

```powershell
uv run story-canvas chapter analyze --root <project-dir> --chapter-id <chapter-id>
uv run story-canvas review chapter --root <project-dir> --chapter-id <chapter-id>
uv run story-canvas review scene --root <project-dir> --chapter-id <chapter-id>
```

必要时补充：

1. `style check`
2. `entity mention-check`
3. `foreshadow check`
4. `world check`

写后不要只看分数，也要人工复看：

1. 开头前 `20%` 是否真的能拉住人
2. 结尾钩子是否有效而不虚假
3. 对话是否只是信息传递
4. 扩写处是否在注水
5. 修正动作是否只是为了过规则

### 修后复检

改过正文后，至少重跑：

```powershell
uv run story-canvas chapter analyze --root <project-dir> --chapter-id <chapter-id>
uv run story-canvas review chapter --root <project-dir> --chapter-id <chapter-id>
```

若问题是 scene-local，再补 `review scene`。

若复检后剩下的是卷级结构、角色弧线或题材承诺问题，不要继续在单章里做机械缝补，应上提到卷级处理。

## 卷级闭环

卷级不能因为“单章都过了”就自动算完成。

至少运行：

```powershell
uv run story-canvas review preflight --root <project-dir> --volume-id <volume-id>
uv run story-canvas review volume-self-template --root <project-dir> --volume-id <volume-id>
uv run story-canvas review volume-self --root <project-dir> --volume-id <volume-id> --input <input>
uv run story-canvas workflow status --root <project-dir> --volume-id <volume-id>
uv run story-canvas export review-packet --root <project-dir> --volume-id <volume-id> --format markdown --output <path>
```

## 独立编辑审查

若宿主支持 subagent / fresh thread，且用户要求独立审查，应优先使用无上下文编辑代理。

这里的“无上下文”是：

1. 不继承当前创作线程、前轮自审结论、作者自我辩护
2. 仍然允许读取项目规则上下文：skill、`docs/guides/volume-self-review.md`、`review volume-self-template` 产物、review packet
3. 它是“无创作线程污染”，不是“无评分标准”

编辑代理应重点回答：

1. 工具检出了什么
2. 工具漏了什么
3. AI 自审漏了什么
4. 改进点是什么

编辑代理必须按统一评分标准工作：

1. 使用 `docs/guides/volume-self-review.md` 里的 10 维 rubric
2. 每维分数严格用 `0..5` 整数
3. 不要再发明“编辑专用另一套分表”
4. 若判定 `not_closed` 或存在 `0-2` 分弱项，必须落到 `issues`、`fixAction`、`chapterRefs/evidenceRefs`

不要把独立编辑 pass 降格成“再跑一遍同样命令然后复述结果”。

## 结束条件

以下任一成立，才能停：

1. 用户明确要求单次 pass
2. 风险已复检并满足当前目标
3. 剩余问题已明确记录为 accepted risk

否则，不应把这轮工作描述为闭环完成。

## 不要照搬旧纯 skill 的地方

以下做法不要原样继承：

1. 为了达字数线自动注水
2. 不看具体问题就多轮自动重写
3. 只靠章节字数或单一评分宣布完成
4. 把“自动化”放在“题材兑现、逻辑和承接”之前
