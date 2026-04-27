# 架构整理重构状态说明

> 日期: 2026-04-26
> 状态: 草稿
> 关联当前入口: `docs/roadmap.md`
> 关联文档:
> - `docs/ARCHITECTURE_GUARDRAILS.md`
> - `docs/adr/ADR-002-optional-dependencies-and-providers.md`
> - `docs/plans/2026-04-26-unified-rule-engine-protocol.md`
> - `docs/plans/2026-04-26-unified-rule-engine-phase1.md`

## 1. 结论摘要

如果问题是“之前说的架构整理/重构是不是已经全部完成”，结论是：

- **仓库分层、owner 和依赖边界整理，基本完成。**
- **统一规则引擎方向的架构重构，只完成了 Phase 1，不算整体完成。**

换句话说：

1. `commands / services / protocol / providers` 这层仓库级边界已经收住。
2. provider 作为 side-effecting client 的 canonical owner 已明确并落地。
3. `style / consistency / review / doctor / workflow` 之间的“统一规则协议”只完成了兼容层改造，还没进入真正的规则注册表与 pack 化阶段。

因此，当前状态更准确地说是：

- **基础架构整理完成**
- **规则系统架构重构进行到中途**

## 2. 已完成的部分

### 2.1 仓库分层与 canonical owner

已完成内容：

- 已有正式的仓库级架构护栏文档
- 命令层、服务层、协议层、工具层、provider 层职责已明确
- 共享关注点已有 canonical owner
- forbidden dependency direction 已明确

依据：

- `docs/ARCHITECTURE_GUARDRAILS.md`
- `src/story_harness_cli/commands/MODULE.md`
- `src/story_harness_cli/services/MODULE.md`

这说明“目录和 owner 谁负责什么”这轮整理不是停留在口头，而是已经沉淀成了持续约束。

### 2.2 provider 边界整理

已完成内容：

- `providers/` 已被定义为外部 API / SDK / optional dependency wrapper 的 canonical owner
- base install 保持 stdlib-only
- services / protocol 不直接碰 provider SDK

依据：

- `docs/adr/ADR-002-optional-dependencies-and-providers.md`
- `docs/ARCHITECTURE_GUARDRAILS.md`

这部分属于明确完成的架构收敛，不应再回退。

### 2.3 统一规则语义 Phase 1

已完成内容：

- `style / consistency / review / doctor / workflow gate` 已补统一规则 judgement 语义
- 输出中已有 `ruleId / source / scope / kind / severity`
- `review` 已开始消费统一 judgement，而不是只消费私有字段
- `doctor` 和 `workflow` 也已开始暴露统一规则语义

依据：

- `docs/plans/2026-04-26-unified-rule-engine-phase1.md`
- `src/story_harness_cli/commands/MODULE.md`
- `src/story_harness_cli/services/MODULE.md`

这说明“规则系统完全散装”这一阶段已经过去了。

## 3. 尚未完成的部分

### 3.1 统一规则引擎 Phase 2 未完成

未完成内容：

- builtin rule registry 还没抽出来
- 规则元数据还没有集中注册
- 新规则仍然主要通过在 `style_detector.py`、`consistency_engine.py`、`story_review.py` 中逐项追加

依据：

- `docs/plans/2026-04-26-unified-rule-engine-protocol.md`
- `docs/plans/2026-04-26-unified-rule-engine-phase1.md`

这意味着：

- 当前“统一规则协议”更多是统一输出语义
- 还不是“统一规则注册与执行底盘”

### 3.2 pack 化未完成

未完成内容：

- 还没有统一的 `rule-packs.yaml` 或同类入口
- `style-profiles.yaml` 仍然只是 style 子系统的先行入口
- genre-pack / project-pack 还没有成为跨 `style / consistency / review / doctor` 的统一载体

影响：

- 新题材或项目特化规则仍然容易局部落在某一子系统里
- 题材规则还没有完全变成“可叠加配置”，而是部分硬编码、部分 profile 化

### 3.3 gate 统一未完成

未完成内容：

- workflow 虽然已输出 `gateDecision`，但还没有彻底建立统一 gate registry
- `outline readiness`、`review readiness`、`export readiness` 仍主要靠现有 service 逻辑拼装
- workflow 还没有完全变成“消费统一规则结果的薄层”

### 3.4 新问题还没完全挂到统一架构上

当前已记录但未完全内建的问题包括：

- 结构化方案文风侵入正文
- 修炼阶段链条矛盾
- 更普适的叙事支架复用泛化
- 导出边界污染

这些问题目前已经有计划文档，但还没有全部进入统一 rule registry，因为 registry 本身还不存在。

## 4. 当前架构状态该怎么理解

### 4.1 已经不再需要重做的大方向

以下方向可以视为已经稳定：

- 命令层负责编排和 I/O
- 服务层负责纯业务逻辑
- 协议层负责状态读写与 schema 默认值
- provider 层负责外部系统接入
- 当前仓库以 stdlib-only 为基线

这些属于“已完成的架构整理”，不应在补功能时反复摇摆。

### 4.2 仍然需要继续推进的重构方向

后续真正还需要做的，不是再次重画大分层，而是：

1. 抽统一 rule registry
2. 把题材/项目特化规则继续 pack 化
3. 让 `review / doctor / workflow` 更多消费统一规则对象
4. 把新增问题挂到统一规则系统，而不是继续零散散落

也就是说，接下来的“架构重构”重点已经从**目录重构**转成了**规则系统收敛**。

## 5. 当前判断

如果只问一句话结论：

- **架构整理完成了吗？**
  - **基础分层和边界整理，算完成。**
- **架构重构完成了吗？**
  - **没有，规则系统只做到 Phase 1。**

## 6. 对后续工作的建议

### 6.1 不建议现在再做一次“大而全架构重构”

原因：

- 仓库大分层已经稳定
- 当前更大的收益来自补功能和检测
- 若现在重开大重构，容易把进度从问题补强拉回抽象整理

### 6.2 建议采用“功能补强 + 架构顺手收口”的方式推进

建议顺序：

1. 先修 `export` 边界问题
2. 再补修炼阶段 progression 最小协议
3. 再补结构化方案腔检测
4. 在做这些功能时，顺手为 Phase 2 抽最小 builtin rule registry

这样能避免：

- 先做空心架构
- 再回头补真实规则

## 7. 推荐下一步文档

如果准备继续推进规则系统架构，而不是只补功能，建议下一份更细文档是：

- `docs/plans/2026-04-26-unified-rule-engine-phase2.md`

它应专门回答：

- builtin rule registry 最小结构是什么
- 现有 `judgements` 如何映射到 registry
- `style-profiles.yaml` 如何与未来的 `genre-pack/project-pack` 兼容
- 不破坏现有命令输出的迁移步骤是什么
