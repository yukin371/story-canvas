# Commands 模块说明

> 最后更新: 2026-04-30
> 状态: 当前有效模块文档

## 1. 模块职责

- 定义所有 CLI 子命令的参数解析和处理逻辑
- 每个命令一个文件，通过 `register_xxx_commands(subparsers)` 注册
- 命令函数 `command_xxx_action(args) -> int` 负责串联 protocol → service → output

## 2. Owns

- argparse 子命令注册（`__init__.py` 导出 + `cli.py` 注册）
- 命令参数定义（--root, --chapter-id, --output 等）
- JSON 输出格式化（`print(json.dumps(...))`）
- 文件 I/O 时机控制（何时 save_state）
- workflow 命令编排（如 `review apply`、`review chapter`、`review scene` 的不同评审路径，以及 `review scene --list-scenes` 的场景枚举）
- `review preflight` 现负责章节 / 卷级只读预检聚合：把 mention hygiene、伏笔到窗 / 逾期、世界 onboarding / 势力与战力风险收敛成一个 AI 自审入口，减少在卷级闭环前来回手拼多个命令输出
- `review preflight` 当前还会带出顶层 `projectAdvisories`；首个 advisory 为缺少 `PRD.md`，让 AI 在常规预检入口就能看到项目立项文档缺口
- `review preflight --volume-id` 当前还会附带 `volumeStructureCheck`，用轻量阶段映射和检查项暴露卷级结构明示度、引入卷 onboarding、伏笔债务和卷尾收束准备度，先服务 AI 自审与人工审查
- `review preflight --volume-id` 现在还会附带 `volumeClosureContract`；首批会消费 `commercialPositioning.releaseCadence` 中显式的“X 章首卷”承诺，并把 `PRD.md` 的 `卷目标` 带进 `closure-readiness` 证据，避免把 1/1 章误判成卷级闭环前提已满足
- `review preflight --volume-id` 聚合 review evidence 时，chapter review 按章节取最新，scene review 按章节 + scene 范围取最新，避免历史低分评审继续污染卷级自审输入
- `review volume-self-template` 现负责 repo-native 的卷级 AI 自审模板生成：基于卷级 `review preflight` 输出模板骨架、当前卷风险摘要、逐章信号、已持久化 chapter/scene review 摘要、卷级 style 风险摘要、独立编辑审查要求和建议修补方向，减少 AI/作者手拼输入文件
- `review volume-self-template` 当前还会根据 `preflight`、`volumeStructureCheck`、chapter/scene review 与 style aggregate 启发式预填 root `scores/issues/closureAssessment`，把模板从“空骨架”收敛成可直接审阅的 draft 起点，但默认仍保持 `not_closed`
- `review volume-self-template` 现支持 `--merge-input` 与 `--editor-input`：可把 author/editor 分片产物结构化 merge 回模板骨架，目录输出时若存在 merge 输入会自动落为 `.draft.yaml`，减少 agent 手工改整份 YAML
- `review volume-self-template` 当前还会把 `projectAdvisories` 写入模板 `_templateContext`，让 AI 自审时同步看到项目级立项缺口
- `review volume-self` 现负责 repo-native 的卷级 AI 自审结果写入：从外部结构化输入读取卷级闭环结论、评分、归因、独立编辑审查结果和修正建议，落盘到 `reviews/story-reviews.yaml`，避免继续手改该状态文件
- `review volume-self` 成功写入后当前还会自动刷新 repo-native 的卷级审查包 `reviews/<volume-id>-review-packet.md`，减少 agent 另跑一次 `export review-packet`
- `review volume-self` 现支持 `--merge-input` 与 `--editor-input`：在最终校验和持久化前，先把局部 author/editor 产物结构化合并到基础输入，减少多代理场景下的手工抄写
- `review editor-draft` 现负责可选文本 AI provider 的独立编辑 fragment 生成：dry-run 只输出 clean-room prompt 与 provider request，真实运行写入 `reviews/<volume-id>-editor-pass.json`，供 `review volume-self-template --editor-input` 或 `review volume-self --editor-input` 消费；该命令不直接写卷级自审真相层
- `review volume-self` 当前还会显式拒绝模板占位值（如 `待填写`），避免把未完成的自审草稿写入真相层
- `review volume-self` 当前还会做最小健康检查：不接受所有维度都为 `0` 的空白评分；`closed` 必须写出 `delivered`，`not_closed` 必须写出 `missing`
- `review volume-self` 当前还会做最小一致性检查：`allowHumanReview=true` 时最低门槛维度必须过线，且独立编辑审查必须完成并给出放行 verdict；`not_closed` 或存在 `0-2` 分弱项时至少要写出一项 `issues`
- `review volume-self` 当前还会校验低分维度的最小证据锚点：`scores[].chapterRefs/evidenceRefs` 若为空，则至少要在带 ref 的 `issues[]` 中能追到对应弱项，避免只给低分不留可核对证据
- `review volume-self` 当前还会对 `0-2` 分弱项做最小联动检查：若对应问题或修复动作里完全没提到该弱项方向，会拒绝写入，避免“分数和问题清单各说各话”
- `review volume-self` 当前还会基于当前卷章节正文与 `scenePlans` 校验 `issues.chapterRefs/evidenceRefs`：至少会验证 `chapter-xxx#paragraph-n` 与 `chapter-xxx#scene-n` 是否真的存在，减少写入空锚点
- `review volume-self` 当前还会在 command 层额外构建章节级 `semanticAnchors`，首批支持 `chapter-xxx#world-rule-onboarding` 与 `chapter-xxx#handoff-gap`，只有当前卷里真实存在对应 world onboarding / chapter handoff 信号时才允许写入
- `review volume-self` 对 `chapter-xxx#scene-n` 的校验当前还要求该场景已能映射到持久化 `sceneReviews`，避免 scene 锚点只能指向 outline 结构却跳不到 review-packet 的对应场景
- `chapter create` 的 command-side 编排：原子化创建章节正文 stub、插入 outline / volume 章节列表、回填 direction / beats / scenePlans 种子，并按需推进 `project.activeChapterId`
- `projection apply` 的 command-side 编排：加载 analysis、读取章节正文并补跑设定一致性抽取，把非冲突高置信新设定交给 service 入账
- `outline scene-add` / `outline scene-list` / `outline scene-detect` / `outline scene-update` / `outline scene-remove` / `outline scene-sync` 这类轻量结构维护命令
- `outline check` 这类“写作前门禁”命令，以及 `chapter suggest` 的 outline-first workflow gate
  默认门禁口径为 `project.positioning` / `project.storyContract` + chapter `direction` + `beats` + `scenePlans`
- `outline check` 当前在 chapter scope 下还会返回 `startGuide`，把缺失的 direction / beats / scenePlans 翻成可执行命令建议，而不只停留在抽象 `nextActions`
- `outline check` 与 `chapter suggest` 当前还会在顶层输出 `projectAdvisories`；不仅会提示缺少 `PRD.md`，也会提示 `PRD.md` 仍停留在 bootstrap/TBD 占位状态，让 AI 在真正开写/续写前就能看到项目级立项文档缺口，同时保持非阻塞
- `brainstorm outline` 与 `structure apply/show/check/map/scaffold` 当前也会在顶层输出 `projectAdvisories`；不仅会提示缺少 `PRD.md`，也会提示 `PRD.md` 仍未补齐卷目标/读者钩子/章节承接点等占位项，把项目级立项缺口继续前推到正式起稿前的灵感/结构整理入口
- 项目初始化参数装配（如 `init` 写入 positioning / storyContract / emotionalContract / storyTemplate / commercialPositioning，并落盘 `worldbook` / `foreshadowing` 默认文件）；当前还会默认生成根目录 `PRD.md`，把立项/卷职责文档作为真实项目初始化产物显式留下
- `init` 当前默认只创建空白章节 stub，不再把结构说明文案写进正文；命令输出会附带 `startGuide/suggestedCommands`，直接提示 AI 下一步该跑什么
- `init` 当前支持 `--volume-id/--volume-title/--volume-theme`，可直接把首章放进首卷，避免“有卷级审查命令但从零起项目不能建卷”的断链
- `init` 当前还支持通过 `--volume-goal` / `--reader-hook` / `--suppression-source` / `--onboarding-focus` / `--chapter-handoff` / `--chapter-delivery` 直接回填 PRD 启动焦点，减少后续 agent/UI 继续手改 `PRD.md`
- `context refresh` 的 command-side 编排：加载 analysis 日志，刷新并持久化包含情绪契约、题材模板、世界约束、线索和伏笔切片的写作上下文；当前还会输出 `chapterHandoff`，并记录当前章节正文内容指纹供 workflow 判断 context 是否过期
- `context refresh/show` 当前还会在命令输出层附带 `projectAdvisories`；不仅会提示缺少 `PRD.md`，也会提示 `PRD.md` 仍停留在模板占位状态，让 AI 在真正拿写作上下文时就能看到项目级立项缺口，同时不污染持久化 `context-lens.yaml`
- doctor 类命令中的项目元数据校验编排
- doctor 现在还会检查项目根目录是否存在 `PRD.md`，在缺失时给出只读 warning，提醒项目仍缺正式立项/卷职责文档入口
- doctor 现在还会识别 `PRD.md` 是否仍停留在 bootstrap/TBD 占位状态；若卷目标、读者钩子、本章承接点/交付点等仍未补齐，会给出 `project-prd-incomplete` warning
- doctor 现在还负责校验可选项目配置如 `style-profiles.yaml`、`review-rules.yaml` 的基本结构，以及 `storyTemplate` 驱动的 `worldbook` / 伏笔账本 / 角色状态追踪基础约束
- doctor 现在还会扫描全项目章节中的 `@{实体}` 包裹引用，并检查是否已在 `entities/worldbook` 中建档
- doctor 现在还会扫描全项目章节中的“已建档但未包裹” plain mention，并提示哪些引用仍应回到 `entity mention-plan/mention-apply` 或显式 adopt 闭环
- doctor 现在还会检查章节中的坏标签语法，例如未闭合 `@{`、空标签 `@{}`、以及把整句对白/叙述塞进 `@{...}` 的非法实体标签
- doctor 现在还会校验 `illustrations.yaml` 中的主图/多图资产引用、缺失文件和孤儿资产
- `entity add` / `entity state-update` / `entity mention-adopt` / `entity mention-plan` / `entity mention-apply` / `entity mention-tag-apply` 现负责 repo-native 的实体建档、状态维护与确定性正文修正，覆盖 `seed/profile/currentState/state/changeLog` 的最小可用写入，并支持把章节中的缺失 mention 显式采纳进 `entities`、把已知 plain mention 批量包成规范 `@{}`，减少 AI 直接改 `entities.yaml` 与章节正文
- `entity mention-adopt` / `entity mention-apply` / `entity mention-tag-apply` 当前在所属章节已挂到某卷时，还会自动刷新 `reviews/<volume-id>-review-packet.md`，减少 mention hygiene 修补后再手工补导出
- `entity mention-apply` / `entity mention-tag-apply` 当前会在写入前校验修补后的 `@{...}` 标签语法，并在输出里返回 `postApplyCheck`，让调用方直接看到剩余 mention action、坏标签数量和是否仍需人工复核
- `entity mention-check` 现负责章节级实体 mention 审查编排：输出已包裹已建档、已包裹未建档、已建档但未包裹、引号内降级忽略，以及最小相关实体/势力/物品上下文
- `entity mention-plan` 现负责把章节级 mention 审查收敛成结构化 action plan：区分“可确定性包裹的已知引用”和“仍需显式建档的缺失引用”，避免 AI 直接根据原文手改正文或 yaml
- `entity mention-plan` 现支持 `--volume-id` 做卷级只读预览：逐章列出待包裹 / 待建档 action，便于卷级自审或人工审查前先看整卷闭环缺口
- `entity mention-apply` 现只允许显式应用 `mention-plan` 中的确定性 tag action；遇到缺失建档 action 仍必须改走 `entity mention-adopt` 或 `world mention-adopt`
- `foreshadow check` 现负责伏笔到窗/逾期/未排期检查编排：兼容旧版 `plannedPayoffChapter` 与新版 `payoffPlan.window`，输出当前章的 due / overdue / unresolved-without-schedule 视图
- `world list` / `world add` / `world mention-adopt` / `world progression-add` / `world progression-stage-add` 现负责 repo-native 的 worldbook 浏览与显式写入，覆盖 `worldRules`、`factions`、`locations`、`artifacts`、`mysteries` 与最小 `powerProgressions` 维护，并支持把章节中的缺失 mention 显式采纳进 `worldbook`，减少 AI 直接改 `worldbook.yaml`
- `world mention-adopt` 当前在所属章节已挂到某卷时，也会自动刷新 `reviews/<volume-id>-review-packet.md`，避免 world mention 建档后卷级审查包继续过期
- `world check` 现负责核心概念 onboarding 与世界尺度审查编排：输出 `storyTemplate.modulePolicy` 下的世界模块缺口、当前章/当前卷涉及的势力/地点/物品/谜团上下文、早期世界规则缺失提示、势力建档薄弱项，以及复用一致性引擎的高风险任务/战力突破冲突信号
- `style check` / `style constraints` / `style report` / `style repair` 这组风格治理命令，以及 optional scorer 的 command-side 装配
- `style check` / `style constraints` / `style report` / `style repair` 这组风格治理命令，以及 `style-profiles.yaml` 中 pattern / 术语词典 / 白名单 / 题材语域词表的 command-side 装配；未显式传 `--profile` 时会按项目定位自动选 profile；当前还会装配 `review-rules.yaml` 的 resolved profile，并把章节/卷/scene scope 透传给服务层规则检测；章节输出现会直接暴露中文高频 AI 句式簇、`paragraphReadability` 与 `clusteredAIPhrasing` 等新风格信号
- `style check` / `consistency check` / `review chapter` / `review scene` 现已开始对外暴露统一规则 judgement 结果，作为后续统一规则引擎协议的 Phase 1 兼容输出；其中 chapter review 还会暴露 `chapterHandoffSignals`，并由命令层读取上一章结尾窗口后以纯文本输入传给服务层，避免 service 侧引入文件 I/O
- `status` 现负责 repo-native 状态浏览编排：默认聚合项目概览、当前卷/章、context lens、最近 chapter / scene review、style 摘要、persisted consistency check、章节级 mention hygiene 摘要与 workflow gate；传 `--volume-id` 时则切到卷级视角，输出卷摘要、最新卷级 AI 自审摘要与卷级 gate，减少真实写作时直接翻 `project.yaml` / `outline.yaml` / `story-reviews.yaml` / `context-lens.yaml`
- `status` 当前还会在 `project.projectAdvisories` 与 `workflow.projectAdvisories` 暴露项目级只读提示；既会提示缺少 `PRD.md`，也会提示 `PRD.md` 是否仍停留在 bootstrap/TBD 占位状态，便于 UI / agent 在总览页直接看到立项文档缺口；同时 `project.reviewRuleConfig` 会暴露 `review-rules.yaml` 的 active/resolved profile 与豁免数量
- `status.targetChapter` 当前还会带出 `startGuide`：显式说明当前章是否已有正文段落、还缺哪些 outline 信号，以及建议先跑哪些结构/scene 命令
- `status` 的卷级 AI 自审摘要当前还会直接暴露 `repairCoverage` 紧凑信号，说明低分弱项是否已经被 `issues/repairSuggestions` 覆盖，便于 UI 或人工审查看到“还有哪些弱项根本没进入修复清单”
- `status` / `workflow status --volume-id` 当前展示的卷级弱项会合并 root 自审与独立编辑评分，并可通过原始 `repairCoverage.rootWeakDimensionLabels` / `editorWeakDimensionLabels` 追溯来源，减少多代理审查后再手读 editor 分表
- `outline scene-sync` 现负责显式 `scenePlans` 的边界校验与安全回填：默认输出校验报告和建议，显式传 `--apply` 才会回写；当前优先覆盖尾部越界收正与“scene 数量一致时按 heuristic 重算边界”
- `entity add` / `entity state-update` / `entity mention-adopt` / `entity mention-apply` / `entity mention-tag-apply` 只在显式子命令下写入实体卡、变化日志与章节正文，不会按正文自动建档或自动改状态
- `entity mention-check` 默认只做只读检查，不会自动补 `@{}` 或自动建档；当前主要服务写后自查和后续审查注入，而不是替代人工命名判断
- `entity mention-plan` 默认只做只读计划预览；即使输出了缺失引用 action，也不会隐式补档
- `entity mention-plan --volume-id` 只做卷级预览，不会跨章自动 apply；真正修正仍必须逐章调用 `mention-apply` 或 adopt 命令
- `foreshadow check` 默认只做只读聚合，不会自动 resolve 或自动改 payoff window；当前主要服务写前提醒、写后自查和 review 前预检
- `world add` / `world mention-adopt` / `world progression-add` / `world progression-stage-add` 只在显式子命令下写入 worldbook，不会按正文自动补档
- `world check` 默认只做只读聚合，不会自动补 worldbook、不会自动改 faction/powerProgressions；当前主要服务首卷 onboarding 审查、世界尺度核对与卷内世界名词回顾
- `export` 现会在导出链路中额外剥离“当前章正文末尾误混入下一章标题”的边界污染，但不会回写原始章节文件
- `export` 现支持 `review-packet`，把章节目标、scenePlans、最新 chapter / scene review、风险与优先动作、正文聚合成单个 Markdown 审查包，供不依赖 MCP 的人工审查使用
- `export review-packet` 当前还会在审查包头部带出项目级 `Project Advisories`；既会提示缺少 `PRD.md`，也会提示 `PRD.md` 是否仍停留在模板占位状态，让人工审查时也能直接看到立项文档缺口
- `export review-packet` 现还会带出章节/卷级 mention hygiene 摘要，明确哪些引用仍待补 `@{}`、哪些包裹引用仍待建档，方便人工审查时直接定位工具闭环缺口
- `export` 现支持 `--volume-id`，可按卷导出 `txt/json/markdown`，并支持卷级 `review-packet`；目录输出时默认使用卷标题命名，如 `第一卷.md`、`第一卷-review-packet.md`
- 卷级 `export review-packet --volume-id` 当前还会带出卷级自审的 `repairCoverage` 摘要，明确弱项覆盖状态与未覆盖弱项，减少人工审查前再反查原始 YAML
- `illustration prompt` / `illustration generate` / `illustration batch-export` / `illustration batch-record` / `illustration export` / `illustration list` / `illustration config` / `illustration pack-migrate` / `illustration pack-export` 这组插图命令，负责编排 prompt pack/template/modifier/commercialMode 解析、文生图/图生图/重绘 provider 请求、batch manifest 导出/回录、临时资产导出、项目级 prompt pack 迁移，以及 `illustrations.yaml` 配置读写；当前 `chapter / entity / temporary` 三类目标都支持首批 use-case 模板矩阵
- `illustration prompt` / `illustration generate` 当前还负责最小 batch task 编排：支持 `batch.count` 的同模板重复生成，并把 `batch.count / variantStrategy` 写入 dry-run 输出与生成历史，避免 UI 或脚本自行发明平行批量协议；`--use-case` 不再只服务临时图，chapter/entity 也可显式指定 `character-sheet`、`cover-poster`、`duel-scene`、`manga-page` 等用途；同时支持 `--text-design-mode/--title-text/--subtitle-text/--body-text/--font-style-hint` 这组正交文字设计参数
- `illustration batch-export` 当前是批量插画的 canonical 导出入口：把 project state + prompt pack 展开成 manifest，并显式区分 `webui-manual` / `external-agent` 两种交付模式
- `illustration pack-migrate` 当前是项目级 prompt pack 资源迁移的 canonical 入口：只处理 `prompts/illustration-packs/*.yaml`，把 legacy 模板重写成当前 canonical 模板格式，不回写历史 `generated[].promptSnapshot`
- `illustration pack-export` 当前是 builtin/default pack 项目化的 canonical 入口：把当前选中的 builtin 或显式指定 pack 克隆到 `prompts/illustration-packs/*.yaml`，供后续本地编辑、迁移和重新设为默认 pack，避免 UI / agent 直接手抄系统模板形成平行真相源
- `illustration batch-record` 当前只负责把 manifest 约定路径下的现存图片资产回录到 `illustrations.yaml`；WebUI 或外部 agent 不得直接修改状态文件
- `illustration export` 当前负责把已生成或已回录的资产导出到目标目录，主要服务临时暂存图的转存，而不是重新生成
- 本地 UI API 若需要触发插画 dry-run 或真实 generate，应复用 `commands/illustration.py` 的命令侧 helper；插画请求组装、provider request 构造和落盘写入仍由命令层 owner
- `workflow status` / `workflow run` / `workflow advance` / `workflow reset` / `workflow export` 这组 workflow 状态机入口，负责把 protocol + service 的推断结果、gate 决策和快照导出编排到 `workflow.yaml`
- `workflow status/export` 现支持 `--volume-id` 的卷级 gate 视图：先基于 `review preflight` 聚合结果判断工具侧阻塞项，再结合最新 `review volume-self` 结果显式判断“是否允许进入人工审查”
- `workflow status/export --volume-id` 当前会输出派生的 `orchestrationPlan.suggestedCommands`，把当前卷级 gate 翻成下一组可执行 CLI，但不自动执行、不写入新的 volume workflow 状态源
- `workflow status/export --volume-id` 当前还会带出卷级自审的 `repairCoverage` 紧凑摘要，便于 workflow 面板直接区分“已有自审”与“弱项是否真的进入修复动作”
- `workflow status/export --volume-id` 当前还会把 `review preflight` 里的 `volumeStructureCheck` 直接抬到顶层输出，便于 UI / agent 不必先反查嵌套 preflight 才能消费卷级结构检查摘要
- `workflow status/export --volume-id` 现在还会把 `volumeClosureContract` 直接抬到顶层输出；当 `closure-readiness` 因承诺章数未满足而转成 `risk/missing` 时，会直接进入 `volume_tooling_gate` 的 blocking rules，而不再只停留在结构草案
- 当卷级自审里存在 `repairCoverage.uncoveredWeakDimensionLabels` 时，`workflow status/export --volume-id` 当前还会把这些未覆盖弱项直接翻成 gate 阻塞原因与 `nextActions`，减少人工自己解读 raw review
- `workflow status/export --volume-id` 当前还会额外输出只读 `changeRequestDrafts`，把当前卷级 gate 的阻塞项收敛成带章节定位与 evidence 的 change-request 风格草案；若尚未进入卷级自审，也会附带 `volumeStructureCheck` 派生的结构修补草案，便于 UI 或 agent 直接组织修稿闭环
- 当卷级自审的 `issues` 已带 `chapterRefs/evidenceRefs` 时，`workflow status/export --volume-id` 当前会优先复用这些结构化定位，而不是只靠 preflight 启发式推断
- `workflow status/export` 当前还会统一输出顶层 `projectAdvisories`；既会提示缺少 `PRD.md`，也会提示 `PRD.md` 是否仍停留在模板占位状态，用于提醒项目尚未补齐立项/卷职责文档入口，但不会改变 gate blocking 结果
- `workflow status` 当前在 chapter scope 下还会带出 `startGuide`；当起步门禁未齐备时返回 bootstrap 命令建议，门禁齐备后则切换到 analyze / context / review 闭环建议，避免在后续阶段继续误报“缺 direction / beats / scenePlans”；`startGuide` 只消费章节起步三类 outline 缺口，不混入当前 gate 的 context/review 阻塞项
- `doctor` 与 `workflow` 现也开始对外暴露统一规则语义：`doctor.judgements`、workflow gate 下的 `ruleJudgements/gateDecision`，用于把结构校验和流程门禁逐步收口到同一规则协议

## 3. Must Not Own

- 纯计算逻辑（委托 services/）
- 状态管理规则（委托 protocol/）
- 文本处理算法（委托 utils/）

## 4. 关键入口

- `commands/__init__.py`: 所有 `register_*_commands` 的导出汇总
- `cli.py`: `build_parser()` 构建完整 argparse 树
- 每个子模块: `register_xxx_commands` + `command_xxx_*` 函数

## 5. 关键依赖

- 依赖 `protocol/`: `ensure_project_root`, `load_project_state`, `save_state`
- 依赖 `services/`: 各业务逻辑服务
- 依赖 `utils/`: `now_iso`, `stable_hash`, 文本工具

## 6. 不变量

- 每个命令函数必须 `return 0` 表示成功
- 致命错误必须 `raise SystemExit("中文消息")`
- 输出统一使用 `print(json.dumps(result, ensure_ascii=False, indent=2))`
- 在兼容旧字段的前提下，新增输出字段应优先挂在统一语义层（如 `judgements`、`ruleJudgements`），而不是继续为每个命令单独发明平行结构
- 新命令必须在 `__init__.py` 和 `cli.py` 双重注册

## 7. 常见坑

- 忘记在 `cli.py` 的 `build_parser()` 中调用 `register_xxx_commands(subparsers)` 会导致命令不可见
- `argparse` 的 `dest` 参数和 `--entity-id` 的 kebab-case 需要显式 `dest="entity_id"`
- `review scene` 的段落范围是 1-based 且基于“去掉标题后的正文段落”计数，和 markdown 原始行号不是一回事
- `review editor-draft --dry-run` 不会调用 provider，也不会写 editor fragment；真实运行需要 `--api-key` 或 `TEXT_PROVIDER_API_KEY` / `OPENAI_API_KEY`
- `review scene --scene-index` 在没有 `scenePlans` 时会回退到启发式候选场景
- 一旦章节里存在显式 `scenePlans`，`review scene --scene-index` 会优先使用显式边界，而不是启发式切分
- `outline scene-update` 更新段落范围时，必须同时提供 `--start-paragraph` 和 `--end-paragraph`
- `outline scene-detect` 默认不会覆盖已有 `scenePlans`，需要显式传入 `--replace`
- `outline scene-detect` 当前会拒绝对“没有正文段落的空白章节”生成 scenePlans，避免把 bootstrap 空稿误判成可用场景
- `outline scene-sync` 当前不会强行重排 scene 数量；若现有 scene 数量与 heuristic 切分数量不一致，它会保留为只读报告，避免把人工结构直接覆盖掉
- `entity mention-check` 对引号内的 plain mention 默认降级忽略，避免把角色彼此的称呼变化机械当成“必须补 `@{}`”的问题
- `entity mention-apply` 只接受 `mention-plan` 中的确定性 tag action；若把缺失建档 action id 直接喂给它，会明确报错并要求改走 adopt 命令
- `foreshadow check` 的 overdue 判断当前只基于 chapter id / chapter number 顺序，不理解更复杂的非线性时间轴
- `chapter suggest` 默认要求目标章节先通过 `outline check`，旧项目如需跳过必须显式传 `--allow-without-outline`
- `outline check` 默认是严格模式；只有显式传入 `--allow-missing-project-gate`、`--allow-missing-beats`、`--allow-missing-scene-plans` 才会放宽
- `review chapter` 的 `priorityActions` / `contractAlignment` 已会消费 `structuredPlanBlock` 这类高置信风格信号；若只看到 `patternResults` 没看到动作项，优先检查 style report 是否被截断或文本是否低于检测阈值
- `review scene` 现在会把 full chapter 与当前 scene 范围一并透传给一致性检测，因此 `outlineDeviation` 只应提示当前 scene 的 beat miss，不再机械复制整章 warning；若看到跨 scene 重复告警，优先检查 `scenePlans` 段落范围是否失真
- `workflow advance` 只能对当前 gate 执行；如果要回到更早 gate，必须先 `workflow run --resume-from <stage>` 或 `workflow reset --from-gate <stage>`
- `workflow status` 会把持久化的 `workflow.yaml` 与当前推断结果合并展示，因此 `currentStage` 可能早于 `inferredCurrentStage`
- chapter workflow 当前最小可验证链路为 `project_contract -> outline_ready -> context_ready -> chapter_review_ready -> scene_review_ready -> export_ready`；其中 `context_ready` 用于确认当前章至少完成一轮 `context refresh`
- 对带有 `chapterContentHash` 的新 context lens，`context_ready` 会在章节正文变化后重新阻塞并要求刷新 context；旧 lens 缺少该字段时保持兼容，不强制判 stale；状态输出用 `contextHashStatus/contextHashTracked` 显式标记 fresh、stale 或 `legacy-untracked`
- `workflow status/export --volume-id` 当前仍不会写 `workflow.yaml`；卷级状态依旧由 `review preflight` + `review volume-self` 的组合结果临时推断，而不是持久化成独立 volume workflow 文件
- `status` 只做只读聚合；若 `scenePlans` 段落范围已越界，它只会报告 `invalidScenePlans`，不会自动回写修正
- `status.targetChapter.mentionHygiene` 只输出紧凑摘要和 top items；需要完整 action plan 时仍应改用 `entity mention-plan`
- `illustration generate --dry-run` 不会写 `illustrations.yaml`；只有真实生成成功后才会落记录
- `illustration generate --batch-count <n>` 当前只支持 `same-template` 策略：会按同一 prompt 连续请求并顺序落盘，不会自动做 modifier/prompt 变体扩散
- `illustration batch-export` 默认会把 manifest 写到 `logs/illustration-batches/<label>.json`；这只是派生清单，不是新的长期真相源
- `illustration batch-record` 要求 manifest 中声明的 `outputFiles[]` 已经落盘；若文件缺失会直接失败，而不是静默跳过
- `illustration generate` / `batch-export` 当前会按 target type + use case 自动选路径：`chapter` 进入 `assets/illustrations/chapters/<chapter-id>/<use-case>/`，`entity` 进入 `assets/illustrations/entities/<entity-id>/<use-case>/`，`temporary` 进入 `tmp/illustrations/staging/<temp-label>/<use-case>/`
- `illustration prompt/generate` 当前支持 `--temp-label`，用于不绑定具体小说章节/角色的临时图任务；默认命名仍由系统给出，自定义命名继续走 `--output-name`
- `illustration prompt/generate --use-case` 当前会统一走首批 use-case 矩阵解析；若当前 pack 没有专用模板，会沿同类 fallback 选模板，而不是误退到 pack 第一条模板
- 本地 UI API 的 `/api/illustration/dry-run` 与 `/api/illustration/generate` 也应保持与 CLI 相同的 payload / provider request / 落盘行为，避免维护平行实现
- `illustration generate --mode image-to-image` 至少需要一张 `--input-image`
- `illustration generate --mode inpaint` 当前复用 edit request，但额外要求 `--mask`
- `illustration generate --mode image-to-image --mask <path>` 会把 mask 一并上传给 provider，mask 仅作用于第一张输入图
- `illustration generate` 真实执行时会把返回图批量写入 `assets/illustrations/`；`filePath` 仍指向主图，额外结果写入 `artifacts[]`
- `illustration list` 会补充资产存在性、数量、主图标记，以及 chapter/entity/input-image/mask 的引用状态
- `illustration prompt/generate` 当前会把已解析的 `promptSnapshot/policySnapshot` 暴露到 CLI 输出与落盘历史，便于后续复现 pack/template/modifier 展开结果
- `doctor` 会基于 `illustrations.yaml` 检查缺失资产、主图路径不一致、失效 target/input/mask 引用和 `assets/illustrations/` 下的孤儿文件

## 8. 测试方式

- 单元测试: 各 `tests/smoke/test_xxx_command.py`
- 调用方式: `from story_harness_cli.cli import main; main(["command", "subcommand", ...])`
- 输出捕获: `contextlib.redirect_stdout(StringIO())`

## 9. 文档同步触发条件

- 新增/删除命令
- 命令参数变化（breaking change）
- 输出格式变化
- workflow 文件读写路径变化
- 注册方式变化
