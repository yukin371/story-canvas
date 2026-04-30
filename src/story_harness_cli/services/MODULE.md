# Services 模块说明

> 最后更新: 2026-04-30
> 状态: 当前有效模块文档

## 1. 模块职责

- 纯业务逻辑：章节分析、变更请求生成、投影管理、一致性校验、实体丰富化、灵感生成、统计计算
- 所有函数接受 state dict（+ 必要参数），返回结果 dict
- 无副作用：不读写文件，不打印输出

## 2. Owns

- `analyzer.py`: 章节分析（实体识别、状态检测、关系检测、场景范围）
- `analyzer.py`: 章节分析（实体识别、状态检测、关系检测、场景范围），以及正文名称到 `entities/worldbook` 建档条目的引用对齐；当前会跳过已建档 worldbook 引用的 inferred character 注册，避免势力/地点/物件污染角色链路
- `change_requests.py`: 变更请求生成与审核
- `projection_engine.py`: 投影状态管理（upsert_by_key 去重），并在 `projection apply` 时吸纳高置信、无冲突的新设定候选到 `worldbook.premiseFacts`
- `consistency_engine.py`: 一致性校验（hard checks: 状态/关系矛盾; soft checks: 大纲偏离），并输出正文中新设定候选、和既有世界设定的冲突预警，以及高置信的“姓名/身份无来源提前揭露”“能力层级 vs 任务风险不匹配”“当前境界 vs 突破目标越阶”风险
- `rule_registry.py`: builtin 规则元数据真相源，集中登记稳定 `ruleId` 的默认 `source/scope/kind/severity/tags`
- `rule_semantics.py`: 统一规则 judgement 语义包装，负责给现有检测结果补 `ruleId/source/scope/kind/severity` 等规范字段
- `review_rule_detector.py`: review-rule profile 驱动的独立规则检测入口，当前负责 `metaLeakage`、`povOverreach` 与 whitelist 豁免求值，并向 `style_detector` 返回可并入 `patternResults` 的规则信号；`povOverreach` 首版只覆盖高置信的有限视角盲区细节断言（如身后/右后方的具体视觉细节），暂不追求全量语义 POV 分析
- `entity_enricher.py`: 角色外貌/能力提取与丰富化提案
- `context_lens.py`: 写作上下文构建（活跃角色/关系 + 情绪契约 + 题材模板 + 世界约束 + 线索/伏笔切片），并产出 `previous/current/next chapter` 承接摘要与可延续的角色变化 / 线程信号
- `context_lens.py`: 当命令层传入当前章节的新 analysis 时，优先使用 analysis 的 scene scope，并只采纳仍由本次 analysis 支撑的同章 snapshot，避免旧 projection 污染新上下文
- `outline_guard.py`: 章节大纲前置检查，判断是否具备项目定位 / 故事契约 + direction / beats / scenePlans 进入写作或细化
- `story_review.py`: 章节回顾评分、场景评审、类型/平台加权评分、评论、改稿建议、契约对齐与商业连载对齐检查，并开始消费情绪契约、揭露偏好、模板关注点、伏笔窗口、世界规则、角色动态状态，以及 style/consistency 护栏信号；对高置信“方案文档腔”会进入 `priorityActions` 与 `contractAlignment.risks`；chapter 级 review 现还会消费章节承接摘要，对“上一章结果 -> 本章开头承接偏弱”输出 `chapterHandoffSignals`、`priorityActions`、`contractAlignment.risks` 与 `chapterHandoffWeak` rule judgement；chapter/scene 共用的 `projectContext`、`priorityActions` 与对齐后处理已收敛到共享 helper，避免两条评审路径长期并行漂移；章节评分现会把禁令、异议、担保、限水、原始日志、接管链路、提交期限等程序/证据张力计入推进、压力与冲突维度；场景伏笔评分与章末商业 hook 对齐现会把陌生号码、日志异常、接管链路、被截断输入等悬念物证信号计入钩子
- `style_detector.py`: AI 风格启发式检测与约束生成；允许通过外部注入 scorer 增强句式近似判断，但默认保持 builtin fallback，并支持基于 profile 的术语观察词、重复白名单、词级阈值、题材语域失真词表、叙事支架复用检测，以及连续 `目标：/风险：/约束：/时间窗口：` 这类结构化方案块识别；`planBlockPolicy` 可对标签白名单与命中阈值做题材级放宽；当前还内建了中文高频 AI 句式簇（`不是……是……`、`不像……更像……`、`真正……从来都是……` / `还有什么？`）、移动端段落可读性信号，以及 `clusteredAIPhrasing` 聚合层，用于把多项轻度 AI 句式/可读性问题收敛成统一风险；同时会消费 `review_rule_detector.py` 返回的规则信号，把 `review-rules.yaml` 驱动的检测结果并入 `patternResults/judgements`
- `illustration_prompting.py`: chapter / entity 插图 prompt 构造、template/modifier/policy/lexicon 解析后的 prompt snapshot 组装、目标元数据整理与 dry-run request 组装；当前 entity prompt 优先抽取角色卡外貌/视觉锚点，chapter prompt 则避免直接注入章节正文摘要，并把模板从标签式拼接收敛成更自然的美术 brief；chapter / entity / temporary 当前都可显式选择首批 use-case 矩阵，并额外支持“纯绘图 / 文字设计”这组正交文本版式参数
- `illustration_prompting.py`: 当前还支持 freeform / temporary 目标 payload；当图片不绑定具体章节或角色时，仍走相同 pack/template 展开，但 target type 会标记为 `temporary`；pack 没有专用模板时，服务层会按同类 use-case fallback 解析模板与词库
- `illustration_batching.py`: batch spec 归一化、delivery mode 约束、batch manifest summary，以及 `webui-manual` / `external-agent` 的纯说明载荷组装
- `reference_mentions.py`: 章节内结构化引用 mention 的纯分析，负责已建档引用目录、已包裹/未包裹/未建档分组、plain mention 的确定性 tag replacement 候选，以及最小 related context
- `workflow_engine.py`: workflow 状态机纯函数，负责阶段推断、状态 hydration/build、gate 决策推进、reset 与导出快照；章节级 `context_ready` 会消费命令层传入的章节正文指纹，对新生成的 context lens 做过期判断，并通过 `contextHashStatus/contextHashTracked` 显式区分 fresh、stale 与旧 lens 兼容状态
- `workflow_engine.py`: workflow gate 现会为阻塞项补统一 `ruleJudgements` 与 `gateDecision`，让门禁结果能引用具体规则 id，而不是只返回散乱说明
- `workflow_engine.py` 的卷级 tooling gate 当前还会消费 command 层透传的 `volumeClosureContract` / `closure-readiness`；当项目已明示“X 章首卷”但当前卷章数未满足时，会直接阻塞在 `volume_tooling_gate`
- `workflow_engine.py` 现还负责卷级 gate 的纯推断：先消费卷级 `review preflight` 聚合结果，再结合最新 `review volume-self` 结论，输出“工具侧是否清障 / 是否可进入人工审查”的只读 workflow 视图
- `workflow_engine.py` 的卷级摘要当前还会透出 `repairCoverage` 紧凑字段，供 `workflow status/export --volume-id` 直接显示弱项覆盖状态，而不必额外反查原始自审记录
- `workflow_engine.py` 的卷级摘要当前还会直接透出 `volumeStructureCheck`，把 preflight 已有的卷级结构检查提升到 workflow 顶层，避免 UI / agent 只能从嵌套 preflight 中取值
- `workflow_engine.py` 在卷级 `human_review_ready` gate 中，当前还会把 `repairCoverage.uncoveredWeakDimensionLabels` 视为显式阻塞，并把这些弱项翻译成更具体的 `nextActions`
- `workflow_engine.py` 当前还会为卷级当前 gate 生成只读 `changeRequestDrafts`：工具侧阻塞会转成带 `chapterId/evidence` 的修复草案，卷级自审阻塞会转成修稿动作草案；当卷级自审尚未生成时，还会把 `volumeStructureCheck` 中的 `risk/missing` 检查项转成结构修补草案，供 UI/agent 直接消费而不必二次解析 `nextActions`
- `volume_self_review.py`: 卷级 AI 自审的纯校验与归一化，负责固定评分维度、缺陷归因、独立编辑审查元数据、问题级工具/自审漏检解释，以及人工审查门槛判断，并提供最近一次卷级自审结果读取 helper
- `text_provider_review.py`: 文本 provider 独立编辑审查的纯 prompt 构造、JSON 输出解析与 editor fragment 归一化；不调用网络、不读写文件
- `volume_self_review.py` 当前还提供卷级自审 payload merge helper，供命令层把 author/editor 分片输入结构化合稿，而不是让 agent 手工拼整份 YAML
- `volume_self_review.py` 生成模板时当前还会透传 command 层卷级预检中的 `volumeStructureCheck`、chapter/scene/style 证据摘要，并显式提示独立编辑审查模式 / 上下文隔离要求，让 AI 自审能直接对照卷级阶段映射与结构检查稿
- `volume_self_review.py` 当前还会把这些卷级工具信号启发式收敛成 root `scores/issues/closureAssessment` draft，优先产出可审阅起点而不是全空模板，但不会擅自把默认结论抬成 `closed`
- `volume_self_review.py` 现还负责拦截模板占位值，避免未填写完成的卷级自审草稿被写入 `story_reviews`
- `volume_self_review.py` 现还会做最小有效性检查，拒绝“全部 0 分”或与闭环结论不匹配的空白 `delivered/missing`
- `volume_self_review.py` 现还会做最小一致性检查，避免“声明可人工审查但门槛未过”“独立编辑审查未完成却想放行”或“未闭环却没有主要问题清单”这类自相矛盾输入
- `volume_self_review.py` 当前还要求 `0-2` 分弱项必须能对齐到可核对的章节或证据锚点，优先通过 `scores[].chapterRefs/evidenceRefs`，否则至少要在带 ref 的 `issues[]` 中能追到对应问题
- `volume_self_review.py` 现还会用轻量关键词做低分维度覆盖检查，避免 `issues/fixAction/repairSuggestions` 与最弱项完全脱节
- `volume_self_review.py` 现还会归一化 `repairCoverage` 摘要，输出弱项列表、未覆盖弱项和 coverage status，供 `status/export` 直接消费
- `volume_self_review.py` 的 `repairCoverage` 当前会合并 root 自审与独立编辑评分中的低分弱项，并保留 `rootWeakDimensionLabels` / `editorWeakDimensionLabels`，避免多代理审查发现的问题只藏在 `editorAssessment.scores` 里
- `volume_self_review.py` 的 `issues` 现还兼容可选 `chapterRefs/evidenceRefs`，用于把卷级问题直接锚到章节或外部审查证据
- `volume_self_review.py` 当前还提供卷级 issue refs 的纯校验 helper，供 command 层在拿到章节段落数 / scenePlans 后验证 `chapter-xxx#paragraph-n` 与 `chapter-xxx#scene-n` 是否真的存在
- `volume_self_review.py` 当前还会消费 command 层提供的 `semanticAnchors` 做纯校验，首批支持 `chapter-xxx#world-rule-onboarding` 与 `chapter-xxx#handoff-gap` 这类章节语义锚点
- `volume_self_review.py` 对 `chapter-xxx#scene-n` 的纯校验当前还会要求 command 层传入对应章节的 persisted `scene review` 映射，确保 scene 锚点能稳定落到 review-packet / scene review 对象
- `inspiration.py`: 随机灵感生成（姓名、角色、世界、大纲骨架）
- `stats.py`: 项目统计（进度、字数、实体、投影）

## 3. Must Not Own

- 文件 I/O（不读文件、不写文件）
- argparse 参数处理
- JSON 输出格式化
- 状态持久化决策

## 4. 关键入口

- `analyze_chapter(root, state, chapter_id)`: 完整章节分析
- `generate_change_requests(state, analysis)`: 分析 → 变更请求
- `apply_projection(state, analysis, chapter_id)`: 投影应用
- `check_consistency(state, chapter_text, chapter_id, keywords=None, *, full_chapter_text=None, scene_scope=None)`: 一致性校验，返回 hard/soft checks、设定候选与设定冲突上下文；`outlineDeviation` 现优先消费显式 `scenePlans` 与正文段落证据，scene review 可通过 `scene_scope` 只看当前场景
- `enrich_entities(state, chapter_id, root)`: 实体丰富化
- `refresh_context_lens(state, chapter_id, analysis)`: 上下文刷新，返回适合当前章节写作的最小约束切片，并显式暴露 `chapterHandoff`；命令层会在持久化前补入当前章节正文内容指纹
- `evaluate_project_story_gate(state)`: 检查项目是否已具备 `primaryGenre`、`targetAudience`、`corePromises`、`paceContract`
- `evaluate_chapter_outline_readiness(state, chapter_id, require_beats=True, require_scene_plans=True, require_project_gate=True)`: 检查单章是否已具备严格大纲前置设计
- `evaluate_project_outline_readiness(state, chapter_id=None, require_beats=True, require_scene_plans=True, require_project_gate=True)`: 生成项目级或章节级大纲门禁报告
- `build_chapter_review(state, chapter_id, chapter_text, analysis)`: 章节质量回顾，输出通用 `scores`、类型/平台加权 `weightedScores`、`contractAlignment` 与 `commercialAlignment`
- `build_scene_review(state, chapter_id, chapter_text, start_paragraph, end_paragraph, analysis)`: 场景质量回顾，输出功能性、连续性、逻辑、伏笔、清晰度，以及场景级 `contractAlignment` 与 `commercialAlignment`
- `list_scene_candidates(chapter_text)`: 基于正文段落启发式切分候选 scene 范围，供 `review scene --list-scenes/--scene-index` 使用
- `resolve_scene_candidates(chapter_entry, chapter_text)`: 优先读取显式 `scenePlans`，否则回退到启发式候选 scene
- `detect_scene_plans(chapter_id, chapter_text)`: 把启发式候选 scene 转成可持久化的显式 `scenePlans`
- `compute_project_stats(state, root)`: 项目统计
- `infer_workflow_status(state, chapter_id=None, chapter_files=None)`: 推断 workflow 当前阶段、阶段完成度与 next actions
- `infer_volume_preflight_workflow(preflight_payload, volume_self_review=None)`: 基于卷级 preflight 聚合结果与最新卷级自审结论推断只读 volume workflow gate
- `build_volume_self_review_template(preflight_payload, generated_at, latest_review=None)`: 生成卷级 AI 自审模板骨架，并附带当前卷的预检摘要、逐章信号和建议修补方向
- `normalize_volume_self_review(raw_payload, volume_id, volume_title, generated_at)`: 校验并归一化卷级 AI 自审结构，计算 `finalAllowHumanReview`
- `build_volume_editor_provider_prompt(preflight_payload, review_packet_text, generated_at)`: 为 clean-room 独立编辑 provider 构造 prompt payload
- `parse_text_provider_json_object(text)`: 解析 provider 返回的严格 JSON 对象，兼容 fenced json
- `normalize_editor_provider_fragment(raw_payload, provider_name, model, generated_at)`: 将 provider 输出归一为 `editorPass` + `editorAssessment` fragment
- `latest_volume_self_review(story_reviews, volume_id)`: 读取指定卷最近一次卷级 AI 自审结果
- `hydrate_workflow_progress(workflow_progress, inferred)`: 合并持久化 workflow 元数据与当前推断阶段结果
- `build_workflow_progress(inferred, existing=None, now_iso, run_mode, resume_from=None)`: 构造或刷新 `workflow.yaml` 快照，并支持从指定 gate 回卷
- `advance_workflow_progress(workflow_progress, inferred, gate_id, decision, feedback, now_iso)`: 记录当前 gate 的 `accept/modify/reject` 决策并推进状态机
- `reset_workflow_progress(workflow_progress, inferred, from_gate, now_iso)`: 清除指定 gate 及之后的决策元数据并回到该 gate
- `export_workflow_payload(workflow_progress, inferred)`: 输出面向 CLI 的 workflow 快照载荷
- `build_style_repair_prompt(chapter_text, style_report, chapter_id)`: 基于 styleAnalysis 生成可直接喂给模型的精修 prompt
- `build_style_change_request_drafts(chapter_id, style_report)`: 把风格问题转成 change-request 风格草案
- `build_chapter_illustration_payload(...)`: 生成章节插图 payload，当前会输出 `promptSnapshot/policySnapshot/templateId/modifierRefs/commercialMode`，以及可复现的 `promptSnapshot.lexiconSnapshot`
- `build_entity_illustration_payload(...)`: 生成人物设定图 payload，当前会输出 `promptSnapshot/policySnapshot/templateId/modifierRefs/commercialMode`，以及可复现的 `promptSnapshot.lexiconSnapshot`
- `build_freeform_illustration_payload(...)`: 生成临时图 / 非小说归属图 payload，当前会输出 `targetType=temporary` 与 `useCase`
- `normalize_illustration_batch_spec(raw_spec)`: 归一化批量插画 spec，保证 jobs/defaults 最小结构和 target 约束
- `build_batch_delivery_payload(...)`: 基于 resolved payload 生成 `webui-manual` 或 `external-agent` 的纯说明块
- `build_batch_manifest_summary(manifest)`: 汇总 batch job 数、输出数量与 target 摘要
- `build_reference_mention_report(state, chapter_text)`: 生成章节级引用审查报告，输出 tagged covered / tagged missing / known unwrapped / quoted ignored
- `build_reference_catalog(state)`: 从 `entities + worldbook` 生成可匹配引用目录
- `collect_tag_replacements(chapter_text, catalog, target_name="")`: 生成可确定性执行的 `@{}` 包裹 replacement 列表

## 5. 关键依赖

- 依赖 `utils/text.py`: 关键词匹配、标签提取、段落拆分
- 依赖 `utils/hashing.py`: 指纹生成（去重用）
- 依赖 `data/`: 创作数据表（inspiration.py 专用）

## 6. 不变量

- 纯函数：相同输入必定产生相同输出
- 不修改传入的 state dict（返回新 dict）
- `entity_enricher.py` 是唯一例外：接受 `root: Path` 参数读取章节文件

## 7. 常见坑

- `entity_enricher.py` 跨段落实体归属问题：当多个实体出现在同一段落时，提取的属性可能错配给后出现的实体
- `consistency_engine.py` 的 negation 检查仅适用于 `INTIMATE_WORDS_NEED_NEGATION_CHECK` 集合中的词
- `consistency_engine.py` 的 `outlineDeviation` 现在优先走 `scenePlans + 正文段落` 的轻量证据匹配；没有显式 `scenePlans` 时才回退到整章段落近似命中，因此“beat 数量与 scene 数量不一致”的章节仍应优先补 scenePlans 再看告警可信度
- `projection_engine.py` 的 `upsert_by_key` 使用 `|` 合并 dict，确保 payload 完整覆盖
- `projection_engine.py` 对新设定的自动入账当前只写 `worldbook.premiseFacts`，不会自动升级成 `worldRules`
- `story_review.py` 里 `primaryGenre` 与 `subGenre`/`styleTags` 的归一化口径不同：前者归主类，后者保留细分类 slug
- `story_review.py` 的职业/程序悬疑张力仍是 core 关键词启发式，后续若继续扩展题材，应优先迁入 profile/overlay 信号配置，而不是无限扩充核心词表
- `story_review.py` 的 `weightedScores.profile` 现在还会保留 `commercialPositioning.targetPlatform`，用于解释平台修正来源
- `build_scene_review` 当前按段落范围近似 scene，不是结构化 scene graph；结果应视为启发式提示
- `resolve_scene_candidates` 只有在 `scenePlans` 缺失时才会启用启发式切分
- `detect_scene_plans` 只是把启发式切分结果显式化，不代表作者意图已完全确认
- `refresh_context_lens` 现在会优先保留紧凑切片而不是整份状态；新增字段应继续遵守“够写当前章即可”的边界
- `context_lens.py` 的 `chapterHandoff` 是启发式摘要，不等于完整章节摘要；它优先服务“写前知道上一章余波 / 本章承接 / 下一章交付”，而不是替代人工章节梳理
- 场景级 `contractAlignment` 复用了章节级契约思想，但阈值更偏向“局部兑现/局部钩子”，不等同于整章判断
- `story_review.py` 现在还会输出 `storyConstraintSignals`，用于暴露当前章评审实际消费到的情绪契约、世界规则、到窗伏笔和角色状态切片
- `story_review.py` 现在还会在 chapter review 中输出 `chapterHandoffSignals`，用于暴露“上一章结果 -> 本章起点”的承接风险；它是软规则，误报应优先通过真实样例回灌，而不是继续硬编码更重的剧情证明器
- `chapterHandoffSignals` 当前只在存在明确前章负载时触发：前章需要留下角色状态变化、活跃线程或章节方向负载；检测会同时看角色/状态/线程锚点、前章 direction / beat / scene goal 的语义锚点、“那句还没散 / 从某处脱身不过半个时辰”这类直接接续句式，以及命令层传入的上一章结尾窗口中是否存在当前章开头短对白 / 短句的高置信承接；单个弱语义锚点只算辅助证据，开头前两段没有接住但前四段内自然回接，会记录 `delayedBridge=true` 并避免误报，不要求每章开头机械复述上一章
- `story_review.py` 现在还会在 chapter review 中输出 `consistencySignals`，用于暴露高频特殊术语复用、设定候选和设定冲突
- `story_review.py` 现在还会通过 `consistencySignals.unintroducedNameReveals` 暴露“先匿名描写、后突兀报姓名”这类认知边界问题
- `story_review.py` 现在还会通过 `consistencySignals.capabilityTaskRisks` 暴露“低修为角色直接承担高风险任务但缺少例外说明”这类设定合理性问题
- `story_review.py` 现在还会通过 `consistencySignals.powerProgressionConflicts` 暴露“当前境界按 worldbook 应先到下一阶段，但正文却直接冲向更高目标”这类突破链问题
- `style_detector.py` / `consistency_engine.py` 现已开始输出统一 `judgements`；`story_review.py` 会进一步汇总成 `ruleJudgements`
- `rule_semantics.py` 现在会优先从 `rule_registry.py` 读取规则默认元数据；detector 侧只应继续提供动态 message/suggestion/evidence，而不是重复硬编码静态元数据
- `workflow_engine.py` 现在会把 gate 的 `missing` 项归一成 `ruleJudgements`，并在 `gateDecision.blockingRules` 中引用对应 rule ids
- `story_review.py` 现在也会在 scene review 中输出 `styleAnalysis` 与 `consistencySignals`，避免局部审查遗漏术语复用和设定漂移
- `story_review.py` 现在还会输出 `wrappedEntitySignals`，用于审查当前章/幕中已包裹实体是否都能对齐到角色卡、势力、地点或特殊物品设定
- `story_review.py` 对 `storyTemplate.reviewFocus` 和 `emotionalContract.revealPreference` 的消费仍是启发式提示，不应被误读成严格剧情证明器
- `style_detector.py` 的特殊术语复用检测默认是启发式；若项目存在刻意反复强化的母题，应该放进 `style-profiles.yaml -> termPolicy.allowRepeated`
- `style_detector.py` 的题材语域失真检测依赖 `style-profiles.yaml -> registerPolicy`；玄幻这类题材的现代项目管理语汇应优先通过 profile 管理，而不是硬编码在 review 层
- `style_detector.py` 的中文高频 AI 句式簇当前仍是启发式密度检测；它们更适合作为“频率过高的风格风险”而不是单句一票否决；`clusteredAIPhrasing` 也只是聚合风险，不等于句句都必须重写
- `style_detector.py` 的 `paragraphReadability` 当前按移动端阅读做偏保守的长段检测；命中不代表段落绝对错误，但会拉低样例的章节评级基线
- `style_detector.py` 的“前世的记忆 / 前世的经验”这类问题不走纯词典匹配，而是通过 `framePolicy` + 结构启发式识别重复叙事支架
- `style_detector.py` 的“方案文档腔”当前只抓高置信标签式块；必须出现同一连续块内至少 3 个标签命中且不少于 2 种标签，避免把普通说明句误判成清单口吻；若题材本就允许结构化术语，应优先通过 `style-profiles.yaml -> planBlockPolicy` 放宽
- `consistency_engine.py` 的突破链检测当前只在 `worldbook.powerProgressions` 明确登记、且正文出现清楚的“突破/冲击/晋入 + 已知阶段名”时触发；带 `传承灌顶/秘法/重修/破格` 等显式例外提示会抑制告警；多角色同窗与“未能突破/突破失败”这类否定句不会再按高置信越阶处理
- `commercialAlignment` 目前基于 hook、字数目标、章末钩子等启发式信号，不等同于真实市场反馈预测
- `illustration_prompting.py` 仍然只负责纯函数式 prompt 组装，不负责读取项目 pack 文件；pack 加载与 builtin / project resolution 仍归 protocol 层 owner
- `illustration_batching.py` 只负责 spec / delivery 的纯归一化和说明组装，不负责读写 manifest 文件，也不负责资产回录
- `illustration_prompting.py` 当前会优先消费 `profile.appearance/visual/look`、`seed.appearance/visual` 与当前外在状态作为角色图 prompt 基线；若角色卡没有这些字段，才回退到 summary
- `illustration_prompting.py` 的 chapter-scene prompt 当前不再直接拼接章节正文 excerpt，避免 prompt 过长和把正文误当作最终生图说明
- `illustration_prompting.py` 当前会优先把 modifier 转成自然短句，再和 pack 的 `lexicon` 一起渲染进模板；兼容旧模板时仍保留 `styleModifiers/userExtraPrompt/commercialPrompt` 这组旧 placeholder
- `illustration_prompting.py` 当前会把 `textDesignMode/titleText/subtitleText/bodyText/fontStyleHint` 收敛进 `promptSnapshot.textDesign`，并转成自然语言版式 brief；该层是请求级参数，不是新的模板分类
- `illustration_prompting.py` 当前按 use-case 家族解析 subject / guardrail / lexicon；即使 pack 只定义了 `chapter-scene`，`duel-scene`、`chase-escape`、`manga-panel` 也应优先沿同类模板 fallback，而不是退成不相关模板
- `evaluate_project_story_gate` 的用途是把“先确定市场定位和故事承诺，再拆章节”变成硬门禁，而不是 review 阶段的软建议
- workflow 的 `currentStage` 口径是“第一个未满足 inferred 条件的 gate”，不是“所有前置 gate 都必须先人工 accept 才算通过”
- `advance_workflow_progress` 只允许对当前 gate 执行 `accept`；若 inferred 条件未满足，会直接拒绝推进
- `context_ready` 的 stale 判断只对带有 `chapterContentHash` 的 lens 生效；旧项目旧 lens 继续按存在性兼容，刷新后才进入内容指纹校验；输出中的 `contextHashStatus=legacy-untracked` 用于暴露这种兼容状态

## 8. 测试方式

- 单元测试: `tests/smoke/test_*_engine.py`, `tests/smoke/test_*_enricher.py`
- 通常通过 commands 层间接测试

## 9. 文档同步触发条件

- 新增/删除 service
- service 接口变化（参数、返回值结构）
- 评分 rubric 或 review 结果结构变化
- 契约对齐规则变化
- 关键词表变化
- 去重/匹配逻辑变化
