# 2026-04-29 从零起卷级创作前的风险收口

## 背景

上一轮实跑已经补齐了项目初始化与章节起步链路，但要从零开始完整写出一卷并进入第二轮审查，仍有几处真实风险会拖慢 agent / CLI 协同：

1. `chapter suggest` 在常见首章场景里容易返回 `created: 0`，缺少解释与后续指引。
2. `outline scene-detect` 对自然 prose 的切分偏保守，容易把多个推进段压成一个 scene。
3. chapter workflow 目前虽然已纳入 `context refresh`，但仍需要进一步确认“建议链路”和“第二轮审查前命令链”是否足够清晰。

## 适用规则

- 当前执行入口：`docs/roadmap.md`
- 架构护栏：
  - CLI 编排与文件 I/O 归 `commands/`
  - 纯检测/纯推断逻辑归 `services/`
  - 不引入新的并行真相源
- 目标模块不变量：
  - `commands/` 负责可执行命令建议与状态聚合输出
  - `services/` 不做文件 I/O
  - `workflow_engine` 的 gate 与 rule semantics 要保持统一
- 兼容性约束：
  - 不能破坏现有 CLI 参数
  - 输出字段新增应尽量增量兼容
  - `.yaml` 仍必须保持 JSON-compatible

## 目标模块

- `src/story_harness_cli/commands/chapter.py`
- `src/story_harness_cli/commands/outline.py`
- `src/story_harness_cli/commands/status.py`
- `src/story_harness_cli/services/change_requests.py`
- `src/story_harness_cli/services/story_review.py`
- `src/story_harness_cli/services/workflow_engine.py`
- 对应 smoke tests 与必要文档

## 计划改动

1. 给 `chapter suggest` 增加“无结构化 change request 时的解释与后续动作”，避免命令看起来像空操作。
2. 强化 `scene-detect` 的保守切分启发式，优先覆盖明显场景位移 / 到场 / 转场信号。
3. 用真实 temp project 和定向 smoke test 验证第二轮审查前链路是否顺畅，并同步文档口径。

## 验证方式

1. 定向 smoke tests：
   - `tests.smoke.test_outline_loop`
   - `tests.smoke.test_status_command`
   - `tests.smoke.test_workflow_command`
   - 如涉及 `chapter suggest`，补相应 smoke test
2. 用临时项目串行实跑：
   - `init -> status -> structure/scaffold -> 写正文 -> scene-detect -> analyze -> suggest -> projection/context/review -> workflow/status`
3. 必要时再跑全量 smoke，至少确认本轮改动未引入新的 workflow/outline 回归。

## 需要同步的文档

- `src/story_harness_cli/commands/MODULE.md`
- 需要时同步 `docs/guides/creative-workflow.md` / `quickstart.md`

## 架构风险

- 若把建议逻辑直接塞进 `commands/` 但不沉到 `services/`，容易形成平行规则。
- 若 scene 切分规则放宽过头，会把单场景误拆成多场景，影响后续 review scene。

## 重复实现风险

- 不能在 skill / guide 文本里发明一套与 CLI 输出不同的“第二轮审查前步骤”。
- 不能在 `status` 和 `workflow` 各自维护不同的“当前应做什么”判断。

## 回滚路径

- 本轮尽量保持增量改动；若新 heuristics 误报，可单独回退 `scene-detect` 的新增 break 规则。
