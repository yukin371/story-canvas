# Workflow 设计现状与缺口整理

> 历史状态: 2026-04-29 起降级为 `historical-source`
> 说明: 本文记录的“缺少显式 workflow 命令组 / `workflow.yaml` / 卷级 gate”等核心缺口已经进入主仓库实现。后续活跃 AI 实施痛点请改查 `docs/tracking/ai-friction-tracker.md`。

> 日期: 2026-04-25
> 状态: Historical source
> 目的: 把仓库内已经存在的 workflow 相关设计、实现和缺口收敛成单一入口，避免后续继续重复设计第二套方案

## 1. 结论

当前仓库已经有两层 workflow：

1. **已实现的命令式创作闭环**
   - 以 `init -> outline check -> chapter analyze -> chapter suggest -> review apply -> projection apply -> context refresh -> review chapter -> review scene -> export` 为主
   - 已有 guide、adapter、sample baseline 和 smoke test 支撑
2. **未实现的显式状态机 workflow**
   - 目标是新增 `workflow run/status/advance/reset/export`
   - 以 `workflow.yaml`、gate history、stage results 和 volume review 为核心
   - 目前只存在设计，没有代码落地

因此，仓库并不是“没有 workflow 设计”，而是：

- **workflow as guide / discipline**：已经存在并且可用
- **workflow as first-class command group / state machine**：已经设计但尚未实现

后续如果继续推进，不应该重新发明一套新流程，而应该在现有 `docs/v3-plan.md` 的设计线上补完命令与状态域。

## 2. 现有设计入口

### 2.1 Canonical guide

- `docs/guides/creative-workflow.md`

当前 canonical workflow 已经明确：

- 先项目定位与 story contract
- 再 outline / beats / scenePlans
- 通过 `outline check` 后再写正文
- 写后走 analyze / suggest / apply / projection / context / review / export

这份 guide 已经承担“作者 / 外部 AI 如何跑完整闭环”的职责。

### 2.2 v3 设计文档

- `docs/v3-plan.md`

这里已经定义了显式 workflow pipeline 的设计目标，包括：

- `commands/workflow.py`
- `services/workflow_engine.py`
- `services/volume_review.py`
- `data/workflow_profiles/`
- `workflow.yaml`
- `workflow run/status/advance/reset/export`

这说明“把 workflow 提升为显式状态机和命令组”已经不是想法，而是已有设计稿。

### 2.3 Skill / adapter 定位

- `docs/guides/migrate-from-skill-prototype.md`
- `adapters/codex-skill/story-harness-writing/SKILL.md`
- `adapters/claude-code/story-harness-writing/SKILL.md`

这些文档已经明确迁移方向：

- 协议和命令 contract 留在主仓库
- skill 最终只保留为薄适配层
- adapter 的职责是“触发正确 workflow”，不是维护第二套协议

### 2.4 已有工程化验证

- `tests/smoke/test_demo_short_story_sample.py`
- `tests/smoke/test_demo_light_novel_short_sample.py`
- `tests/smoke/test_demo_xuanhuan_short_sample.py`
- `tests/smoke/test_demo_urban_occult_long_sample.py`
- `tests/smoke/test_layered_full_loop.py`

这些 smoke test 证明：命令式闭环和 layered layout 已经可以作为 workflow baseline 被回归验证。

## 3. 已经实现的 workflow 能力

### 3.1 手工驱动闭环已完整

当前 CLI 已经能支持：

- 项目初始化
- 项目契约与商业连载蓝图
- outline-first gate
- beat / scenePlans 维护
- 章节分析、建议、变更决策、投影更新、context refresh
- chapter / scene review
- stats / doctor / export

这意味着“workflow”在操作层面并不缺失，只是还没有被统一包装成一个显式状态机入口。

### 3.2 layered layout 已为 workflow state 预留土壤

`tests/smoke/test_layered_full_loop.py` 已经覆盖：

- layered project 初始化
- `spec/` 与 root workflow 目录分层
- 章节分析、review、doctor、export、foreshadow

这说明：

- 项目文件组织已经具备承载更多 workflow 中间状态的条件
- 后续新增 `workflow.yaml` 并不需要推翻当前协议，只需要扩域

### 3.3 style / provider 设计已形成相邻先例

`docs/v3-plan.md` 中 style、provider、packs 的思路已经部分落地。这给 workflow 后续实现提供了两个直接约束：

- workflow profile 应该走 builtin + optional pack 路线
- workflow engine 不应直接耦合 provider 或宿主 skill

## 4. 当前缺口

### 4.1 缺少正式的 `workflow` 命令组

当前 `src/story_harness_cli/cli.py` 和 `src/story_harness_cli/commands/__init__.py` 中：

- 没有 `register_workflow_commands`
- 没有 `commands/workflow.py`

结果是：

- workflow 只能由用户或 adapter 手工拼命令驱动
- 无法通过统一命令查询“当前阶段在哪、下一步该做什么”

### 4.2 缺少显式状态文件 `workflow.yaml`

`docs/v3-plan.md` 里已经定义：

- `currentStage`
- `gateHistory`
- `stageResults`

但当前协议层还没有：

- `workflow_progress` state domain
- `workflow.yaml` 文件映射
- 相关 schema 默认值

结果是：

- 当前 workflow 的阶段信息散落在已有文件中，难以统一 resume / report / export

### 4.3 缺少 workflow state machine service

当前服务层没有：

- `services/workflow_engine.py`
- gate evaluation orchestration
- stage transition 逻辑

结果是：

- `creative-workflow.md` 只是人工遵循的文档，不是系统可执行的状态机

### 4.4 缺少卷级 review 聚合能力

`docs/v3-plan.md` 设计了 volume review，但当前没有：

- `services/volume_review.py`
- 卷级节奏 / 起承转合聚合评分
- workflow gate 对卷级结果的消费

结果是：

- 商业长篇项目已有 chapter / scene review，但缺少更高层的 volume gate

### 4.5 adapter 还没有接到显式 workflow API

当前 Codex / Claude adapter 已经是薄适配，但它们仍然主要依赖：

- 文字化 guide
- 手工命令链

而不是：

- `workflow status`
- `workflow run --non-interactive`
- `workflow advance --decision ...`

这会让宿主侧继续保留较多“编排责任”。

## 5. 与 `chinese-novelist-skill` 的关系

`E:/Github/chinese-novelist-skill` 最值得借鉴的不是它的目录协议，而是它对 workflow 的上层编排：

- 阶段化设计
- 中断续写
- 写作模式选择
- 自动校验与修复

这些内容与当前仓库的关系应当是：

- **借鉴其编排思路**
- **落到本仓库既有协议和命令体系**
- **不要把它的 `00-大纲.md` / `03-写作计划.json` 目录约定直接搬进来**

也就是说，后续如果做 workflow：

- `workflow.yaml` 应承接它的“写作计划 / 进度跟踪”职责
- adapter 应吸收它的宿主交互体验
- 协议仍以 `story-harness-cli` 当前 layered layout 为准

## 6. 建议实施顺序

### 6.1 第一阶段：最小可用 workflow state

目标：

- 不改现有闭环命令语义
- 先新增显式 workflow 状态

建议实现：

- `protocol/schema.py` 增加 `workflow_progress`
- `protocol/state.py` 映射 `workflow.yaml`
- `commands/workflow.py` 先实现 `status` / `run`
- `services/workflow_engine.py` 先做 stage inference 和 next-step recommendation

首轮不要做：

- 自动重写
- 宿主并行模式
- 远端 provider 依赖

### 6.2 第二阶段：gate decision 与 reset

目标：

- 让 workflow 从“只读状态查询”升级为“可推进状态机”

建议实现：

- `workflow advance`
- `workflow reset`
- `gateHistory` 持久化
- `--non-interactive` 报告输出

### 6.3 第三阶段：volume review 与 profile

目标：

- 补上商业长篇真正需要的卷级 gate

建议实现：

- `services/volume_review.py`
- `data/workflow_profiles/`
- builtin profile + optional pack 加载

### 6.4 第四阶段：adapter 对接

目标：

- 让 Codex / Claude adapter 从“命令脚本助手”变成“workflow front-end”

建议实现：

- adapter 改用 `workflow status/run/advance`
- 仅保留少量 fallback 命令说明

## 7. 推荐的最小实施切片

如果只做一个最小切片，建议是：

1. 新增 `workflow.yaml`
2. 新增 `workflow status`
3. 新增 `workflow run --non-interactive`
4. 只覆盖以下阶段：
   - `project_contract`
   - `outline_ready`
   - `chapter_review_ready`
   - `scene_review_ready`
   - `export_ready`

这样可以先把现有人工闭环“显式化”，而不是一开始就做成复杂 orchestration engine。

## 8. 验证建议

后续真正开始实现 workflow 命令时，至少应补以下验证：

1. `tests/smoke/test_workflow_status.py`
   - 无 `workflow.yaml` 的旧项目应自动推断状态或优雅回退
2. `tests/smoke/test_workflow_run_non_interactive.py`
   - 对 demo 项目输出当前 gate 报告
3. `tests/smoke/test_workflow_advance.py`
   - gate decision 能正确写入 `workflow.yaml`
4. 扩展 `tests/smoke/test_demo_urban_occult_long_sample.py`
   - 验证商业长篇项目的 workflow stage 与 volume-ready 条件

## 9. 当前建议

当前建议不是“再写一份新的 workflow 方案”，而是：

1. 以 `docs/v3-plan.md` 为唯一 workflow 实现蓝图
2. 以 `docs/guides/creative-workflow.md` 为当前人工闭环 canonical guide
3. 以后续 `workflow` 命令组把两者接起来

这样可以避免：

- guide 一套
- skill 一套
- v3 plan 一套
- 实际 CLI 又一套

这也是本次整理的核心目的。
