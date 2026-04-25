# 统一规则引擎协议 Phase 1 实施计划

> 日期: 2026-04-26
> 状态: 进行中
> 关联设计: `docs/plans/2026-04-26-unified-rule-engine-protocol.md`

## 1. 目标

在不推翻现有 `style` / `consistency` / `review` / `doctor` / `workflow` 命令结构的前提下，先把“规则语义”统一出来。

本阶段只做最小闭环：

1. 为现有检测结果补统一规则元数据：
   - `ruleId`
   - `source`
   - `scope`
   - `kind`
   - `severity`
2. 产出统一 `judgements` 数组，供命令和 review 直接消费。
3. 保留现有旧字段，避免破坏当前测试和调用方。

## 2. 非目标

1. 不在本阶段重写 `workflow gate`
2. 不在本阶段引入完整 rule registry / DSL
3. 不在本阶段移除旧字段

## 3. 方案

### 3.1 style

- 为 `patternResults` 中的可检测项补统一规则语义
- 新增 `judgements`：
  - 来源：`source=core` 或 `genre-pack`
  - 范围：`scope=chapter`
  - 类型：`kind=style`

### 3.2 consistency

- 为 `settingConflicts`、`unintroducedNameReveals`、`capabilityTaskRisks` 等补统一规则语义
- 新增 `judgements`：
  - `hard` / `soft`

### 3.3 review

- 消费 style / consistency 的统一 `judgements`
- 在结果中输出：
  - `ruleJudgements`
  - 兼容保留旧的 `styleAnalysis` / `consistencySignals`

### 3.4 doctor

- 为 `checks` 中的 warning / error 补统一规则语义
- 新增 `judgements`：
  - 优先服务项目结构校验、建档覆盖度、资产引用校验
  - 保留原有 `checks` 作为兼容输出

### 3.5 workflow

- 为各 gate 的阻塞项补统一规则语义
- 在 `stageResults` 中新增：
  - `ruleJudgements`
  - `gateDecision`
- 让 workflow payload 能直接引用当前 gate 的 `blockingRules`

## 4. 风险

- 如果直接改旧结构，容易打坏现有 smoke tests
- 如果统一语义做得太重，会在 Phase 1 就引入过多重构成本

## 5. 验证方式

- `python -m unittest tests.smoke.test_style_detector tests.smoke.test_style_command`
- `python -m unittest tests.smoke.test_consistency_engine tests.smoke.test_consistency_command`
- `python -m unittest tests.smoke.test_review_chapter tests.smoke.test_review_scene`
- 通过后跑 `python -m unittest discover -s tests`

## 6. 当前停点

- 已完成：
  - `style / consistency / review / doctor / workflow gate` 已接入统一规则 judgement 语义
  - `doctor` 新增兼容输出 `judgements`
  - `workflow` stage 新增 `ruleJudgements` 与 `gateDecision`
- 已记录但尚未内建成 detector 的问题：
  - 结构化方案文风侵入正文
  - 修炼阶段链条矛盾
  - 更普适的叙事支架重复检测继续泛化
- 下一轮建议顺序：
  - 先进入 Phase 2，抽 builtin rule registry
  - 再把新问题逐条挂到统一 rule registry，而不是继续散落在各命令中
