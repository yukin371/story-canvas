# Story Harness CLI 项目画像

> 最后更新: 2026-04-25
> 事实来源: `README.md`、`pyproject.toml`、入口代码、测试目录
> 说明: 只记录高置信度事实；未确认项标记为 `TBD`

## 1. 项目类型

- 主语言: Python 3.10+
- 仓库类型: CLI 工具（单包）
- 当前主线: `main`
- 主模块: `src/story_harness_cli/`

## 2. 当前定位

Agent-native 小说创作工作流 CLI。将长篇小说的创作状态拆分为结构化文件层（proposals / reviews / projections / context），让 AI agent 和作者在明确的约束下协作，减少设定漂移和状态丢失。当前协议已覆盖基础定位层、故事契约、情绪契约、题材模板与商业连载蓝图，并开始把世界约束、伏笔账本和写作上下文接入实际命令消费，但整体仍处于早期功能积累阶段。

## 3. 运行与构建入口

- 主程序入口: `src/story_harness_cli/main.py` → `story_harness_cli.cli:main`
- 构建系统: hatchling (`pyproject.toml`)
- 本地运行方式: `PYTHONPATH=src python -m story_harness_cli <command>` 或 `pip install -e .` 后 `story-harness <command>`
- 关键命令矩阵:

| 命令 | 子命令 | 用途 |
|------|--------|------|
| `init` | — | 初始化项目 |
| `brainstorm` | `character` / `world` / `outline` | 灵感生成 |
| `outline` | `propose` / `promote` / `check` / `beat-add` / `beat-complete` / `beat-list` / `scene-add` / `scene-list` / `scene-detect` / `scene-update` / `scene-remove` | 大纲管理、严格写作前门禁与章节场景维护（默认检查 project positioning / storyContract + direction / beats / scenePlans） |
| `chapter` | `analyze` / `suggest` | 章节分析与细化建议生成（`suggest` 默认要求先通过严格 outline-first 门禁） |
| `review` | `apply` / `chapter` / `scene` | 审核变更请求 / 生成章节与一幕回顾评分（含类型/平台加权、契约对齐、商业对齐） |
| `projection` | `apply` | 应用投影 |
| `context` | `refresh` / `show` | 写作上下文 |
| `entity` | `enrich` / `review` / `list` / `show` | 角色管理 |
| `style` | `check` / `constraints` / `report` / `repair` | AI 风格模式检测、约束生成、聚合报告与修复建议生成 |
| `illustration` | `prompt` / `generate` / `list` / `config` | 插图 prompt 构造、文生图/图生图 provider 请求、批量资产落盘与生成记录查看 |
| `workflow` | `status` / `run` / `advance` / `reset` / `export` | workflow 状态机：推断当前 gate、持久化到 `workflow.yaml`、记录 `accept/modify/reject` 决策，并支持 `run --resume-from` 回卷与快照导出 |
| `consistency` | `check` | 一致性校验 |
| `stats` | — | 项目统计 |
| `export` | — | 导出纯文本 |
| `doctor` | — | 项目校验（含 style profile、商业蓝图、插图资产引用与落盘状态检查） |

## 4. 技术栈

- 运行时: Python 3.10+（base install 保持 stdlib-only；增强能力允许通过 optional dependencies 接入，见 `docs/adr/ADR-002-optional-dependencies-and-providers.md`）
- 框架: argparse（子命令路由）
- 持久化: JSON-compatible YAML 文件（`.yaml` 后缀，内容为合法 JSON）
- 可选项目配置: `keywords.yaml`、`style-profiles.yaml`
- 测试框架: unittest（stdlib）
- CI 平台: GitHub Actions

## 5. 当前验证基线

- Lint: `ruff format --check src/ tests/` + `ruff check src/ tests/`
- Test: `PYTHONPATH=src python -m unittest discover -s tests`
- Build: `pip install -e .`（需 hatchling）或 `uv sync`
- Security: TBD
- Release: TBD

## 6. 仓库拓扑

- `src/story_harness_cli/commands/`: CLI 子命令实现（每个命令一个模块）
- `src/story_harness_cli/services/`: 业务逻辑层（分析、投影、一致性等）
- `src/story_harness_cli/providers/`: 外部 API、SDK 与 optional dependency wrapper
- `src/story_harness_cli/protocol/`: 状态加载/保存、文件路径、schema 默认值
- `src/story_harness_cli/utils/`: 通用工具（哈希、时间、文本处理）
- `src/story_harness_cli/data/`: 创作数据表（角色原型、世界元素、中文姓名等）
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
- 报告 / issue / archive 入口: `docs/plans/`、`docs/releases/`
- hooks / commit policy / CI governance: `.github/workflows/ci.yml`、`docs/COMMIT_POLICY.md`、`docs/ENGINEERING_GOVERNANCE.md`

## 8. 已知高风险区域

- `protocol/state.py` 的 `_sync_outline()`: volumes 与 flat chapters 的同步逻辑，直接影响大纲一致性
- `services/analyzer.py`: 实体识别逻辑（`@{名称}` vs `@名称`），影响后续所有分析
- `utils/text.py`: 关键词表（STATE_KEYWORDS / APPEARANCE_KEYWORDS / ABILITY_KEYWORDS），硬编码中文关键词
- `services/entity_enricher.py`: 跨段落实体归属问题（已知 bug：多实体同段落时属性可能错配）

## 9. 缺失或待确认项

- 发布流程: TBD（确认路径：PyPI 发布 + 版本策略）
- 适配器安装脚本的实际使用情况: TBD
- Security 基线与权限模型: TBD
