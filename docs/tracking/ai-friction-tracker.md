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
  - `repairCoverage` 现在会把独立编辑评分中的 `0-2` 分弱项合并到卷审弱项摘要，并保留 `rootWeakDimensionLabels` / `editorWeakDimensionLabels`，让 `workflow status --volume-id` 的下一步提示能直接看到多代理审查发现的卷级闭环、爽点兑现、伏笔节奏等弱项。
- 当前证据:
  - `Kant` 的 fresh-context editor pass
  - `projects/agent-volume-e2e-20260429/reviews/volume-001-self-review.yaml`
  - `projects/demo-climate-court-20260429/reviews/volume-001-editor-pass.json`
  - `tests.smoke.test_review_volume_self.test_review_volume_self_repair_coverage_includes_editor_weak_dimensions`
- 期望收口:
  - 增加导入 editor pass 的正式入口，而不是让 agent 手工抄写。
- 下次实施必查:
  - 子代理结果是否已能稳定序列化为 editor fragment，并直接被 CLI 吃掉，无需二次抄录。
  - workflow/status 是否直接暴露 editor 弱项；若仍必须手读 `editorAssessment.scores`，继续收口摘要层。

### AIF-003 状态产物需要手工刷新才能一致

- 状态: `mitigated`
- 首次记录: `2026-04-29`
- 最近核对: `2026-04-29`
- 现象:
  - mention hygiene 或 volume-self 状态改变后，`workflow status` 可能已更新，但 `review-packet` 仍需重新导出才能同步。
  - 章节闭环里，即使重新执行了 `chapter analyze` 与 `context refresh`，`workflow status/run` 仍可能继续读到旧的 `contextChapterContentHash`，把 `context_ready` 判成 `stale-context-refresh`。
- AI 负担:
  - agent 需要额外判断哪个文件是最新真相源，并主动重导出。
  - agent 还需要区分到底是自己漏跑命令，还是 workflow 摘要层没有同步到最新 context hash。
- 当前缓解:
  - `review volume-self` 成功写入后现在会自动刷新 `reviews/<volume-id>-review-packet.md`，并在命令输出里返回刷新结果与目标文件路径。
  - `entity mention-adopt` / `entity mention-apply` / `entity mention-tag-apply` / `world mention-adopt` 现在也会在章节属于某卷时自动刷新对应的卷级审查包。
- 当前证据:
  - `projects/agent-volume-e2e-20260429/reviews/volume-001-review-packet.md`
  - `python -m story_canvas export --root .\projects\agent-volume-e2e-20260429 --volume-id volume-001 --format review-packet --output ...`
  - `projects/xiaoshidi-bailan` 在 `2026-04-29` 的章节闭环中，`context refresh` 输出了最新 `chapterContentHash=eba73cf0b2`，但随后 `workflow status/run` 仍显示 `contextChapterContentHash=503e94a16e` 并阻塞在 `stale-context-refresh`。
  - 同项目在同日再次串行执行 `chapter analyze -> chapter suggest -> review apply -> projection apply -> context refresh -> review chapter -> review scene -> workflow status` 后，`context refresh` 已刷新到 `chapterContentHash=87cebf26d3`，但 `workflow status` 仍继续读取旧的 `contextChapterContentHash=503e94a16e`。
  - 同项目继续修稿并串行执行 `chapter analyze -> context refresh -> review chapter -> review scene -> workflow status` 后，`context refresh` 又刷新到 `chapterContentHash=58fdba9b86`，`workflow status` 仍卡在同一个旧值 `contextChapterContentHash=503e94a16e`。
  - 同项目进一步修稿并串行执行 `chapter analyze -> context refresh -> review scene -> workflow status` 后，`context refresh` 已刷新到 `chapterContentHash=a6106bcb14`，`workflow status` 仍保持 `contextChapterContentHash=503e94a16e` 不变。
- 期望收口:
  - mention hygiene 等其他卷级关键状态写入后，也能自动刷新 review packet，或在 status 输出中明确提示“导出已过期”。
  - `workflow status/run` 与 `context refresh` 应共享同一最新 context hash，不应在命令已成功返回后仍需要人工判断到底哪个视图可信。
- 下次实施必查:
  - 除当前已覆盖的卷审与 mention 修补入口之外，其他卷级状态修改后是否还需要手工补一次 `export review-packet`。
  - 章节闭环里重新跑完 `chapter analyze` + `context refresh` 后，`workflow status` 是否仍会误报 `stale-context-refresh`；若复现，应继续收口 workflow/context 同步链。

### AIF-004 mention / entity 修补链稳定性不足

- 状态: `mitigated`
- 首次记录: `2026-04-29`
- 最近核对: `2026-04-29`
- 现象:
  - `entity mention-tag-apply` 在实跑中出现过乱码/异常显示，后续还需要人工复核正文与 gate 状态。
- AI 负担:
  - 代理无法完全信任工具输出，必须再读正文和复跑 gate 做二次确认。
- 当前缓解:
  - `entity mention-tag-apply` / `entity mention-apply` 现在会在写入前校验修补后的 `@{...}` 标签语法；若结果包含非法标签会拒绝写入。
  - 两个命令输出新增 `postApplyCheck`，暴露剩余 mention action 摘要、坏标签数量和是否需要人工复核，减少 agent 修补后再手读正文。
- 当前证据:
  - `projects/agent-volume-e2e-20260429/chapters/chapter-001.md`
  - `projects/agent-volume-e2e-20260429/chapters/chapter-002.md`
  - `python -m story_canvas workflow status --root .\projects\agent-volume-e2e-20260429 --volume-id volume-001`
- 期望收口:
  - mention 修补后的正文、实体状态和 gate 结果应一次性保持一致，不再要求人工兜底核对。
- 下次实施必查:
  - mention 修补后 `postApplyCheck.valid` 是否足够替代人工读正文；若仍需复跑完整 gate，应转入 AIF-005 的命令编排收口。

### AIF-005 真实闭环命令编排过碎

- 状态: `mitigated`
- 首次记录: `2026-04-29`
- 最近核对: `2026-04-29`
- 现象:
  - 一次卷级闭环需要显式串行运行 `status/context/outline/review/workflow/export` 多条命令。
- AI 负担:
  - 调用方需要自己记忆顺序、刷新时机和失败后的回退位置。
- 当前缓解:
  - `workflow status/export --volume-id` 现在输出 `orchestrationPlan.suggestedCommands`，按当前卷级 gate 给出下一组可执行 CLI。
  - 该计划只作为派生命令队列，不自动执行，也不写入新的卷级 workflow 状态源。
- 当前证据:
  - `docs/plans/2026-04-29-agent-writing-workflow-e2e.md`
  - `projects/agent-volume-e2e-20260429/workflow.yaml`
- 期望收口:
  - 提供更高层的串行 orchestration 或更明确的下一步提示。
- 下次实施必查:
  - 真实实跑时 `orchestrationPlan.suggestedCommands` 是否足够覆盖下一步；若仍需要人工跨命令编排，再评估持久化 volume workflow run。

### AIF-006 多命令并行写入不适合批量建档

- 状态: `mitigated`
- 首次记录: `2026-04-29`
- 最近核对: `2026-04-29`
- 现象:
  - 新项目初始化时，尝试并行执行 `entity add` / `world add` 这类状态写入命令会触发 stale snapshot 防护。
  - 防护本身正确，但批量种子建档和多代理分工时缺少 repo-native 串行批处理入口。
  - 同一项目的章节闭环里，若并行执行 `review scene`、`chapter analyze`、`context refresh`、`review chapter` 这类都会写项目状态的命令，也会触发同样的 stale snapshot 防护。
- AI 负担:
  - agent 必须手动记住“读状态 -> 单条写入 -> 再读状态”的串行约束，不能把独立 seed 命令自然并行化。
  - agent 还需要区分哪些命令虽然看起来像“分析/评审”，但实际上会写 `story-reviews.yaml`、`detailed_outlines`、`project` 等状态，因此不能并行。
- 当前缓解:
  - 只靠调用方串行执行；暂无批处理命令。
- 当前证据:
  - `projects/demo-climate-court-20260429` 初始化阶段并行建档触发状态覆盖保护。
  - `projects/xiaoshidi-bailan` 章节闭环时，并行执行 `review scene` 与并行执行 `chapter analyze/context refresh/review chapter` 均触发 “项目状态已被其他命令更新，请重新执行当前命令以避免覆盖”。
- 期望收口:
  - 提供 `entity/world` seed batch 或 project bootstrap spec，一次性写入角色、势力、地点、物件和世界规则。
  - 明确标注会写状态的闭环命令，或提供 repo-native orchestration/queue，让章节闭环可安全串行调度，而不是靠调用方猜哪些命令不能并发。
- 下次实施必查:
  - 新项目 seed 阶段是否仍需 agent 逐条敲命令；如果是，应优先实现批量 bootstrap，而不是继续靠提示词约束。
  - 章节闭环阶段是否仍需调用方手工试错后才能知道哪些命令会写状态；如果是，应继续收口命令元数据或 orchestration 层。

### AIF-007 分析器会把非角色引用推入角色链路

- 状态: `mitigated`
- 首次记录: `2026-04-29`
- 最近核对: `2026-04-29`
- 现象:
  - `chapter analyze` 曾把已建档 `worldbook` 引用（势力、地点、物件、规则）注册为 `inferred::...` character。
  - 状态词检测曾把 `没有离开` 这类否定短语识别成角色状态变化。
  - 污染一旦进入 `projection.yaml`，`context refresh` 曾优先使用旧 projection scope，导致新 analysis 已修复但 context 仍显示旧污染。
- AI 负担:
  - agent 需要手动清理 `entities.yaml`，并复核 context/review 中的活跃实体和状态候选是否被污染。
- 当前缓解:
  - `analyzer.resolve_entities` 现在会对齐 `worldbook` 名称/别名，跳过已建档 worldbook 引用的 inferred character 注册。
  - `state_tags_for_paragraph` 增加直接否定窗口，避免 `没有/未/并未/... + 状态词` 生成状态标签。
  - `context_lens.refresh_context_lens` 在有当前章节 analysis 时，优先使用 analysis scene scope，并只采纳仍由本次 analysis 支撑的同章 snapshot。
- 当前证据:
  - `tests.smoke.test_chapter_auto_register.test_worldbook_mentions_are_not_auto_registered_as_characters`
  - `tests.smoke.test_keywords.test_state_keywords_ignore_direct_negation`
  - `tests.smoke.test_context_refresh.test_context_refresh_prefers_current_analysis_over_stale_projection_scope`
- 期望收口:
  - 分析器输出区分 character / faction / location / artifact / rule，不只是在 inferred character 入口跳过 worldbook。
- 下次实施必查:
  - 新项目 `chapter analyze` 后是否还需要手工删除 `inferred::` worldbook 条目；是否仍有否定句状态误报。

### AIF-008 评审题材信号过窄会误导作者迎合检测器

- 状态: `mitigated`
- 首次记录: `2026-04-29`
- 最近核对: `2026-04-29`
- 现象:
  - 职业法庭 / 程序悬疑章节中，禁令、异议、担保、限水损失、原始日志、接管链路、提交期限等真实张力没有被 `review chapter` 充分计分。
  - 一幕评审与商业对齐曾只把问号或通用 hook 词当作追读钩子，漏掉“陌生号码 / 别追某时间点 / 日志光标残影 / 接管链路异常”这类无问号但明确可追读的物证悬念。
  - 评分会诱导 agent 把文本改成通用“危险/威胁/追杀”词，而不是保持题材语域。
- AI 负担:
  - agent 需要判断是正文问题还是工具漏报，并可能手动解释“为什么低分不可信”。
- 当前缓解:
  - `review chapter` 的情节推进、人物压力、冲突张力已计入程序/证据/公共后果类关键词。
  - `review scene` 的伏笔与回收维度、章末商业 hook 对齐已计入悬念物证/异常信号，不再只依赖问号。
- 当前证据:
  - `tests.smoke.test_review_chapter.test_review_chapter_counts_procedural_legal_tension`
  - `tests.smoke.test_review_scene.test_review_scene_counts_mystery_hook_without_question_mark`
  - `projects/demo-climate-court-20260429/chapters/chapter-001.md`
- 期望收口:
  - 题材 overlay 或 profile 可配置 review signal，而不是继续在 core 里堆硬编码词表。
- 下次实施必查:
  - 非玄幻/悬疑/言情等新题材实跑时，评分是否仍要求作者改成通用冲突词；若复现，应推动 profile 化题材信号。

### AIF-009 卷级预检混入历史评审噪音

- 状态: `mitigated`
- 首次记录: `2026-04-29`
- 最近核对: `2026-04-29`
- 现象:
  - 同一章节/场景多次复评后，`review preflight --volume-id` 的 `reviewEvidence.lowSceneReviews/topRuleJudgements` 曾混入旧低分场景评审和旧规则命中。
  - 这会让已修复问题继续出现在卷级自审输入里。
- AI 负担:
  - agent 需要人工判断哪些 review evidence 是最新真相、哪些只是历史噪音。
- 当前缓解:
  - 卷级预检现在对 chapter review 按章节取最新，对 scene review 按章节 + scene 范围取最新，再聚合低分场景和规则命中。
- 当前证据:
  - `tests.smoke.test_review_preflight.test_review_preflight_uses_latest_scene_review_per_scope`
  - `projects/demo-climate-court-20260429` 的旧低分 scene review 不应再污染最新 preflight。
- 期望收口:
  - review 写入侧可考虑按 fingerprint/scope upsert 或显式标记 superseded，减少状态文件长期堆积历史噪音。
- 下次实施必查:
  - 多轮复评后，`reviewEvidence.lowSceneReviews` 是否只反映最新仍低分的场景；如果旧问题仍出现，应继续收口 review 写入策略。

### AIF-010 卷级预检未消费卷目标 / 章数承诺

- 状态: `active`
- 首次记录: `2026-04-29`
- 最近核对: `2026-04-29`
- 现象:
  - `projects/demo-climate-court-20260429` 的 `commercialPositioning.releaseCadence` 写明“测试用三章首卷”，`PRD.md` 也写明第一卷目标是完成临时禁令听证前的证据争夺并交出第一场程序胜负。
  - 但 `review preflight --volume-id` / `workflow status --volume-id` 的 `volumeStructureCheck.closure-readiness` 只看到当前卷 1/1 章已落正文，就判定具备进入卷级闭环判断的最低前提。
  - 独立编辑代理后续才指出“单章只是开场，不构成三章首卷的小故事闭环”。
- AI 负担:
  - agent 需要手动对照 `project.yaml` / `PRD.md` / `outline.yaml` 判断当前卷是不是缺章或缺交付，而不能只信 `volumeStructureCheck`。
- 当前缓解:
  - 独立编辑审查会在 `editorAssessment.scores` 中暴露 `volumeClosure=1`，且 `repairCoverage.editorWeakDimensionLabels` 会把“卷级闭环”带入 workflow 弱项摘要。
- 当前证据:
  - `projects/demo-climate-court-20260429/project.yaml`
  - `projects/demo-climate-court-20260429/PRD.md`
  - `projects/demo-climate-court-20260429/reviews/volume-001-editor-pass.json`
  - `projects/xiaoshidi-bailan/project.yaml`
  - `projects/xiaoshidi-bailan/outline.yaml`
  - `projects/xiaoshidi-bailan/reviews/volume-001-self-review.draft.yaml`
  - `2026-04-29` 实跑中，`projects/xiaoshidi-bailan` 的 `paceContract` 明确要求“前三章”完成异常机制展示、第一次外部挑衅、一次轻松打脸和至少两位师姐强记忆点，但 `review preflight --volume-id volume-001` / `workflow status --volume-id volume-001` 仍因当前 outline 只有 `chapter-001` 而把 `closure-readiness` 判成 `pass`。
- 期望收口:
  - `volumeStructureCheck` 应消费明确的卷目标、预期章数、`releaseCadence` / `PRD` 里的首卷交付要求；若当前卷章节数或交付节点不足，应在 preflight 阶段给出 `risk/missing`，而不是等独立编辑人工发现。
- 下次实施必查:
  - 新项目卷级预检是否仍把“当前 outline 里只有一章”误当作“短卷已满足结构前提”；若复现，应优先实现卷目标/章数承诺解析。

### AIF-011 本地 UI 审查工作区缺少核心卷审视图且项目切换会残留旧章节

- 状态: `active`
- 首次记录: `2026-04-29`
- 最近核对: `2026-04-29`
- 现象:
  - 审查工作区左侧“角色卡”当前只显示 `name/type` 和“设定图”按钮，没有角色详情阅读面板。
  - “资料”分组中的 `世界设定 / 卷结构 / 审查包` 仍是硬编码 `待接入`，无法在 UI 内核对卷级闭环所需信息。
  - 项目切换到另一个同样使用 `chapter-001` 的项目时，主面板会保留旧 `selectedChapter`，直到人工再点一次章节才刷新成正确正文、评分和字数。
- AI 负担:
  - agent / 人工审查无法只靠 UI 检查角色卡、世界真相层、卷结构和 review packet，必须退回 CLI/API/文件阅读。
  - 项目切换后的脏章节面板会制造错误审查上下文，导致 reviewer 以为当前项目内容、评分或字数异常。
- 当前缓解:
  - 本地 UI API 的 `ProjectSummary` 已暴露 `entities.profile/seed/aliases`、`worldbook.entries/stats`、`volumes[]` 与 `reviewPackets[]`，审查工作区可直接浏览角色卡、世界设定、卷结构和审查包预览。
  - `project-registry.json` 已增加工作台私有 `activeRoot`，`useWorkspace` 会在刷新后恢复上次打开项目；退出项目时清空该字段。
  - `ReviewWorkbenchView` 在 `selectedRoot` 变化时清空旧章节/角色/资料选择，并在章节列表刷新时用新项目的 chapter object 替换同名旧对象，避免 `chapter-001` 跨项目残留。
- 当前证据:
  - 本地 UI `http://127.0.0.1:43187/` 在 `2026-04-29` 选中 `projects/xiaoshidi-bailan` 时，角色列表可见，但“资料”区仍显示 `待接入`。
  - 同轮切换 `projects/小师弟只想摆烂` 与 `projects/xiaoshidi-bailan` 时，主面板一度继续显示旧 stub 项目的 `# 第一章`，手动再点 `chapter-001` 后才切回 `扫地也算修行 / 79 分 / 3171 字`。
  - `ui/src/components/workbench/ReviewWorkbenchPane.vue`
  - `ui/src/views/workbench/ReviewWorkbenchView.vue`
  - `ui/src/api/storyCanvas.ts`
  - `tests.smoke.test_illustration_command.test_story_canvas_ui_api_project_summary_includes_review_workbench_references`
  - `tests.smoke.test_illustration_command.test_story_canvas_ui_api_project_registry_persists_active_root`
- 期望收口:
  - review workbench 提供 repo-native 的角色详情、世界设定、卷结构和审查包浏览入口，而不是只保留占位字样。
  - 项目切换时，章节选择状态至少按 `project root + chapter id` 共同校验，避免同名 `chapter-001` 复用脏状态。
- 下次实施必查:
  - 在真实浏览器重启 API 服务后，切换两个都含 `chapter-001` 的项目时，主面板是否仍会残留旧章节；若复现，应继续收口 chapter selection identity。
  - 角色卡和资料视图是否足够支撑人工卷审；若仍需回到文件里读完整 worldbook/review packet，应补更完整的跳转或展开视图。

### AIF-012 章节/场景评审会对已兑现 beat 稳定误报 `outlineDeviation`

- 状态: `active`
- 首次记录: `2026-04-29`
- 最近核对: `2026-04-29`
- 现象:
  - `projects/xiaoshidi-bailan` 在补齐 `chapter-002`、`chapter-003` 正文并同步 `scenePlans` 后，`review chapter` 与 `review scene` 仍对两个章节的全部已规划 beat 持续报出 `outlineDeviation`。
  - 告警 payload 能列出正确的 beat summary，但 `evidence` 为空，也没有指出正文里到底缺了哪一段。
  - 同一章的 chapter review 和 scene review 会重复带出同样的三条 warning，放大“正文没写到”的假信号。
- AI 负担:
  - agent 必须手读正文和细纲，判断到底是正文真漏写，还是工具没有识别到已兑现的 beat。
  - 误报会直接污染章节闭环判断，逼着作者为迎合检测器去改写本来已经成立的承接、对抗和打脸段落。
- 当前缓解:
  - 无；目前只能人工核对正文与细纲，手动接受该 warning 为工具误报。
- 当前证据:
  - `projects/xiaoshidi-bailan/chapters/chapter-002.md`
  - `projects/xiaoshidi-bailan/chapters/chapter-003.md`
  - `projects/xiaoshidi-bailan/outline.yaml`
  - `projects/xiaoshidi-bailan/detailed_outlines.yaml`
  - `2026-04-29` 实跑中，`review chapter --chapter-id chapter-002` 与 `review scene --chapter-id chapter-002 --scene-index 1/2/3` 均对该章三条 beat 全量触发 `outlineDeviation`。
  - 同日 `review chapter --chapter-id chapter-003` 与 `review scene --chapter-id chapter-003 --scene-index 1/2/3` 继续对“霍飞当众再验 / 陆闲把杂役动作变成破局 / 霍飞吃瘪、师姐团确认底牌”三条已在正文明确兑现的 beat 全量触发 `outlineDeviation`。
- 期望收口:
  - beat/scene 匹配至少要给出正文证据片段、命中段落或未命中原因，避免“全量 planned = 未出现”的黑箱告警。
  - scene review 不应在整章已确认误报的前提下，对每个 scene 机械复制同一组 warning。
- 下次实施必查:
  - 真实多 scene 章节里，`outlineDeviation` 是否仍会对已兑现 beat 全量误报；若复现，应优先补 beat 命中证据或 scene-local 匹配测试，而不是要求作者改写正文。

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
