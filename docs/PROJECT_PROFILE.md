# Story Canvas 项目画像

> 最后更新: 2026-04-27
> 事实来源: `README.md`、`pyproject.toml`、入口代码、测试目录
> 说明: 只记录高置信度事实；未确认项标记为 `TBD`

## 1. 项目类型

- 主语言: Python 3.10+
- 仓库类型: 故事与视觉工作流产品仓库（Python 工作流内核 + 早期 SPA UI）
- 当前主线: `main`
- 对外主模块: `src/story_canvas/`
- 内部实现 owner: `src/story_harness_cli/`

## 2. 当前定位

Story Canvas 当前是一个 Agent-native 的故事与视觉工作流产品，当前以 `story-canvas` 作为主命令入口，并开始提供单页 UI 作为视觉壳。它将长篇小说与相关视觉资产的创作状态拆分为结构化文件层（proposals / reviews / projections / context / illustration records），让 AI agent 和作者在明确约束下协作，减少设定漂移和状态丢失。当前协议已覆盖基础定位层、故事契约、情绪契约、题材模板、商业连载蓝图，以及 provider-backed 插画生成链路；UI 层复用同一文件协议，不引入新的真相源。

## 3. 运行与构建入口

- 主程序入口: `src/story_canvas/main.py` → `story_canvas.cli:main` → `story_harness_cli.cli:main`
- 构建系统: hatchling (`pyproject.toml`)
- 安装分发名: `story-canvas`
- 本地运行方式: `PYTHONPATH=src python -m story_canvas <command>` 或 `pip install -e .` 后 `story-canvas <command>`
- 兼容入口: `PYTHONPATH=src python -m story_harness_cli <command>` 与 `story-harness <command>` 暂时保留
- 关键命令矩阵:

| 命令 | 子命令 | 用途 |
|------|--------|------|
| `init` | — | 初始化项目 |
| `brainstorm` | `character` / `world` / `outline` | 灵感生成 |
| `outline` | `propose` / `promote` / `check` / `beat-add` / `beat-complete` / `beat-list` / `scene-add` / `scene-list` / `scene-detect` / `scene-update` / `scene-remove` / `scene-sync` | 大纲管理、严格写作前门禁与章节场景维护（默认检查 project positioning / storyContract + direction / beats / scenePlans，并支持 scenePlans 边界校验/回填） |
| `chapter` | `create` / `analyze` / `suggest` | 新章创建、章节分析与细化建议生成（`suggest` 默认要求先通过严格 outline-first 门禁） |
| `status` | — | 聚合项目、当前卷/章、context、review、consistency 与 workflow 状态，减少直接翻协议文件 |
| `review` | `apply` / `chapter` / `scene` / `preflight` / `volume-self-template` / `volume-self` | 审核变更请求、生成章节与一幕回顾评分、聚合章节/卷级预检，生成卷级 AI 自审模板，并持久化卷级 AI 自审结果 |
| `projection` | `apply` | 应用投影 |
| `context` | `refresh` / `show` | 写作上下文 |
| `foreshadow` | `plant` / `resolve` / `list` / `check` | 伏笔台账与到窗/逾期检查 |
| `entity` | `add` / `state-update` / `mention-adopt` / `mention-plan` / `mention-apply` / `mention-tag-apply` / `enrich` / `review` / `list` / `show` / `mention-check` | 角色建档、状态维护，以及章节/卷级实体 mention 覆盖检查与预览 |
| `world` | `list` / `add` / `mention-adopt` / `progression-add` / `progression-stage-add` / `check` | worldbook 浏览与显式维护、核心概念 onboarding、势力层级与战力尺度审查 |
| `style` | `check` / `constraints` / `report` / `repair` | AI 风格模式检测、约束生成、聚合报告与修复建议生成 |
| `illustration` | `prompt` / `generate` / `list` / `config` | 插图 prompt 构造、文生图/图生图 provider 请求、批量资产落盘与生成记录查看 |
| `workflow` | `status` / `run` / `advance` / `reset` / `export` | workflow 状态机：推断当前 gate、持久化到 `workflow.yaml`、记录 `accept/modify/reject` 决策，并支持 `run --resume-from` 回卷与快照导出 |
| `consistency` | `check` | 一致性校验 |
| `stats` | — | 项目统计 |
| `export` | — | 导出纯文本、按卷导出与审查包导出（支持 `--volume-id`） |
| `doctor` | — | 项目校验（含 style profile、商业蓝图、插图资产引用与落盘状态检查） |

## 4. 技术栈

- 运行时: Python 3.10+（base install 保持 stdlib-only；增强能力允许通过 optional dependencies 接入，见 `docs/adr/ADR-002-optional-dependencies-and-providers.md`）
- 框架: argparse（子命令路由）
- UI: Vue 3 + Vite + TDesign Vue Next（`ui/`，当前为单页应用视觉壳）
- 持久化: JSON-compatible YAML 文件（`.yaml` 后缀，内容为合法 JSON）
- 可选项目配置: `keywords.yaml`、`style-profiles.yaml`、`review-rules.yaml`
- 可选增强依赖: `rapidfuzz`、`sentence-transformers`（`embedding-local`）、`openai`
- 测试框架: unittest（stdlib）
- CI 平台: GitHub Actions

## 5. 当前验证基线

- Lint: `ruff format --check src/ tests/` + `ruff check src/ tests/`
- Test: `PYTHONPATH=src python -m unittest discover -s tests`
- Build: `pip install -e .`（需 hatchling）或 `uv sync`
- Security: TBD
- Release: TBD

## 6. 仓库拓扑

- `src/story_canvas/`: 对外 Python 模块与主 CLI 入口包装
- `src/story_harness_cli/commands/`: CLI 子命令实现（每个命令一个模块）
- `src/story_harness_cli/services/`: 业务逻辑层（分析、投影、一致性等）
- `src/story_harness_cli/providers/`: 外部 API、SDK 与 optional dependency wrapper
- `src/story_harness_cli/protocol/`: 状态加载/保存、文件路径、schema 默认值
- `src/story_harness_cli/utils/`: 通用工具（哈希、时间、文本处理）
- `src/story_harness_cli/data/`: 创作数据表（角色原型、世界元素、中文姓名等）
- `ui/`: 单页 UI 壳，与 CLI 共享协议层与 provider 能力
- `tests/smoke/`: 冒烟测试
- `tests/fixtures/minimal_project/`: 最小测试 fixture
- `projects/demo-novel/`: 长篇样例工程
- `projects/demo-short-story/`: 短篇端到端验证样例工程
- `projects/demo-light-novel-short/`: 风格驱动短篇样例工程（西幻轻小说）
- `projects/demo-xuanhuan-short/`: 风格驱动短篇样例工程（玄幻网文）
- `projects/demo-urban-occult-long/`: 商业化网站连载长篇样例工程（都市玄幻 / 民俗志怪 / 职业线）
- `docs/`: 文档与模板
- `adapters/`: 宿主适配器（Codex、Claude Code 等）
- `scripts/`: 安装脚本

## 7. 现有治理骨架

- 当前执行入口: `docs/roadmap.md`
- 架构护栏: `docs/ARCHITECTURE_GUARDRAILS.md`
- ADR: `docs/adr/ADR-001-json-compatible-yaml.md`、`docs/adr/ADR-002-optional-dependencies-and-providers.md`
- 模块文档规范: `src/story_harness_cli/commands/MODULE.md`、`src/story_harness_cli/services/MODULE.md`、`src/story_harness_cli/protocol/MODULE.md`
- UI 模块文档: `ui/MODULE.md`
- 报告 / issue / archive 入口: `docs/plans/`、`docs/tracking/`、`docs/releases/`
- hooks / commit policy / CI governance: `.github/workflows/ci.yml`、`docs/COMMIT_POLICY.md`、`docs/ENGINEERING_GOVERNANCE.md`

## 7.1 命名迁移说明

- 产品名: `Story Canvas`
- 仓库名: `story-canvas`
- 主 CLI 命令: `story-canvas`
- 主 Python 模块: `story_canvas`
- 兼容 CLI 命令: `story-harness`
- 兼容 Python 模块: `story_harness_cli`
- 当前不做内部源码树整体迁移；实现 owner 仍在 `src/story_harness_cli/`

## 8. 已知高风险区域

- `protocol/state.py` 的 `_sync_outline()`: volumes 与 flat chapters 的同步逻辑，直接影响大纲一致性
- `services/analyzer.py`: 实体识别逻辑（`@{名称}` vs `@名称`），影响后续所有分析
- `utils/text.py`: 关键词表（STATE_KEYWORDS / APPEARANCE_KEYWORDS / ABILITY_KEYWORDS），硬编码中文关键词
- `services/entity_enricher.py`: 跨段落实体归属问题（已知 bug：多实体同段落时属性可能错配）

## 9. 缺失或待确认项

- 发布流程: TBD（确认路径：PyPI 发布 + 版本策略）
- 适配器安装脚本的实际使用情况: TBD
- Security 基线与权限模型: TBD
