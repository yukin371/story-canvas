# Story Canvas

[English](./README.en.md) | [简体中文](./README.md)

Story Canvas 是一个面向 Agent 的故事与视觉工作流项目，当前以 `story-canvas` 作为主命令入口，并提供早期单页 UI 作为视觉壳。

它的目标不是用一个超大 Prompt 一次性写完小说，而是把创作过程拆成结构化状态：正文、提案、审查、投影、上下文刷新，以及逐步纳入的插画生成与可视化操作面。这样作者和 AI 可以在更明确的约束下协作，减少设定漂移、状态丢失和长篇写作中的“越写越散”。

如果你想先看标准闭环流程，建议先读 [docs/guides/creative-workflow.md](./docs/guides/creative-workflow.md)。

当前仓库提供：

- 基于文件协议的故事工程状态层
- 用于状态推进的 Python CLI
- 存放在 `projects/` 下的样例工程
- smoke tests 与可回归的故事基线
- 面向外部 API / SDK 的可选 provider 基础层
- 面向插画生成的 provider-backed 图片能力
- 带有商业化定位与连载蓝图的长篇样例

它目前还不是一个完整创作工作台，但已经不再只是“单纯 CLI”。当前产品由文件协议、Python 工作流入口与单页 UI 共同构成；短期内主工作流仍以命令入口驱动，UI 和图片能力会并行推进。并行开发清单见 [docs/plans/story-canvas-parallel-roadmap.md](./docs/plans/story-canvas-parallel-roadmap.md)。

## 它解决什么问题

- 把“提案”和“正史”分开管理
- 把章节分析变成显式审查步骤，而不是隐式脑补
- 只有在明确决策后，才更新机器可读状态
- 为下一轮写作刷新本地上下文，而不是反复重塞整个项目
- 在停止前同时检查章节级和场景级质量
- 把小说写作管理成一个可迭代、可追溯的工程流程

## 写作能力矩阵

这个仓库已经不再只是“角色卡 + 章节正文”。它已经具备约束式写作闭环，但不同能力的完成度并不完全相同。

| 能力域 | 当前状态 | 已实现内容 | 当前缺口 |
|------|------|------|------|
| 项目初始化与仓库骨架 | 已完成 | `init` 会创建固定项目结构、章节文件、协议文件、projections、reviews，以及 flat / layered 布局 | 当前仍通过命令完成初始化，尚无可视化项目初始化界面 |
| 项目级写作约束 | 已完成 | `project.yaml` 已支持 positioning、storyContract、emotionalContract、storyTemplate、commercialPositioning | 更像协议层，不是独立的 PRD 工作台 |
| 世界观 / 角色 / 伏笔 / 线索 / 时间线 | 已完成 | 已有 worldbook、entities、foreshadowing、threads、timeline、causality 等状态文件和命令 | 编辑体验仍偏原始，没有 UI 辅助 |
| 大纲与细纲 | 已完成 | 已支持 chapter direction、beats、scenePlans、detailed outline init/show、structure scaffold | 仍依赖 CLI 和人工审查 |
| 写前门禁与结构审查 | 已完成 | `outline check`、`doctor`、`consistency check`、workflow gate 已可检查写作准备度 | 仍是启发式检查，不是形式化证明 |
| 落稿支持 | 部分完成 | 正文保存在 `chapters/*.md`，`context refresh` 会给出当前章所需的角色、世界规则、线索、伏笔上下文 | 还没有专门的正文编辑器或桌面写作 UI |
| 写后审查与迭代 | 已完成 | `chapter analyze -> chapter suggest -> review apply -> projection apply -> context refresh -> review chapter/scene` 已能形成闭环，并可导出 `review-packet` 给人工审查 | 没有 Web UI 时，批量筛选和修改仍不够顺手 |
| 成稿导出 | 已完成 | `export` 已支持多种纯文本导出格式 | 发布包装和对外分发还不是这一层负责 |
| 人工审查界面 | 部分完成 | 所有结构化产物都已落盘，可供人查阅；`export --format review-packet` 可生成单章 Markdown 审查包 | 缺少更顺手的阅读、筛选、修改界面，现已提前进入并行开发轨道 |
| 模板丰富度与工作流自由编排 | 部分完成 | 已有 structure templates、style profiles、storyTemplate 字段、workflow 状态机 | 更丰富的题材模板和自由编排能力计划在 `v1.2` 增强 |
| 插画生成与视觉资产流 | 部分完成 | 已有 `illustration` 命令、provider 抽象，以及 OpenAI / 兼容网关图像请求链路 | 仍缺少历史浏览、参数复用、批量确认和更顺手的视觉界面 |

一句话总结：这个仓库已经具备一个可用的“小说工程内核”，可以做约束、写作、审查、投影和导出；当前主要缺的是界面层、人工审查体验，以及更丰富的模板资源。

当前发布边界补充：

- `v1.0.x` 仍以故事协议、workflow 闭环和样例回归为发布锚点
- 插画生成和早期 UI 不再完全后置到 `v1.1`，而是提前并行开发，用于降低小说生成测试的人力成本
- 当前主 CLI 命令为 `story-canvas`，旧命令 `story-harness` 仅保留为兼容别名

## 核心模型

当前工作流以这些层次组织：

1. `chapters/*.md`：正文
2. `proposals/draft-proposals.yaml`：进入正史前的提案
3. `reviews/change-requests.yaml`：分析之后生成的修改建议
4. `projections/projection.yaml`：当前机器可读真相层
5. `projections/context-lens.yaml`：当前章节的局部写作上下文

## 快速开始

方案 A：初始化一个新项目

```powershell
uv sync
uv run story-canvas init --root .\demo --title "Fog Harbor" --genre "Mystery"
```

如果你在做真实的商业化连载项目，建议初始化时就把商业定位写进去，而不是事后补元数据：

```powershell
uv run story-canvas init `
  --root .\demo `
  --title "夜巡收煞录" `
  --genre "奇幻" `
  --primary-genre fantasy `
  --sub-genre urban-occult `
  --style-tag web-serial `
  --target-audience qidian-reader `
  --core-promise "每章结尾保留追读钩子" `
  --pace-contract "中快节奏" `
  --premise "夜班接尸人继承城隍夜巡牌，处理都市异案并追查失踪父亲真相" `
  --hook-line "接尸抬到空棺的当夜，他被迫上岗做城隍夜巡。" `
  --hook-stack career-entry-hook `
  --hook-stack cliffhanger-end `
  --target-platform qidian `
  --serialization-model "2到3章一个单元异案，持续抬升主线阴谋" `
  --release-cadence "日更两章" `
  --chapter-word-floor 2000 `
  --chapter-word-target 3000
```

如果你在做重约束长篇，建议初始化时就把情绪契约和模板策略写进去，让后续审查与上下文刷新有明确消费对象：

```powershell
uv run story-canvas init `
  --root .\demo `
  --title "归墟" `
  --genre "奇幻" `
  --primary-genre fantasy `
  --sub-genre xuanhuan `
  --core-promise "暗线逐步拼合并持续兑现世界真相" `
  --pace-contract "中快节奏，卷末集中爆发" `
  --core-emotion "压迫下反制" `
  --core-emotion "真相落地时的原来如此" `
  --chapter-emotion-floor "每章至少有一个明确情绪推进点" `
  --forbidden-emotion "空转讲设定" `
  --default-reveal-mode partial-inference `
  --allow-direct-explain-at-climax `
  --story-template-id xianxia-revenge-serial `
  --story-template-label "仙侠复仇长篇" `
  --module-policy worldbook=required `
  --module-policy worldRules=required `
  --module-policy factions=required `
  --module-policy foreshadowLedger=required `
  --module-policy characterStateTracking=required `
  --review-focus "世界规则兑现" `
  --review-focus "伏笔长回收"
```

这会在普通项目骨架之外，同时初始化：

- `project.emotionalContract`
- `project.storyTemplate`
- `worldbook.yaml`
- `foreshadowing.yaml`

然后编辑 `demo/chapters/chapter-001.md`，再执行：

```powershell
uv run story-canvas chapter analyze --root .\demo --chapter-id chapter-001
uv run story-canvas chapter suggest --root .\demo --chapter-id chapter-001
uv run story-canvas review apply --root .\demo --chapter-id chapter-001 --all-pending --decision accepted
uv run story-canvas projection apply --root .\demo --chapter-id chapter-001
uv run story-canvas context refresh --root .\demo --chapter-id chapter-001
uv run story-canvas review chapter --root .\demo --chapter-id chapter-001
uv run story-canvas outline scene-detect --root .\demo --chapter-id chapter-001
uv run story-canvas review scene --root .\demo --chapter-id chapter-001 --scene-index 1
uv run story-canvas doctor --root .\demo
uv run story-canvas export --root .\demo --chapter-id chapter-001 --format review-packet --output .\demo\chapter-001-review.md
```

方案 B：直接跑已验证的短篇基线

```powershell
uv run story-canvas doctor --root .\projects\demo-short-story
uv run story-canvas chapter analyze --root .\projects\demo-short-story --chapter-id chapter-001
uv run story-canvas chapter suggest --root .\projects\demo-short-story --chapter-id chapter-001
uv run story-canvas review apply --root .\projects\demo-short-story --chapter-id chapter-001 --all-pending --decision accepted
uv run story-canvas projection apply --root .\projects\demo-short-story --chapter-id chapter-001
uv run story-canvas context refresh --root .\projects\demo-short-story --chapter-id chapter-001
uv run story-canvas review chapter --root .\projects\demo-short-story --chapter-id chapter-001
uv run story-canvas review scene --root .\projects\demo-short-story --chapter-id chapter-001 --scene-index 1
```

方案 C：运行已验证的风格驱动短篇基线

```powershell
uv run story-canvas doctor --root .\projects\demo-light-novel-short
uv run story-canvas chapter analyze --root .\projects\demo-light-novel-short --chapter-id chapter-001
uv run story-canvas review chapter --root .\projects\demo-light-novel-short --chapter-id chapter-001
uv run story-canvas review scene --root .\projects\demo-light-novel-short --chapter-id chapter-001 --scene-index 1
uv run story-canvas export --root .\projects\demo-light-novel-short --format markdown --output .\projects\demo-light-novel-short\manuscript.md
```

方案 D：运行已验证的玄幻网文短篇基线

```powershell
uv run story-canvas doctor --root .\projects\demo-xuanhuan-short
uv run story-canvas chapter analyze --root .\projects\demo-xuanhuan-short --chapter-id chapter-001
uv run story-canvas review chapter --root .\projects\demo-xuanhuan-short --chapter-id chapter-001
uv run story-canvas review scene --root .\projects\demo-xuanhuan-short --chapter-id chapter-001 --scene-index 1
uv run story-canvas export --root .\projects\demo-xuanhuan-short --format markdown --output .\projects\demo-xuanhuan-short\manuscript.md
```

仓库直跑回退方式：

```powershell
$env:PYTHONPATH='src'
python -m story_canvas chapter analyze --root .\demo --chapter-id chapter-001
```

如果你想看当前样例矩阵，请读 [docs/guides/sample-matrix.md](./docs/guides/sample-matrix.md)。

如果你想跑更接近真实商业连载的长篇基线，可以使用 `demo-urban-occult-long`。它包含显式 `commercialPositioning`、卷结构骨架和章节字数目标。

完整闭环和停止条件见：

- [docs/guides/creative-workflow.md](./docs/guides/creative-workflow.md)
- [docs/guides/quickstart.md](./docs/guides/quickstart.md)

## 工作流示例

单章循环：

```text
chapter.md
  -> chapter analyze
  -> chapter suggest
  -> review apply
  -> projection apply
  -> context refresh
  -> review chapter
  -> scene detect / 维护 scenePlans
  -> review scene
  -> 如果评分不够好，改正文或改 scene plan
  -> 继续迭代直到可接受
```

大纲循环：

```text
目标或想法
  -> outline propose
  -> outline promote
  -> projection apply
```

## 命令概览

- `story-canvas init`
- `story-canvas brainstorm character|world|outline`
- `story-canvas chapter analyze`
- `story-canvas chapter suggest`
- `story-canvas review apply`
- `story-canvas review chapter`
- `story-canvas review scene`
- `story-canvas outline propose`
- `story-canvas outline promote`
- `story-canvas outline beat-add`
- `story-canvas outline beat-complete`
- `story-canvas outline beat-list`
- `story-canvas outline scene-add`
- `story-canvas outline scene-list`
- `story-canvas outline scene-detect`
- `story-canvas outline scene-update`
- `story-canvas outline scene-remove`
- `story-canvas outline detail-init`
- `story-canvas outline detail-show`
- `story-canvas projection apply`
- `story-canvas context refresh|show`
- `story-canvas entity enrich|review|list|show|graph`
- `story-canvas style check|constraints|report|repair`
- `story-canvas illustration prompt|generate|list|config`
- `story-canvas structure list|apply|show|check|map|scaffold`
- `story-canvas thread plant|resolve|list|check`
- `story-canvas foreshadow plant|resolve|list`
- `story-canvas arc define|milestone|list|check`
- `story-canvas workflow status|run|advance|reset|export`
- `story-canvas timeline add/list/check`
- `story-canvas causality add/list/check`
- `story-canvas search`
- `story-canvas consistency check`
- `story-canvas stats`
- `story-canvas migrate`
- `story-canvas export --format json|markdown|txt`
- `story-canvas export --format spec-outline|spec-characters|spec-global-outline|spec-detail|review-packet`
- `story-canvas doctor`

## 仓库结构

- `src/story_canvas/`：对外 Python 模块与主 CLI 入口包装
- `src/story_harness_cli/`：当前内部命令、协议、服务实现 owner
- `adapters/`：Codex、Claude Code 等宿主的 adapter 源码
- `scripts/install_adapter.py`：把单个宿主 adapter 安装到对应目录
- `scripts/install_adapters.py`：批量安装多个宿主 adapter
- `docs/`：协议与指南文档
- `projects/`：样例项目与回归基线
- `tests/`：smoke tests 与 fixtures

## 项目架构与约束机制

### 分层架构

项目采用清晰的分层设计，每层职责明确：

```
src/story_harness_cli/
├── protocol/          # 协议层：状态管理、schema定义、文件读写
│   ├── files.py       # 项目文件结构约定（ROOT_FILES、路径规则）
│   ├── io.py          # JSON-compatible YAML 统一读写
│   ├── state.py       # 状态加载/保存/指纹校验/大纲同步
│   ├── schema.py      # 默认项目状态结构
│   ├── style_profiles.py    # 风格配置：术语、语域、框架策略
│   ├── review_rules.py      # 审查规则：启停列表、豁免机制
│   └── prompt_packs.py      # 插图提示词系统
├── services/          # 业务逻辑层：分析、约束引擎
│   ├── analyzer.py        # 章节分析：实体识别、状态检测、关系检测
│   ├── consistency_engine.py  # 一致性校验：矛盾检查、设定冲突检测
│   ├── style_detector.py  # AI风格检测：句式识别、可读性、方案文档腔
│   ├── context_lens.py    # 写作上下文构建：角色、关系、情绪契约切片
│   ├── story_review.py    # 章节质量回顾：评分、契约对齐、商业连载检查
│   ├── workflow_engine.py # 工作流状态机：门禁、决策推进、回卷
│   ├── projection_engine.py  # 投影状态管理：设定去重、worldbook同步
│   └── text_provider_review.py  # 独立编辑审查：prompt构造、JSON解析
├── providers/         # 适配层：外部服务集成
│   ├── text/openai_http.py  # 文本生成：OpenAI兼容API客户端
│   └── image/         # 图片生成：多provider抽象层
├── commands/          # CLI命令层：用户交互入口
└── utils/             # 工具函数：文本处理、哈希、关键词匹配
```

### AI写作约束机制

项目通过多层约束确保AI写作的质量和一致性：

#### 1. 风格配置约束 (`style_profiles.yaml`)

**术语策略** (`termPolicy`)
- `watchTerms`: 高频术语监控，防止过度重复
- `allowRepeated`: 白名单术语（如母题关键词）
- `perTermThresholds`: 词级阈值配置
- `specialTermSuffixes`: 特殊术语后缀识别

**语域策略** (`registerPolicy`)
- `allowTerms`: 允许的题材语汇
- `disallowedCategories`: 禁止的语域类别
  - 示例：玄幻题材禁止"优先级""框架""闭环"等现代项目管理语汇

**框架策略** (`framePolicy`)
- `allowPrefixes`: 允许的叙事框架前缀
- `perPrefixThresholds`: 框架复用阈值
  - 示例：检测"前世的记忆""前世的经验"等重复叙事支架

**方案块策略** (`planBlockPolicy`)
- `allowLabels`: 允许的标签类型
- `minLabels`: 最小标签数量
- `minDistinctLabels`: 最小不同标签数
  - 检测"目标：/风险：/约束：/时间窗口："等结构化清单

#### 2. 审查规则约束 (`review-rules.yaml`)

```yaml
activeProfile: "default"
profiles:
  default:
    enabledRules: []  # 启用的规则ID列表
    exemptions:       # 细粒度豁免配置
      - ruleId: "metaLeakage"
        scope:
          chapterIds: ["chapter-001"]
          volumeIds: []
          scenePlanIds: []
        allowWhen:
          quotedOnly: false
          matchPatterns: []
        reason: "测试章节允许元信息泄露"
```

#### 3. AI风格检测引擎

**中文高频AI句式簇检测**
- "不是……是……"
- "不像……更像……"
- "真正……从来都是……"
- "还有什么？"

**移动端可读性检测**
- 长段落识别（影响移动端阅读体验）

**方案文档腔检测**
- 连续块内≥3个标签命中 + ≥2种标签类型
- 示例：`目标：xxx 风险：xxx 约束：xxx`

**聚合风险层** (`clusteredAIPhrasing`)
- 把多项轻度AI句式/可读性问题收敛成统一风险

#### 4. 上下文约束 (`context_lens.py`)

**写作上下文切片**
- 活跃角色/关系状态
- 情绪契约（核心情绪、禁止情绪、揭露偏好）
- 题材模板关注点
- 世界规则与伏笔窗口
- 线索/伏笔切片

**章节承接摘要**
- `previous chapter`: 上一章余波和交付
- `current chapter`: 当前章写作目标
- `next chapter`: 下一章方向预览

**最小约束原则**
- 只输出"够写当前章"的上下文，避免prompt过长

#### 5. 工作流门禁机制

**项目级gate**
- 检查`positioning.primaryGenre`
- 检查`storyContract.corePromises`
- 检查`emotionalContract.coreEmotion`

**章节级gate**
- 检查`direction`是否存在
- 检查`beats`是否完整
- 检查`scenePlans`是否定义

**上下文gate**
- 校验context lens是否过期（通过章节内容指纹）
- 区分`fresh`/`stale`/`legacy-untracked`状态

#### 6. 文本Provider独立审查

**Clean-room独立编辑模式**
- 独立的HTTP客户端，支持任意OpenAI兼容API
- 通过`TEXT_PROVIDER_API_KEY`/`BASE_URL`环境变量配置
- 支持structured output (`json_object`格式)

**审查流程**
1. 构造独立审查prompt（包含章节全文+style分析+consistency信号）
2. 发送到外部provider
3. 解析返回的JSON对象
4. 归一为`editorPass + editorAssessment` fragment

#### 7. 约束流程总览

```
写作前 → 检查项目gate → 检查章节gate → 构建context lens
        ↓
写作中 → 应用style profile → 应用review rules → 生成文本
        ↓
写作后 → style detector检测 → consistency检查 → story review
        ↓
迭代   → 生成change request → 修正正文 → 重新审查
```

### 约束配置示例

**项目级风格配置** (`style-profiles.yaml`)

```yaml
profiles:
  xuanhuan-zh:
    patternThresholds:
      formulaicTransition: 2.5
    extraPatterns:
      formulaicTransition: ["下一刻", "下一秒", "话音未落"]
    registerPolicy:
      disallowedCategories:
        - id: "modern-planning"
          label: "现代项目管理语汇"
          terms: ["优先级", "框架", "闭环", "底层逻辑"]
          suggestion: "玄幻正文避免使用现代项目管理语汇"
```

**项目级审查规则** (`review-rules.yaml`)

```yaml
activeProfile: "strict"
profiles:
  strict:
    enabledRules:
      - "metaLeakage"
      - "povOverreach"
      - "outlineDeviation"
    exemptions:
      - ruleId: "metaLeakage"
        scope:
          chapterIds: ["chapter-001"]
        reason: "第一章允许元信息泄露"
```

### 关键设计原则

1. **纯函数设计**: services层不修改输入state，返回新dict
2. **状态指纹校验**: 防止旧快照覆盖新状态
3. **根目录级写锁**: 避免多命令同时写同一项目
4. **JSON-compatible YAML**: 所有状态文件必须为合法JSON
5. **分层责任**: protocol层负责状态，services层负责逻辑，commands层负责交互

## 已实现功能

当前实现已经覆盖：

- 分层文件协议：正文、提案、审查、投影、上下文
- 章节分析、建议生成，以及“先审再应用”的显式流程
- 章节评审、场景评审、风格评审，以及 profile 驱动约束
- 风格修复指导，以及 provider-backed 的插图 prompt、dry-run、真实 OpenAI 文生图 / 图生图请求、多资产落盘与资产状态查看
- outline-first gate、beat 跟踪、scene plan 维护、detailed outline 辅助
- project positioning、story contract、emotional contract、story template、commercial serial blueprint 校验
- worldbook / foreshadowing / threads / timeline / causality / structure / character arc 跟踪
- entity enrich、review、list、show、relationship graph 导出
- workflow 阶段推断、`workflow.yaml` 持久化、gate decision、reset/export、`run --resume-from` 回卷
- project stats、跨章节搜索、一致性检查、layered layout 迁移
- `projects/` 下已跟踪的短篇、风格驱动短篇、玄幻短篇、商业长篇样例基线
- provider 能力的可选依赖边界，同时保持 base install 为 stdlib-only

## 后续改进方向

下一轮应继续聚焦几个现实短板：

- 在早期 UI 并行推进的同时，继续提升结构化故事状态的人类审查体验
- 把插图资产管理收敛到 Story Canvas 的视觉界面轨道，而不是继续扩大 `v1.0.x` 的纯 CLI 发布面
- 继续加深 `review` 和 `workflow` 对故事约束的消费，尤其是 worldbook、伏笔回收窗口、动态角色状态
- 扩充题材模板与工作流模板，避免所有小说都套同一套骨架
- 稳定 provider 层，至少补一到两个真实可用集成
- 继续把算法、词典、prompt 资源外部化，同时保留 builtin fallback
- 加强长篇状态下的 schema / workflow 校验，尤其是 graph、thread、structure 语义
- 继续扩充 `projects/` 样例，覆盖更多商业题材和生产流程
- 在命令契约与样例稳定后，再推进 release / distribution

## 开发

同步环境：

```powershell
uv sync
```

运行 smoke tests：

```powershell
uv run python -m unittest discover -s tests
```

对一个故事项目执行结构校验：

```powershell
uv run story-canvas doctor --root .\projects\demo-short-story
```

安装一个宿主 adapter：

```powershell
uv run python scripts/install_adapter.py --host codex --force
uv run python scripts/install_adapter.py --host codex --repo-skill --force
uv run python scripts/install_adapter.py --host claude --workspace <workspace-root> --force
```

其中 `--repo-skill` 会把 Codex skill 部署到当前仓库的 `.codex/skills/<skill-name>`，适合把仓库自带 adapter 直接作为 repo-local skill 使用；`adapters/codex-skill/<skill-name>` 仍然是 source of truth。

一次安装多个 adapter：

```powershell
uv run python scripts/install_adapters.py --workspace <workspace-root> --force
```

贡献与发布相关文档：

- `CONTRIBUTING.md`
- `docs/guides/creative-workflow.md`
- `docs/guides/quickstart.md`
- `docs/guides/sample-matrix.md`
- `docs/guides/releasing.md`

## 路线图

- 稳定 provider-backed 扩展点与 optional dependency 打包边界
- 扩展 `projects/` 下的样例基线，并持续与 smoke coverage 对齐
- 加强 graph、thread、structure、commercial workflow 等 richer schema 的校验
- 用真实长篇项目验证更复杂的生产流程
- 在 Python CLI 契约稳定后，再回头评估发行策略

