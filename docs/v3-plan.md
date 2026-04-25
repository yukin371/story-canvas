# Story Harness CLI v3 Implementation Plan

> 状态：待实现 | 创建：2026-04-25 | 已完成 v2 全书 25 章写作验证
> 本版修订：依赖策略以 `ADR-002 Optional Dependencies and Providers Boundary` 为准

## Context

v2 完成了完整的 25 章小说「归墟」写作循环（三卷均分 ~88/100），验证了核心写作-审查闭环。
v3 聚焦三个方向：**流程强化**、**质量提升**、**视觉扩展**。

本次修订补充一个前提：**v3 不应把所有算法、词表、提示词都继续硬编码在仓库内**。对于重复实现成本高、质量明显受限的部分，采用 `base + extras + packs` 方案，并把 side-effecting client 收敛到 `providers/`。

正式边界见 [ADR-002 Optional Dependencies and Providers Boundary](./adr/ADR-002-optional-dependencies-and-providers.md)。早期讨论保留在 [docs/plans/2026-04-25-v3-dependency-boundary.md](./plans/2026-04-25-v3-dependency-boundary.md)。

---

## Cross-Cutting Design Boundary

### 1. 能力分层

| 层级 | 适用内容 | 依赖策略 | 必须满足 |
|------|----------|----------|----------|
| Core Built-in | CLI、state schema、gate 状态机、基础 heuristics | 保持 stdlib 可运行 | 缺少任何外部依赖时也能工作 |
| Optional Local Packs | 词表、字典、prompt pack、可替换规则集 | 可选安装 / 外部资源包 / 仓库外版本化资源 | 缺失时自动回退到内置最小集 |
| Optional Remote Providers | 图像生成、LLM 评分/分类增强、重型算法外包 | 通过 provider/client 接口接入 | 必须支持 `--dry-run` 或导出请求，不把网络依赖变成核心门禁 |

### 2. 允许外部化的内容

| 类别 | 优先外部化对象 | 内置保留内容 |
|------|----------------|--------------|
| 算法 | 相似度/重复句检测、感官分类、卷级弧线评分增强 | 基础规则、可解释 heuristics、最小可用评分 |
| 字典/词表 | 风格禁忌词、类型词库、视觉元素词典、平台偏好词表 | 回归测试所需最小词表 |
| 提示词 | 插图 prompt 模板、卷级审阅 prompt、风格约束模板 | 离线 `--dry-run` 所需的默认模板 |

### 3. 落地规则

- **base install 仍是当前发布基线**：所有核心命令和离线测试必须继续在 stdlib-only 下可运行。
- **不破坏服务层纯度**：外部 API 调用、资产落盘、provider 鉴权不应放进 `services/`；`services/` 只负责请求构造、结果解释和兜底 heuristics。
- **状态协议不跟随依赖漂移**：`.yaml` 文件结构应与 provider 名称、prompt pack 版本、词表来源解耦，避免未来切换依赖时触发状态迁移风暴。
- **测试必须能离线跑通**：CI 和 smoke test 只能依赖内置 fallback / mock provider，不能要求真实网络调用。

---

## Feature 1: Enhanced Workflow Pipeline (大)

### 流水线定义

```
PRD/项目定位 → 大纲框架 → [GATE: 大纲审阅] → 细纲展开 → 自审评分 → [GATE: 细纲审阅]
→ 章节生成 → 章节评分修正 → 卷完成检查 → 卷级弧线审阅 → [GATE: 导出审阅]
```

### Gate 机制

- CLI 交互式确认（`a`ccept / `m`odify / `r`eject）
- `--non-interactive` 模式打印报告后退出（供 Claude Code/CI 编排）
- `--feedback` 存储修改意见，`--restart-from` 回退重跑

### 卷级弧线审阅（起承转合）

- 分析卷内全部 chapterReviews
- 四维度评分：qi(起)、cheng(承)、zhuan(转)、he(合)，各 20 分
- 生成节奏曲线、线索回收率、角色弧进度
- **基础版** 使用内置启发式评分
- **增强版** 可接入外部 review profile / prompt pack / 算法评分器，但 gate 结果必须保留可解释的 builtin fallback

### 新增文件

| 文件 | 用途 |
|------|------|
| `commands/workflow.py` | CLI 交互（run/status/advance/reset/export） |
| `services/workflow_engine.py` | 流水线状态机、gate 评估 |
| `services/volume_review.py` | 卷级弧线审阅的 builtin 评分与结果结构 |
| `data/workflow_profiles/` | 内置 gate/profile 最小模板；后续可扩展外部 pack |

### 新增状态：`workflow.yaml`

```yaml
currentStage: "outline_review"
gateHistory: [{gateId, decision, feedback, timestamp}]
stageResults: {stage_id: {completed, score, profile, ...}}
```

### CLI 命令

```
workflow run        --root <path> [--resume-from <stage>] [--non-interactive]
workflow status     --root <path>
workflow advance    --root <path> --gate <id> --decision <accept|modify|reject> [--feedback <text>]
workflow reset      --root <path> [--from-gate <stage>]
workflow export     --root <path> [-o <path>]
```

---

## Feature 2: Style Analysis Pipeline (中)

### 检测 7 种 AI 典型模式

| 模式 | 基础检测方法 | 阈值 |
|------|--------------|------|
| 比喻密度 | `像...一样` / `宛如` / `仿佛` 频率 | >3次/千字 |
| 模糊副词 | 微微/缓缓/不禁/默默/淡淡 等 | >5次/千字 |
| 叙述性情感 | `感到悲伤` / `心中涌起` / `一股...袭来` | >2次/千字 |
| 程式化过渡 | 然而/与此同时/就在这时 | >2次/千字 |
| 句式重复 | 连续段落开头结构相似 | ≥3段连续 |
| 感官单一 | 视觉/听觉/触觉/嗅觉/味觉分布 | 缺失≥2类 |
| 段落均质 | 段落长度标准差/均值比 | <0.3 |

### 检测架构

- **Builtin detector**：处理频次统计、长度分布、显式词表匹配，确保离线可运行
- **Optional algorithm lane**：句式相似、重复表达聚类、感官分类等高重复实现成本能力允许接第三方库或远端模型
- **Optional dictionary lane**：类型化禁忌词、平台风格词表、感官词典、套话黑名单可用外部 pack 维护，避免持续把大词表塞回 `utils/text.py`
- `styleAnalysis` 中应记录 `source: builtin | optional-pack | provider`，便于解释和回归比较
- AI 检测不是只在成文后打分，而是要进入“生成时约束 + 生成后检测 + 超阈值修复”的闭环

### 集成方式

- **不新增评审维度**，作为 `proseControl` 的子分析
- 从 proseControl 20 分中扣除 0-6 分
- 审查结果中增加 `styleAnalysis` 字段，含具体证据、来源和修改建议

### 协作闭环

```text
style profile / prompt pack
  -> style constraints
  -> draft prompt / chapter write
  -> style check
  -> review chapter(styleAnalysis)
  -> style repair
  -> 复检或通过
```

### 当前实现口径

- [x] `services/style_detector.py` — builtin baseline（7 类模式的最小可用检测）
- [x] `commands/style.py` — `style check/constraints/report` CLI 命令
- [x] `services/story_review.py` — `_score_prose_control` 已集成 `style_detector`
- [x] `protocol/style_profiles.py` — builtin + project `style-profiles.yaml` 加载与自动选型

### 待完成

- [ ] `commands/style.py` — 新增 `style repair`，输出结构化修复方案或变更请求草案
- [ ] 为 style 分析引入 external lexicon / prompt pack 的加载口径
- [ ] adapter / workflow 侧把 `style constraints` 自动注入 draft prompt，而不是只让用户手工调用
- [ ] 明确 `style repair` 与 `chapter suggest` / `review apply` 的边界，避免两套改稿建议重复实现

### CLI 命令

```
style check        --root <path> [--chapter-id <id>] [--profile <name>]
style constraints  --root <path> [--chapter-id <id>] [--profile <name>]
style report       --root <path> [--volume-id <id>] [-o <path>] [--profile <name>]
style repair       --root <path> --chapter-id <id> [--profile <name>] [--format <prompt|change-requests>]
```

---

## Feature 3: AI Illustration (中-大)

### 设计目标

- 图像生成天然属于外部 provider 能力，不应把 provider SDK / HTTP 调用与 prompt 逻辑混成一个模块
- 提示词模板和视觉词典应支持外部 pack，避免在仓库内重复维护大量风格词、镜头词、服饰词和平台特化 prompt
- 必须同时覆盖文生图（`text-to-image`）与图生图（`image-to-image`），而不是只做单向 prompt 出图
- model id 不能写死在协议里；当前用户环境可使用 `gpt-image-2`，但 schema 应允许任意 provider model 字符串

### Provider / Prompt 边界

```python
class PromptPack(Protocol):
    def build_character_prompt(self, entity, *, profile) -> dict: ...
    def build_chapter_prompt(self, chapter, analysis, *, profile) -> dict: ...

class ImageProviderClient(Protocol):
    def generate_image(self, request: dict) -> dict: ...
```

- `services/` 负责从 `entities.yaml` / chapter analysis 生成 prompt request 和 fallback 模板
- provider 调用、鉴权、下载、文件写入属于 side-effecting client，不能和纯 service 混放
- side-effecting client 的 canonical owner 为 `src/story_harness_cli/providers/`

### OpenAI 方向

- OpenAI adapter 默认支持传入任意 model 字符串，优先兼容当前环境可用的 `gpt-image-2`
- 若部署环境只提供其他 GPT Image 家族 model，也应通过 `illustration config --set-model` 切换，而不是改协议
- 若继续保持仓库零依赖，则可使用 stdlib `urllib.request` 走 HTTP
- 若后续允许可选 provider SDK，也应保持为 optional dependency，不得影响 `illustration prompt --dry-run`

### 当前实现口径

- [x] `providers/image/openai_http.py` — OpenAI image provider 的最小 stdlib HTTP client 骨架

### 待完成

- [ ] `services/illustration_prompting.py` — prompt request 构造、视觉要素提取、reference 组装
- [ ] `commands/illustration.py` — `prompt/generate/list/config`
- [ ] `protocol/schema.py` / `protocol/state.py` — `illustrations.yaml`
- [ ] provider request schema 明确 `text-to-image` / `image-to-image` 双模式

### 角色设定图流程

```
entities.yaml appearance → extract_character_visual() → PromptPack → ImageProviderClient → 存储到 assets/
```

### 章节插图流程

```
chapter 高潮场景 → generate_chapter_illustration_prompt() → PromptPack → ImageProviderClient → 存储到 assets/
```

### 新增文件

| 文件 | 用途 |
|------|------|
| `services/illustration_prompting.py` | 提示词构造、视觉要素提取、fallback 模板 |
| `providers/image/openai_http.py` | OpenAI image provider 的 stdlib HTTP 实现 |
| `commands/illustration.py` | generate/prompt/list/config + side-effect 协调 |
| `data/prompt_packs/illustration/` | 内置默认 prompt pack |
| `data/visual_lexicons/` | 内置最小视觉词典；可扩展外部 pack |

### 新增状态：`illustrations.yaml`

```yaml
adapter: {name: openai, model: "gpt-image-2", defaultSize: "1024x1024", quality: standard}
promptPack: {name: default, version: "builtin"}
generated: [{id, type, mode, chapterId, entityId, promptText, revisedPrompt, inputImages, maskPath, filePath, artifacts, metadata, generatedAt}]
```

### 存储布局

```
<project>/assets/illustrations/
  chapter-005_climax.png
  char-shen-xuan_reference.png
```

### CLI 命令

```
illustration generate  --root <path> (--chapter-id | --entity-id) --mode <text-to-image|image-to-image> [--input-image <path> ...] [--mask <path>] [--dry-run] [--prompt-pack <name>]
illustration prompt    --root <path> (--chapter-id | --entity-id) --mode <text-to-image|image-to-image> [--input-image <path> ...] [--mask <path>] [--prompt-pack <name>]
illustration list      --root <path>
illustration config    --root <path> --set-adapter/--set-model/--show
```

---

## Shared Changes (all features)

### `protocol/schema.py` — 新增 state domains

- `workflow_progress`: 流水线进度追踪
- `illustrations`: 插图配置和生成记录

### `protocol/state.py` — STATE_KEY_MAP + STATE_FILE_NAMES

- `"workflow_progress": "workflow.yaml"`
- `"illustrations": "illustrations.yaml"`

### `cli.py` + `commands/__init__.py` — 注册新命令组

- `register_workflow_commands`
- `register_style_commands`
- `register_illustration_commands`

### 资源加载约束

- 可选词表 / prompt pack 必须有 builtin 默认值
- review 结果中需要保留 profile / pack / provider 元数据，便于回放和 A/B 比较
- 不允许把大体量词表和 prompt 常量继续无限制塞入单个 `utils/text.py`

---

## Implementation Order

1. **Feature 2: Style Analysis Pipeline** — 中，无新状态域，先完成 builtin baseline，再补可选 profile/lexicon lane
2. **Feature 1: Workflow Pipeline** — 大，需要新状态域 + 卷级审阅；增强评分器保持为 optional lane
3. **Feature 3: Illustration** — 中-大，默认先打通 prompt + dry-run，再接真实 provider

---

## Verification

每个 feature 完成后：

1. `uv run python -m unittest discover -s tests` — 全量回归
2. 对 demo-guixu 运行新命令验证真实数据
3. 检查旧项目向后兼容（加载无 `workflow.yaml` / `illustrations.yaml` 的项目不报错）
4. Feature 2: 对已写 ch1-25 运行 `style check`，分别验证 builtin 与 optional profile 输出
5. Feature 3: `--dry-run` 模式验证 prompt pack 与视觉词典输出，provider 层用 mock 测试
6. 断网或缺失 optional dependency 时，命令应清晰回退，而不是直接崩溃
