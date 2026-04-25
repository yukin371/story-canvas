# Services 模块说明

> 最后更新: 2026-04-25
> 状态: 当前有效模块文档

## 1. 模块职责

- 纯业务逻辑：章节分析、变更请求生成、投影管理、一致性校验、实体丰富化、灵感生成、统计计算
- 所有函数接受 state dict（+ 必要参数），返回结果 dict
- 无副作用：不读写文件，不打印输出

## 2. Owns

- `analyzer.py`: 章节分析（实体识别、状态检测、关系检测、场景范围）
- `analyzer.py`: 章节分析（实体识别、状态检测、关系检测、场景范围），以及正文名称到 `entities/worldbook` 建档条目的引用对齐
- `change_requests.py`: 变更请求生成与审核
- `projection_engine.py`: 投影状态管理（upsert_by_key 去重），并在 `projection apply` 时吸纳高置信、无冲突的新设定候选到 `worldbook.premiseFacts`
- `consistency_engine.py`: 一致性校验（hard checks: 状态/关系矛盾; soft checks: 大纲偏离），并输出正文中新设定候选、和既有世界设定的冲突预警，以及高置信的“姓名/身份无来源提前揭露”与“能力层级 vs 任务风险不匹配”风险
- `rule_semantics.py`: 统一规则 judgement 语义包装，负责给现有检测结果补 `ruleId/source/scope/kind/severity` 等规范字段
- `entity_enricher.py`: 角色外貌/能力提取与丰富化提案
- `context_lens.py`: 写作上下文构建（活跃角色/关系 + 情绪契约 + 题材模板 + 世界约束 + 线索/伏笔切片）
- `outline_guard.py`: 章节大纲前置检查，判断是否具备项目定位 / 故事契约 + direction / beats / scenePlans 进入写作或细化
- `story_review.py`: 章节回顾评分、一幕评审、类型/平台加权评分、评论、改稿建议、契约对齐与商业连载对齐检查，并开始消费情绪契约、揭露偏好、模板关注点、伏笔窗口、世界规则、角色动态状态，以及 style/consistency 护栏信号
- `style_detector.py`: AI 风格启发式检测与约束生成；允许通过外部注入 scorer 增强句式近似判断，但默认保持 builtin fallback，并支持基于 profile 的术语观察词、重复白名单、词级阈值、题材语域失真词表，以及叙事支架复用检测
- `illustration_prompting.py`: chapter / entity 插图 prompt 构造、目标元数据整理与 dry-run request 组装
- `workflow_engine.py`: workflow 状态机纯函数，负责阶段推断、状态 hydration/build、gate 决策推进、reset 与导出快照
- `workflow_engine.py`: workflow gate 现会为阻塞项补统一 `ruleJudgements` 与 `gateDecision`，让门禁结果能引用具体规则 id，而不是只返回散乱说明
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
- `check_consistency(state, chapter_text, chapter_id)`: 一致性校验，返回 hard/soft checks、设定候选与设定冲突上下文
- `enrich_entities(state, chapter_id, root)`: 实体丰富化
- `refresh_context_lens(state, chapter_id, analysis)`: 上下文刷新，返回适合当前章节写作的最小约束切片
- `evaluate_project_story_gate(state)`: 检查项目是否已具备 `primaryGenre`、`targetAudience`、`corePromises`、`paceContract`
- `evaluate_chapter_outline_readiness(state, chapter_id, require_beats=True, require_scene_plans=True, require_project_gate=True)`: 检查单章是否已具备严格大纲前置设计
- `evaluate_project_outline_readiness(state, chapter_id=None, require_beats=True, require_scene_plans=True, require_project_gate=True)`: 生成项目级或章节级大纲门禁报告
- `build_chapter_review(state, chapter_id, chapter_text, analysis)`: 章节质量回顾，输出通用 `scores`、类型/平台加权 `weightedScores`、`contractAlignment` 与 `commercialAlignment`
- `build_scene_review(state, chapter_id, chapter_text, start_paragraph, end_paragraph, analysis)`: 一幕质量回顾，输出功能性、连续性、逻辑、伏笔、清晰度，以及一幕级 `contractAlignment` 与 `commercialAlignment`
- `list_scene_candidates(chapter_text)`: 基于正文段落启发式切分候选 scene 范围，供 `review scene --list-scenes/--scene-index` 使用
- `resolve_scene_candidates(chapter_entry, chapter_text)`: 优先读取显式 `scenePlans`，否则回退到启发式候选 scene
- `detect_scene_plans(chapter_id, chapter_text)`: 把启发式候选 scene 转成可持久化的显式 `scenePlans`
- `compute_project_stats(state, root)`: 项目统计
- `infer_workflow_status(state, chapter_id=None, chapter_files=None)`: 推断 workflow 当前阶段、阶段完成度与 next actions
- `hydrate_workflow_progress(workflow_progress, inferred)`: 合并持久化 workflow 元数据与当前推断阶段结果
- `build_workflow_progress(inferred, existing=None, now_iso, run_mode, resume_from=None)`: 构造或刷新 `workflow.yaml` 快照，并支持从指定 gate 回卷
- `advance_workflow_progress(workflow_progress, inferred, gate_id, decision, feedback, now_iso)`: 记录当前 gate 的 `accept/modify/reject` 决策并推进状态机
- `reset_workflow_progress(workflow_progress, inferred, from_gate, now_iso)`: 清除指定 gate 及之后的决策元数据并回到该 gate
- `export_workflow_payload(workflow_progress, inferred)`: 输出面向 CLI 的 workflow 快照载荷
- `build_style_repair_prompt(chapter_text, style_report, chapter_id)`: 基于 styleAnalysis 生成可直接喂给模型的精修 prompt
- `build_style_change_request_drafts(chapter_id, style_report)`: 把风格问题转成 change-request 风格草案
- `build_chapter_illustration_payload(state, chapter_id, chapter_title, chapter_text, mode, input_images=None, mask_path=\"\", prompt_pack_name=\"default\")`: 生成章节插图 payload
- `build_entity_illustration_payload(state, entity, mode, input_images=None, mask_path=\"\", prompt_pack_name=\"default\")`: 生成人物设定图 payload

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
- `projection_engine.py` 的 `upsert_by_key` 使用 `|` 合并 dict，确保 payload 完整覆盖
- `projection_engine.py` 对新设定的自动入账当前只写 `worldbook.premiseFacts`，不会自动升级成 `worldRules`
- `story_review.py` 里 `primaryGenre` 与 `subGenre`/`styleTags` 的归一化口径不同：前者归主类，后者保留细分类 slug
- `story_review.py` 的 `weightedScores.profile` 现在还会保留 `commercialPositioning.targetPlatform`，用于解释平台修正来源
- `build_scene_review` 当前按段落范围近似 scene，不是结构化 scene graph；结果应视为启发式提示
- `resolve_scene_candidates` 只有在 `scenePlans` 缺失时才会启用启发式切分
- `detect_scene_plans` 只是把启发式切分结果显式化，不代表作者意图已完全确认
- `refresh_context_lens` 现在会优先保留紧凑切片而不是整份状态；新增字段应继续遵守“够写当前章即可”的边界
- 一幕级 `contractAlignment` 复用了章节级契约思想，但阈值更偏向“局部兑现/局部钩子”，不等同于整章判断
- `story_review.py` 现在还会输出 `storyConstraintSignals`，用于暴露当前章评审实际消费到的情绪契约、世界规则、到窗伏笔和角色状态切片
- `story_review.py` 现在还会在 chapter review 中输出 `consistencySignals`，用于暴露高频特殊术语复用、设定候选和设定冲突
- `story_review.py` 现在还会通过 `consistencySignals.unintroducedNameReveals` 暴露“先匿名描写、后突兀报姓名”这类认知边界问题
- `story_review.py` 现在还会通过 `consistencySignals.capabilityTaskRisks` 暴露“低修为角色直接承担高风险任务但缺少例外说明”这类设定合理性问题
- `style_detector.py` / `consistency_engine.py` 现已开始输出统一 `judgements`；`story_review.py` 会进一步汇总成 `ruleJudgements`
- `workflow_engine.py` 现在会把 gate 的 `missing` 项归一成 `ruleJudgements`，并在 `gateDecision.blockingRules` 中引用对应 rule ids
- `story_review.py` 现在也会在 scene review 中输出 `styleAnalysis` 与 `consistencySignals`，避免局部审查遗漏术语复用和设定漂移
- `story_review.py` 现在还会输出 `wrappedEntitySignals`，用于审查当前章/幕中已包裹实体是否都能对齐到角色卡、势力、地点或特殊物品设定
- `story_review.py` 对 `storyTemplate.reviewFocus` 和 `emotionalContract.revealPreference` 的消费仍是启发式提示，不应被误读成严格剧情证明器
- `style_detector.py` 的特殊术语复用检测默认是启发式；若项目存在刻意反复强化的母题，应该放进 `style-profiles.yaml -> termPolicy.allowRepeated`
- `style_detector.py` 的题材语域失真检测依赖 `style-profiles.yaml -> registerPolicy`；玄幻这类题材的现代项目管理语汇应优先通过 profile 管理，而不是硬编码在 review 层
- `style_detector.py` 的“前世的记忆 / 前世的经验”这类问题不走纯词典匹配，而是通过 `framePolicy` + 结构启发式识别重复叙事支架
- `commercialAlignment` 目前基于 hook、字数目标、章末钩子等启发式信号，不等同于真实市场反馈预测
- `evaluate_project_story_gate` 的用途是把“先确定市场定位和故事承诺，再拆章节”变成硬门禁，而不是 review 阶段的软建议
- workflow 的 `currentStage` 口径是“第一个未满足 inferred 条件的 gate”，不是“所有前置 gate 都必须先人工 accept 才算通过”
- `advance_workflow_progress` 只允许对当前 gate 执行 `accept`；若 inferred 条件未满足，会直接拒绝推进

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
