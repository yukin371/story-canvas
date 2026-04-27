# 统一规则引擎 Phase 2 设计

> 日期: 2026-04-26
> 状态: 草稿
> 关联当前入口: `docs/roadmap.md`
> 关联设计:
> - `docs/plans/2026-04-26-unified-rule-engine-protocol.md`
> - `docs/plans/2026-04-26-unified-rule-engine-phase1.md`
> - `docs/plans/2026-04-26-architecture-refactor-status.md`
> - `docs/plans/2026-04-26-writing-gap-remediation-plan.md`

## 1. 背景

Phase 1 已经完成的事情，是把现有 `style / consistency / review / doctor / workflow` 输出中的规则语义先统一出来：

- `ruleId`
- `source`
- `scope`
- `kind`
- `severity`
- `judgements`

这一步已经让系统从“每个命令各说各话”进入了“至少对外说同一种规则语言”的阶段。

但 Phase 1 仍有明显停点：

1. 规则元数据还没有集中注册。
2. 新规则仍然需要分别塞进 `style_detector.py`、`consistency_engine.py`、`story_review.py` 或 `workflow_engine.py`。
3. `style-profiles.yaml` 只管 style 子系统，还不是统一 pack 入口。
4. `doctor`、`review`、`workflow` 虽然都开始消费 `judgements`，但它们还不是在消费同一个 registry。

因此 Phase 2 的目标不是重做 Phase 1，而是补上最小 builtin rule registry，让“统一规则语义”变成“统一规则元数据底盘”。

## 2. 目标

1. 引入最小 builtin rule registry，集中管理规则元数据。
2. 不重写现有 detectors，只先让它们引用 registry 中的定义。
3. 让 `style-profiles.yaml` 保持可用，同时为未来 `genre-pack / project-pack` 留出兼容路径。
4. 保持现有命令输出兼容，不移除旧字段、不强制修改测试用例结构。
5. 为后续功能补强项提供明确挂点，例如：
   - `export` 边界污染
   - 结构化方案腔
   - 修炼阶段 progression 冲突

## 3. 非目标

- 不在本阶段引入完整 DSL。
- 不在本阶段让所有规则都改成配置驱动执行。
- 不在本阶段重做 `style-profiles.yaml` 文件格式。
- 不在本阶段统一 rubric scoring 计算实现。
- 不在本阶段重构 workflow stage 推断算法。

## 4. Phase 2 要解决的核心问题

### 4.1 当前真正缺的不是 `judgement` 结构

`judgement` 结构在 Phase 1 已经存在。缺的是：

- 这条规则的 canonical 定义放哪
- 新规则新增时先改哪
- 哪些字段可以被 pack 覆盖
- 哪些字段只能由 detector 决定

### 4.2 registry 应该解决的事情

registry 的职责应限定为：

1. 提供规则元数据真相源
2. 提供规则 id 的 canonical owner
3. 提供默认描述、默认标签、默认建议、默认 `source/scope/kind/severity`
4. 提供 pack 覆盖入口

registry 不应直接负责：

1. 执行复杂检测逻辑
2. 读取章节文件
3. 生成 review 分数
4. 决定 workflow 当前阶段

## 5. Phase 2 设计结论

### 5.1 新增最小 registry 模型

建议新增一个 builtin registry 模块，例如：

- `src/story_harness_cli/services/rule_registry.py`

它的 canonical owner 是：

- 规则元数据 owner: `services/rule_registry.py`
- 规则 judgement 组装 owner: `services/rule_semantics.py`
- 检测逻辑 owner: 各自 detector/service

### 5.2 `rule_semantics.py` 不被替代

`rule_semantics.py` 继续保留，职责不变：

- 负责把 detector 结果装配成统一 judgement
- 提供 scopeRef helper

Phase 2 只是让它从“纯手写字段拼装”升级为“优先从 registry 读取默认元数据，再叠加 detector 上下文”。

### 5.3 registry 先只管元数据，不管执行器

Phase 2 不做“规则注册表 + 执行器分发”一体化框架。

只先做到：

- `ruleId -> RuleDefinition`

不要在这阶段把 detector 也抽成插件，否则重构面会过大。

## 6. 最小对象模型

### 6.1 `RuleDefinition`

建议最小结构如下：

```json
{
  "id": "capabilityTaskMismatch",
  "source": "core",
  "scope": "chapter",
  "kind": "soft",
  "severity": "warning",
  "title": "角色能力与任务门槛不匹配",
  "description": "低能力角色参与高风险任务且缺少安全边界说明",
  "tags": ["plausibility", "entity-state", "xianxia"],
  "messageTemplate": "检测到角色能力与任务门槛可能不匹配。",
  "suggestionTemplate": "补足保护条件、规则例外或能力依据。",
  "packOverrides": {
    "genre-pack": ["tags", "messageTemplate", "suggestionTemplate", "severity"],
    "project-pack": ["tags", "messageTemplate", "suggestionTemplate", "severity"]
  }
}
```

### 6.2 `RuleRegistry`

建议 registry 暂时只是内存字典：

```python
RULE_REGISTRY: dict[str, RuleDefinition]
```

不需要数据库，不需要复杂索引。

### 6.3 `ResolvedRuleDefinition`

后续 commands / services 消费时，可得到解析后的结果：

```json
{
  "id": "registerDrift",
  "source": "genre-pack",
  "scope": "chapter",
  "kind": "style",
  "severity": "medium",
  "title": "题材语域失真",
  "description": "正文中出现与题材显著不符的现代项目管理语汇"
}
```

它是 builtin definition 叠加 pack override 后的结果。

## 7. 建议首批登记的规则

Phase 2 不需要一次性全收完，只先把已经稳定存在的规则登记进去。

### 7.1 `style`

- `registerDrift`
- `specialTermRepetition`
- `narrativeFrameRepetition`
- 现有稳定的 AI 风格 pattern ids

### 7.2 `consistency`

- `stateContradiction`
- `relationContradiction`
- `timelineConflict`
- `outlineDeviation`
- `settingConflict`
- `unintroducedNameReveal`
- `capabilityTaskMismatch`

### 7.3 `doctor`

- `missing-style-profiles`
- `invalid-style-profiles`
- `invalid-style-profiles-shape`
- 结构性必需状态缺失类 rule ids

### 7.4 `workflow`

- `missing-outline-direction`
- `missing-beats`
- `missing-scene-plans`
- 其他当前 gate 已经稳定使用的 blocking rule ids

## 8. 与现有 `judgements` 的映射

### 8.1 映射原则

Phase 2 不改变 `judgement` 输出结构，只改变其字段来源。

当前：

- detector / command 自己写死 `source/scope/kind/severity`

Phase 2 后：

1. detector 先给出：
   - `ruleId`
   - `message`
   - `suggestion`
   - `evidence`
   - `scopeRef`
   - `payload`
2. `rule_semantics` 从 registry 读取默认：
   - `source`
   - `scope`
   - `kind`
   - `severity`
   - `tags`
3. 再把 detector 层提供的动态字段覆盖进去

### 8.2 动态字段与静态字段边界

静态字段归 registry：

- `ruleId`
- `source`
- `scope`
- `kind`
- `severity`
- `title`
- `description`
- `tags`
- 默认模板

动态字段归 detector / command：

- `message`
- `suggestion`
- `evidence`
- `scopeRef`
- `payload`
- `status`

### 8.3 `doctor` 和 `workflow` 的兼容方式

`doctor` 和 `workflow` 当前不是“先 detect 再 judge”的典型结构，但也不需要特别重构。

兼容策略：

- 继续由它们生成现有 `checks` / `missing`
- 在装配 `judgements` 时通过 registry 补足元数据

也就是说，Phase 2 允许存在“非 detector 风格的 judgement 生产者”，只要它们最终也引用统一 registry。

## 9. `style-profiles.yaml` 兼容方案

### 9.1 不推翻现有文件

Phase 2 明确保持：

- `style-profiles.yaml` 继续存在
- `patternThresholds / extraPatterns / termPolicy / registerPolicy / framePolicy` 继续有效

原因：

- 它已经是当前 style 子系统稳定入口
- 直接重命名或强制迁移会制造无必要 breakage

### 9.2 兼容方向

建议把 `style-profiles.yaml` 理解为：

- **Phase 2 的局部 genre-pack / project-pack 先行入口**

它还不是完整规则 pack，但已经具备：

- 规则阈值覆盖
- 白名单 / allowlist
- 局部题材词表

### 9.3 未来统一 pack 的迁移方式

后续若引入 `rule-packs.yaml`，迁移方式应是：

1. 先新增统一 pack 入口
2. `style-profiles.yaml` 继续可读
3. 将 `style-profiles.yaml` 的内容映射进统一 pack 解析层
4. 等统一 pack 稳定后，再决定是否弃用旧入口

不建议：

- 在 Phase 2 直接要求所有项目改写 `style-profiles.yaml`

### 9.4 现阶段可新增的轻量兼容层

可选新增一个 pack 解析 helper，例如：

- `protocol/rule_packs.py`

职责：

- 先解析 builtin core registry
- 再叠加 style profile 中与规则相关的 override
- 暂不要求真正存在 `rule-packs.yaml`

这样能提前把“读取配置”和“执行 style 检测”解耦。

## 10. 目录与 owner 建议

### 10.1 建议新增文件

- `src/story_harness_cli/services/rule_registry.py`
- 可选：`src/story_harness_cli/protocol/rule_packs.py`

### 10.2 canonical owner

| 关注点 | owner | 说明 |
|------|------|------|
| 规则元数据定义 | `services/rule_registry.py` | builtin rule definitions |
| judgement 组装 | `services/rule_semantics.py` | 统一 judgement builder |
| style pack 解析 | `protocol/style_profiles.py` | 现有 style 配置入口 |
| 未来统一 pack 解析 | `protocol/rule_packs.py` | 若新增统一入口 |
| 检测逻辑 | 原有 detectors/services | 不迁移 owner |

## 11. 分步迁移方案

### Step 1: 建 builtin registry

- 新增 `rule_registry.py`
- 只登记已稳定 rule ids
- 不改任何 command 输出

### Step 2: 升级 `build_rule_judgement`

- 支持传入 `rule_id` 后自动补默认元数据
- 仍允许显式覆盖 `source/scope/kind/severity`

这样可以逐步迁移，不需要一次性修改所有调用点。

### Step 3: 迁移 `style` 和 `consistency`

- 先从 `style_detector.py` 和 `consistency_engine.py` 开始
- 去掉重复的静态元数据硬编码
- 保留动态 message/suggestion/evidence

### Step 4: 迁移 `doctor` 和 `workflow`

- 把现有 `checks` / `missing` 对应到 registry rule ids
- 让 `doctor.judgements` 和 `workflow.ruleJudgements` 也统一走 registry

### Step 5: 把新增问题挂到 registry

后续新规则一律先补：

1. registry definition
2. detector / producer
3. smoke tests

不再允许“只在 review 里临时拼一个新风险字符串”作为长期方案。

## 12. 与当前实施计划的关系

Phase 2 不应阻塞当前功能补强。

推荐结合方式：

1. 先按 `writing-gap-remediation-plan` 修 `export` 边界
2. 做修炼阶段 progression 规则时，同时补其 registry definition
3. 做结构化方案腔检测时，同时补其 registry definition

这样新问题一落地，就直接进入新底盘，而不是再走一轮散装实现。

## 13. 验收标准

### 最低验收标准

- 已有稳定 rule ids 在 builtin registry 中有统一定义
- `build_rule_judgement` 能从 registry 读取默认元数据
- `style` 和 `consistency` 至少有一部分调用点切到 registry
- 不破坏现有 `judgements` / `ruleJudgements` / `gateDecision` 输出结构

### 一般验收标准

- `doctor` 与 `workflow` 也引用 registry，而不是继续手写平行元数据
- `style-profiles.yaml` 能继续兼容读取
- 新规则实现流程已明确变成“先注册、再检测、再暴露”

## 14. 风险

- 如果 registry 设计过重，Phase 2 会再次退化成抽象工程
- 如果想一次性把 detectors 也插件化，会显著扩大变更面
- 如果 `style-profiles.yaml` 迁移过急，容易破坏现有项目配置
- 如果 `doctor` / `workflow` 强行完全统一执行模型，可能在这一阶段做过头

## 15. 当前建议

Phase 2 的正确目标不是“做一个很漂亮的规则框架”，而是：

- 给现有规则找一个统一元数据真相源
- 让新增规则不再继续散落
- 为 Phase 3 的 pack 化做准备

因此，最稳的推进顺序是：

1. 小 registry
2. judgement builder 接 registry
3. style / consistency 先迁
4. doctor / workflow 再迁
5. 新问题边做边挂载
