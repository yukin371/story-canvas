# 卷级自审独立编辑审查与三段式归因优化计划

> 日期: 2026-04-28
> 状态: 执行中
> 关联入口: `docs/roadmap.md`
> 关联模块:
> - `docs/guides/volume-self-review.md`
> - `src/story_harness_cli/services/volume_self_review.py`
> - `src/story_harness_cli/commands/review.py`
> - `adapters/codex-skill/story-harness-writing/SKILL.md`
> - `adapters/claude-code/story-harness-writing/SKILL.md`

## 1. 目标模块

- 卷级 AI 自审 guide / template / normalize 流程
- 宿主 adapter 的写作与审查 skill
- 相关 smoke tests

## 2. 现有 owner

- 卷级自审模板与归一化 owner: `src/story_harness_cli/services/volume_self_review.py`
- 卷级自审命令编排 owner: `src/story_harness_cli/commands/review.py`
- adapter 真相源 owner: `adapters/codex-skill/story-harness-writing/`、`adapters/claude-code/story-harness-writing/`
- 流程文档 owner: `docs/guides/volume-self-review.md`

## 3. 影响面

- `review volume-self-template`
- `review volume-self`
- `status --volume-id`
- `workflow status/export --volume-id`
- 外部 agent 的卷级审查执行方式
- 现有小说工程的卷级缺陷归因与样例回灌

## 4. 适用规则

- 当前唯一执行入口以 `docs/roadmap.md` 为准，卷级闭环必须区分“AI 自审 -> 修正 -> 复检 -> 人工审查”。
- 服务层保持纯函数，不引入文件 I/O 或外部依赖。
- `review volume-self` 已是 repo-native 的卷级 AI 自审写入口，本轮只扩展既有结构，不新建平行真相源。
- adapter 必须保持“薄”，只要求宿主按 canonical workflow 执行，不把评分逻辑迁出仓库协议。
- 兼容性约束:
  - 不新增必须参数。
  - 旧版 `volume-self` 输入缺少新字段时应尽量兼容。
  - `.yaml` 仍必须是 JSON-compatible YAML。
- 文档与测试必须随结构扩展同步。

## 5. 问题定义

本轮针对“已存在问题为何没有被及时暴露”补三段式审查闭环：

1. 为什么工具没有检测到。
2. 为什么 AI 自审没有注意到。
3. 如何优化规则、流程或 skill。

同时引入“独立编辑”视角，避免同一线程既写正文/自审又给自己打分。

## 6. 计划改动

1. 扩展卷级自审 guide，明确要求独立编辑审查与三段式归因。
2. 扩展 `volume_self_review` 模板与归一化结构：
   - 增加独立编辑审查元数据。
   - 增加编辑评分/评语/改进点。
   - 给 issue 增加“为什么工具漏掉”“为什么自审漏掉”“优化动作”等字段。
3. 保持 `review volume-self` / `review volume-self-template` 命令入口不变，仅增强输出/校验。
4. 更新 Codex / Claude adapter skill：
   - 若宿主支持 subagent / 新线程 / 无上下文代理，则卷级独立编辑审查应优先走该通道。
   - 若不支持，明确 fallback 为 fresh thread / same agent fallback，并标记可信度下降。
5. 补 smoke tests，覆盖模板生成、兼容写入、新字段持久化。
6. 用现有项目做真实校验，至少覆盖：
   - `projects/mingdengzhaogu`
   - `projects/demo-urban-occult-long`

## 7. 验证方式

- `PYTHONPATH=src python -m unittest tests.smoke.test_review_volume_self tests.smoke.test_status_command tests.smoke.test_workflow_command`
- 必要时补跑 `PYTHONPATH=src python -m unittest discover -s tests`
- 用现有小说工程执行实际检测命令，确认：
  - 工具能检出既有问题或能说明为什么漏检。
  - 模板能承载独立编辑评分和三段式归因。
  - skill 文档明确要求独立编辑通道。

## 8. 需要同步的文档

- `docs/guides/volume-self-review.md`
- `src/story_harness_cli/services/MODULE.md`
- `src/story_harness_cli/commands/MODULE.md`
- `adapters/MODULE.md`（若 adapter 触发条件描述需要补充）
- `adapters/codex-skill/story-harness-writing/SKILL.md`
- `adapters/claude-code/story-harness-writing/SKILL.md`

## 9. 架构风险

- 若把“独立编辑代理”做成 CLI 强依赖，会破坏离线核心闭环；因此本轮只在协议字段和 adapter workflow 中要求，不把代理运行时塞进 core CLI。

## 10. 重复实现风险

- 已存在 `generation_miss / self_review_miss / tooling_miss` 归因，不能再新造一套平行分类；本轮应在既有分类上补“为什么漏掉”和“怎么优化”。

## 11. 回滚路径

- 若新字段效果不佳，可保留兼容解析，回退模板显示与 adapter 强约束，不影响旧 review 读取。

## 12. 兼容性影响

- 计划保持命令行参数不变。
- 新字段以可选扩展为主，旧 review 记录应继续可读。
