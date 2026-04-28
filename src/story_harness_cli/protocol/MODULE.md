# Protocol 模块说明

> 最后更新: 2026-04-28
> 状态: 当前有效模块文档

## 1. 模块职责

- 定义项目文件结构约定（哪些文件必须存在、路径规则）
- 加载和保存项目状态（所有 YAML 文件的统一读写）
- 保存前的状态快照校验与根目录级写回互斥
- 提供默认 schema
- 大纲同步（volumes ↔ flat chapters）

## 2. Owns

- `ROOT_FILES` 常量：必须存在的根目录文件列表
- `load_project_state(root)`: 将所有 YAML 文件加载为统一 state dict
- `save_state(root, state)`: 将 state dict 写回各 YAML 文件
- 项目状态指纹：`load_project_state` 记录、`save_state` 校验，防止旧快照覆盖新状态
- `default_project_state()`: 返回所有 key 的空默认值
- `project.yaml` 默认结构：包含 `positioning`、`storyContract`、`emotionalContract`、`storyTemplate` 与 `commercialPositioning`
- `worldbook.yaml`: 世界/背景/规则/势力真相层状态文件（可缺省，缺失时回退 schema 默认值）
- `worldbook.yaml`: 世界/背景/规则/势力真相层状态文件（可缺省，缺失时回退 schema 默认值）；当前还可选承载 `powerProgressions[]`，记录玄幻/仙侠等题材的“当前境界 -> 下一阶段 -> 突破条件/瓶颈”最小链条
- `reviews/story-reviews.yaml`: 章节/一幕评审报告状态文件；当前还承载卷级 AI 自审结果 `volumeSelfReviews[]`
- `workflow.yaml`: workflow 状态机进度文件（可缺省，缺失时回退 schema 默认值；持久化 `currentStage`、`workflowStatus`、`gateHistory`、`stageResults` 等决策快照）
- `illustrations.yaml`: 插图配置与生成记录文件（可缺省，缺失时回退 schema 默认值）
- `illustrations.yaml`: 插图配置与生成记录文件（可缺省，缺失时回退 schema 默认值）；当前还承载 `promptSystem` 默认 pack / template / modifier / commercialMode，以及 `batchSystem.defaultDeliveryMode/externalAgentSkill`
- `protocol/illustration_batches.py`: 插画 batch manifest 默认目录与默认文件名约定，避免 commands / adapter / UI 各自发明导出路径
- `prompt_packs.py`: builtin prompt pack 真相源、项目级 `prompts/illustration-packs/*.yaml` 加载，以及旧版 `promptPack` 到新版 `promptSystem.defaultPack` 的兼容映射辅助；当前还负责 pack/template/modifier/policy/lexicon 的最小规范化、坏条目过滤、来源元数据补齐，以及用户 pack 文档的序列化/保存/导出
- `_sync_outline()`: volumes → flat chapters 自动同步

## 3. Must Not Own

- 业务逻辑（分析、投影、一致性等）
- 文件路径之外的项目约定

## 4. 关键入口

- `protocol/__init__.py`: `ensure_project_root`, `load_project_state`, `save_state`
- `protocol/files.py`: `ROOT_FILES`, `chapter_path`, `root_file`
- `protocol/io.py`: `dump_json_compatible_yaml`, `load_json_compatible_yaml`
- `protocol/style_profiles.py`: style profile 的 builtin 默认值、项目级覆盖与自动选择；当前也承载术语观察词、重复白名单、词级阈值、题材语域失真词表，以及叙事支架例外配置
- `protocol/review_rules.py`: review rule profile 的 builtin 默认值、项目级 `review-rules.yaml` 加载与白名单豁免归一化；当前承载规则启停列表与 `ruleId + scope + allowWhen + reason` 结构化豁免
- `protocol/schema.py`: `default_project_state`
- `protocol/prompt_packs.py`: builtin prompt packs、项目自定义 pack 加载与 pack summary / resolution
- `protocol/prompt_packs.py`: builtin prompt packs、项目自定义 pack 加载与 pack summary / resolution；同时负责把前端回传的用户模板保存到 `prompts/illustration-packs/`、把 builtin/default pack 导出到项目作用域，并对可选 `lexicon.subjectPhrases/detailPhrases/modePhrases/commercialPhrases/negativePhrases` 做最小规范化
- `protocol/illustration_batches.py`: batch manifest 导出路径约定
- `protocol/state.py`: `_sync_outline`, re-exports

## 5. 关键依赖

- 依赖 `utils/hashing.py`: 仅 `state.py` 中的指纹生成

## 6. 不变量

- `save_state` 开头始终调用 `_sync_outline`，保证 volumes 和 flat chapters 一致
- `save_state` 写回前必须校验载入时状态指纹，发现外部更新时拒绝覆盖
- `save_state` 写回阶段必须持有项目根目录级别锁，避免多命令同时写同一项目
- 所有 YAML 文件内容必须为合法 JSON
- `load_project_state` 对缺失文件使用 schema 默认值填充
- `load_project_state` 会为旧版 `project.yaml` 回填缺失的定位/契约/情绪契约/题材模板/商业蓝图字段
- `load_project_state` 会为旧版 `story-reviews.yaml` 回填缺失的 `sceneRubricVersion` / `sceneReviews` / `volumeSelfReviewRubricVersion` / `volumeSelfReviews`
- `load_project_state` 会为缺失的 `workflow.yaml` 回填完整 `workflow_progress` 默认结构
- `load_project_state` 会为缺失的 `illustrations.yaml` 回填完整 `illustrations` 默认结构
- `load_project_state` 会为旧版 `illustrations.yaml` 兼容回填 `promptSystem.defaultPack/defaultTemplateByUseCase/defaultModifierRefs/commercialMode` 与 `batchSystem.defaultDeliveryMode/externalAgentSkill`
- `load_project_state` 会为缺失的 `worldbook.yaml` 回填完整 `worldbook` 默认结构
- `load_project_state` 会为旧版或缺失的 `worldbook.yaml` 回填 `powerProgressions: []`，旧项目不需要迁移也不能因此报错
- `chapter_path` 的 fallback glob 查找只在 `chapters/` 目录内
- `style-profiles.yaml` 是可选配置文件，缺失时必须回退 builtin profile；除 pattern thresholds 外，也允许承载 `termPolicy.watchTerms/allowRepeated/perTermThresholds`、`registerPolicy.allowTerms/disallowedCategories`、`framePolicy.allowPrefixes/perPrefixThresholds` 与 `planBlockPolicy.allowLabels/minLabels/minDistinctLabels`
- `review-rules.yaml` 是可选配置文件，缺失时必须回退 builtin `default` profile；当前允许承载 `activeProfile`、`profiles.<name>.enabledRules[]` 与 `profiles.<name>.exemptions[]`
- `powerProgressions` 是 worldbook 的可选结构；协议层只保证默认值和读写兼容，不负责解释具体突破链语义

## 7. 常见坑

- `_sync_outline` 会覆盖 `outline["chapters"]` 和 `outline["chapterDirections"]`，不要手动维护这两个字段
- 多个会写状态的命令不能依赖“先 load 再晚点 save”而假设项目没变；一旦状态指纹不一致，必须重跑命令
- Windows 下路径需要用 `Path.resolve()` 避免反斜杠问题
- `workflow.yaml` 保存的是“推断结果 + 决策元数据”的组合快照，不能把 gate 是否完成仅理解为人工决策结果
- `illustrations.yaml` 当前保存的是配置、主图路径和资产元数据摘要，不等于图片二进制资产本身；图片文件仍存放在 `assets/illustrations/`
- batch manifest 本身不是长期状态真相源；它是由 CLI 基于 project state + prompt pack 解析出来的派生产物，真正历史仍回录到 `illustrations.yaml`
- `prompt_packs.py` 当前优先级为：显式指定 pack > `promptSystem.defaultPack` > builtin `default`；项目自定义 pack 与 builtin pack 允许并存，但 pack 文件本身仍必须是 JSON-compatible YAML
- `prompt_packs.py` 当前会为 project pack 补最小规范化：缺失 `id` 时按文件名派生 `project/<slug>`，缺失 `version` 时回填 `project`，并过滤缺少关键字段的 template / modifier / policy 条目；`lexicon` 缺失或坏结构时必须安全回退为空，而不是让 pack 整体失效
- `prompt_packs.py` 当前还会把常见 legacy prompt template（如 `visual direction:` / `user direction:` / `commercial direction:` 和旧 placeholder）迁到新 placeholder 风格；该迁移只作用于模板资源层，不回写历史生成记录
- 用户自定义 pack 只能落在 `prompts/illustration-packs/`；协议层保存 helper 不允许直接复用 builtin pack id 覆盖系统模板
- builtin/default pack 若需要项目内定制，必须先经协议层 export helper 克隆到 project scope，再编辑或迁移；不能直接改 builtin 真相源，也不能回写历史 `generated[].promptSnapshot`

## 8. 测试方式

- 单元测试: `tests/smoke/test_schema.py` 验证 schema 默认值
- 集成测试: 几乎所有测试都通过 `load_project_state` 间接测试

## 9. 文档同步触发条件

- 新增或删除 ROOT_FILES 中的文件
- 新增或删除项目级可选配置文件加载规则（如 `keywords.yaml`、`style-profiles.yaml`、`review-rules.yaml`、`worldbook.yaml`）
- 新增或删除 workflow 状态文件（如 `reviews/story-reviews.yaml`）
- `_sync_outline` 逻辑变化
- 状态锁或状态指纹校验逻辑变化
- `default_project_state` 结构变化
- 文件路径约定变化
