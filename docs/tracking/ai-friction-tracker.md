# AI 实施痛点长期追踪

> 最后更新: 2026-04-29
> 状态: 当前有效长期追踪入口
> 作用: 记录会持续增加 AI 实施负担的真实流程痛点，并要求后续实施前后固定回看与回写

## 1. 使用规则

### 1.1 何时必须检查

以下任务开工前，必须先读本文件的 `Active` 条目，并在边界摘要里写出本轮适用的痛点编号：

1. 真实写作流程实跑
2. workflow / review / export / entity / status / adapter 相关实现
3. 样例项目回归
4. 多代理参与的端到端测试

### 1.2 何时必须回写

以下情况完成后，必须回写本文件：

1. 发现新的 AI 手工兜底点
2. 某条痛点被缓解或彻底解决
3. 某个临时 `plan` / 项目级审查已经不再适合作为当前输入

### 1.3 状态定义

- `active`: 真实流程中仍稳定存在，后续实施前必须检查
- `mitigated`: 已有局部缓解，但仍会让 AI 手工兜底
- `resolved`: 已有 repo-native 收口路径，后续只需回归确认
- `historical-source`: 原始临时文档已降级，只保留回溯价值

### 1.4 归档规则

一条痛点满足以下任一条件后，可从 `Active` 迁到 `Resolved`：

1. 已有 repo-native 命令或稳定测试覆盖，且最近两次真实实施未再触发
2. 旧痛点已经被新 tracker 条目替代，不再需要把原始 `plan` 当活跃输入

迁移后，对应临时文档必须至少补一条历史状态说明，避免继续使用“当前缺口”口吻。

## 2. Active

### AIF-001 卷级自审输入手工负担过重

- 状态: `mitigated`
- 首次记录: `2026-04-29`
- 最近核对: `2026-04-29`
- 现象:
  - `review volume-self` 输入过长，`scores` 与 `editorAssessment.scores` 需要双写。
  - 低分项还要求手工补 `issues`、`repairSuggestions`、`evidenceRefs`、`verificationCommands`。
- AI 负担:
  - 即使 CLI 模板已生成，agent 仍需要大段手工拼装 JSON-compatible YAML。
- 当前缓解:
  - `review volume-self-template` 已支持 `--merge-input` / `--editor-input`，可把 author/editor 分片结构化合回模板骨架并导出 draft。
  - `review volume-self-template` 现在还会根据 `preflight`、`volumeStructureCheck`、chapter/scene review 与 style aggregate 启发式预填 root `scores/issues/closureAssessment`，把草稿从“空骨架”收敛成可直接审阅的起点。
  - `review volume-self` 已支持 `--merge-input` / `--editor-input`，减少最终写入前的整文件手改。
- 当前证据:
  - `projects/agent-volume-e2e-20260429/reviews/volume-001-self-review.yaml`
  - `python -m story_canvas review volume-self --root .\projects\agent-volume-e2e-20260429 --volume-id volume-001 --input ...`
- 期望收口:
  - 提供可直接提交或最少手改的 volume-self draft 生成能力。
- 下次实施必查:
  - 代理是否仍需大段重写 root `scores/issues/closureAssessment`，还是已经收敛为少量复核与局部改写。

### AIF-002 多代理编辑结论无法直接导入卷审

- 状态: `mitigated`
- 首次记录: `2026-04-29`
- 最近核对: `2026-04-29`
- 现象:
  - 独立 editor 子代理已给出 verdict、10 维分数和 top problems，但主线程仍需手动搬运到卷审输入文件。
- AI 负担:
  - 多代理参与并未转成 repo-native 结构化输入，只是先口头输出，再人工抄录。
- 当前缓解:
  - `review volume-self-template --editor-input`
  - `review volume-self --editor-input`
  - 两者都已能直接消费结构化 editor 产物，不再要求把 `editorPass` / `editorAssessment` 手工抄进主输入文件。
- 当前证据:
  - `Kant` 的 fresh-context editor pass
  - `projects/agent-volume-e2e-20260429/reviews/volume-001-self-review.yaml`
- 期望收口:
  - 增加导入 editor pass 的正式入口，而不是让 agent 手工抄写。
- 下次实施必查:
  - 子代理结果是否已能稳定序列化为 editor fragment，并直接被 CLI 吃掉，无需二次抄录。

### AIF-003 状态产物需要手工刷新才能一致

- 状态: `mitigated`
- 首次记录: `2026-04-29`
- 最近核对: `2026-04-29`
- 现象:
  - mention hygiene 或 volume-self 状态改变后，`workflow status` 可能已更新，但 `review-packet` 仍需重新导出才能同步。
- AI 负担:
  - agent 需要额外判断哪个文件是最新真相源，并主动重导出。
- 当前缓解:
  - `review volume-self` 成功写入后现在会自动刷新 `reviews/<volume-id>-review-packet.md`，并在命令输出里返回刷新结果与目标文件路径。
  - `entity mention-adopt` / `entity mention-apply` / `entity mention-tag-apply` / `world mention-adopt` 现在也会在章节属于某卷时自动刷新对应的卷级审查包。
- 当前证据:
  - `projects/agent-volume-e2e-20260429/reviews/volume-001-review-packet.md`
  - `python -m story_canvas export --root .\projects\agent-volume-e2e-20260429 --volume-id volume-001 --format review-packet --output ...`
- 期望收口:
  - mention hygiene 等其他卷级关键状态写入后，也能自动刷新 review packet，或在 status 输出中明确提示“导出已过期”。
- 下次实施必查:
  - 除当前已覆盖的卷审与 mention 修补入口之外，其他卷级状态修改后是否还需要手工补一次 `export review-packet`。

### AIF-004 mention / entity 修补链稳定性不足

- 状态: `active`
- 首次记录: `2026-04-29`
- 最近核对: `2026-04-29`
- 现象:
  - `entity mention-tag-apply` 在实跑中出现过乱码/异常显示，后续还需要人工复核正文与 gate 状态。
- AI 负担:
  - 代理无法完全信任工具输出，必须再读正文和复跑 gate 做二次确认。
- 当前证据:
  - `projects/agent-volume-e2e-20260429/chapters/chapter-001.md`
  - `projects/agent-volume-e2e-20260429/chapters/chapter-002.md`
  - `python -m story_canvas workflow status --root .\projects\agent-volume-e2e-20260429 --volume-id volume-001`
- 期望收口:
  - mention 修补后的正文、实体状态和 gate 结果应一次性保持一致，不再要求人工兜底核对。
- 下次实施必查:
  - mention 修补后是否仍需人工读正文确认工具没有写坏。

### AIF-005 真实闭环命令编排过碎

- 状态: `active`
- 首次记录: `2026-04-29`
- 最近核对: `2026-04-29`
- 现象:
  - 一次卷级闭环需要显式串行运行 `status/context/outline/review/workflow/export` 多条命令。
- AI 负担:
  - 调用方需要自己记忆顺序、刷新时机和失败后的回退位置。
- 当前证据:
  - `docs/plans/2026-04-29-agent-writing-workflow-e2e.md`
  - `projects/agent-volume-e2e-20260429/workflow.yaml`
- 期望收口:
  - 提供更高层的串行 orchestration 或更明确的下一步提示。
- 下次实施必查:
  - 真实实跑时是否仍频繁停下来判断“下一条命令该跑什么”。

## 3. Resolved

### AIF-R001 缺少显式 workflow 命令组与 `workflow.yaml`

- 状态: `resolved`
- 原始来源:
  - `docs/plans/2026-04-25-workflow-gap-analysis.md`
- 当前证据:
  - 仓库已存在 `workflow status/run/advance/reset/export`
  - 真实项目已写入 `projects/*/workflow.yaml`
- 归档动作:
  - 原始文档降级为历史资料，不再作为活跃缺口入口。

### AIF-R002 缺少卷级审查包导出

- 状态: `resolved`
- 原始来源:
  - `docs/plans/2026-04-26-workflow-gap-notes.md`
- 当前证据:
  - `export --format review-packet --volume-id`
  - `projects/agent-volume-e2e-20260429/reviews/volume-001-review-packet.md`
- 归档动作:
  - 原始缺口保留回溯价值，但当前活跃状态已转移到本文件。

### AIF-R003 缺少卷级 AI 自审持久化与人工审查 gate

- 状态: `resolved`
- 原始来源:
  - `docs/plans/2026-04-25-workflow-gap-analysis.md`
  - `docs/plans/2026-04-26-workflow-gap-notes.md`
- 当前证据:
  - `review volume-self-template`
  - `review volume-self`
  - `workflow status --volume-id`
- 归档动作:
  - 旧“缺少卷级 gate”的临时文档降级为历史资料；后续只跟踪新的 AI 负担点。

## 4. Historical Sources Downgraded This Round

- `docs/plans/2026-04-25-workflow-gap-analysis.md`
  - 类型: `historical-source`
  - 原因: 显式 workflow 命令组和状态文件已落地。
- `docs/plans/2026-04-26-workflow-gap-notes.md`
  - 类型: `historical-source`
  - 原因: 其中已解决项已归档，未解决项转入本文件长期追踪。
- `docs/plans/2026-04-26-writing-review-gap-log.md`
  - 类型: `historical-source`
  - 原因: 不再继续把单份 gap log 当活跃入口；后续活跃痛点应集中记录在本文件。
- `docs/plans/2026-04-26-writing-gap-remediation-plan.md`
  - 类型: `historical-source`
  - 原因: 它是阶段性实施计划，不应继续承担长期缺口入口职责。

## 5. 下轮实施检查清单

每次真实实施前，至少回答：

1. 本轮适用哪些 `AIF-*` 条目？
2. 有没有哪条痛点已经不再复现，可以迁到 `Resolved`？
3. 有没有新的手工兜底动作，应新增条目？
4. 本轮引用的旧 `plan` 是否仍只是背景材料，还是被误当成活跃规则源？
