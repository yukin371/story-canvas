# 统一规则引擎协议设计

> 日期: 2026-04-26
> 状态: 设计中
> 范围: `style` / `consistency` / `review` / `doctor` / `workflow gate` / 项目约束协议

## 1. 背景

当前仓库已经积累了多类“写作质量与约束”能力：

- `style`
  - AI 风格检测
  - 题材语域失真
  - 重复叙事支架
- `consistency`
  - 状态矛盾、关系矛盾、设定冲突
  - 新设定候选
  - 认知边界与任务合理性问题
- `review`
  - 章节/场景质量评分
  - 契约对齐与商业连载对齐
- `doctor`
  - 项目结构、协议完整性、建档覆盖度
- `workflow`
  - 不同阶段的 gate 判断

这些能力已经开始有效工作，但目前仍然存在一个核心问题：

1. 它们从用户视角都像“规则”或“检查”。
2. 但内部实际上混杂了检测、评分、门禁、配置、项目特化和题材特化。
3. 如果继续按需求逐条打补丁，后续扩到悬疑、恋爱、科幻、现代修仙时，会逐渐失去边界。

因此需要一份统一设计，把“什么是规则、什么是评分、什么是 gate、什么是题材包、什么是项目特化”彻底分清。

## 2. 结论摘要

仅用“通用规则 + 类型规则”的双层划分不够。

后续系统应该采用“三轴统一模型”：

1. `source`
   - 规则来自哪里
2. `scope`
   - 规则作用于什么对象
3. `kind`
   - 规则本质上是在做什么

双层校验仍然保留，但它只属于 `source` 轴的一部分，而不是完整架构。

## 3. 设计目标

1. 让 `style` / `consistency` / `review` / `doctor` / `workflow` 共享同一套规则协议。
2. 允许“通用底盘 + 题材包 + 项目特化”叠加，而不是各自维护一套散乱逻辑。
3. 让“检测结果”、“质量评分”、“流程门禁”在模型上明确区分。
4. 保持 stdlib-only，不引入复杂 NLP 或推理依赖。
5. 让规则可以渐进外置，但 builtin 仍有最小可用集。

## 4. 非目标

1. 不在这一版做深层语义理解引擎。
2. 不保证系统能自动发现所有写作问题。
3. 不把 `review` 变成剧情证明器。
4. 不在这一版引入复杂 DSL、数据库或规则编译器。

## 5. 三轴模型

### 5.1 `source`: 规则来源轴

用于回答“这条规则是仓库内建、题材特有，还是项目自定义”。

建议统一为三层：

- `core`
  - 所有项目共享的基础规则
- `genre-pack`
  - 题材或子题材规则包
- `project-pack`
  - 当前项目自己的额外约束、例外和偏好

加载顺序：

`core -> genre-pack -> project-pack`

后者只能覆盖前者，不应破坏协议结构。

### 5.2 `scope`: 规则对象轴

用于回答“这条规则要检查的是哪个层级”。

建议统一为：

- `project`
  - 项目定位、目标受众、故事契约、题材模板、workflow 元数据
- `world`
  - 世界观、规则、势力、地点、特殊物品、修炼体系
- `entity`
  - 角色卡、能力、状态、关系、认知边界、成长轨迹
- `chapter`
  - 单章结构、节奏、揭示、情绪、设定、风格
- `scene`
  - 局部场景功能、连续性、信息传递、局部情绪
- `export`
  - 标题边界、章节拼接、格式与导出完整性

### 5.3 `kind`: 规则性质轴

用于回答“这条规则是在判对错、判可疑、评分，还是控制流程”。

建议统一为：

- `hard`
  - 硬约束，冲突就是错
- `soft`
  - 合理性风险，需要解释或补充
- `style`
  - 风格信号，不一定是事实错误
- `rubric`
  - 评分项，用于质量评估
- `gate`
  - 阶段门禁，用于工作流推进

## 6. 统一对象模型

### 6.1 `RuleDefinition`

每条规则都应有统一定义结构：

```json
{
  "id": "capability-task-mismatch",
  "source": "core",
  "scope": "chapter",
  "kind": "soft",
  "severity": "warning",
  "tags": ["xianxia", "plausibility", "entity-state"],
  "description": "低修为角色参与高风险任务但缺少例外说明",
  "trigger": "builtin detector or pack config",
  "suppressWhen": ["safeguard-explained", "project-exception-declared"],
  "messageTemplate": "检测到角色能力与任务门槛可能不匹配",
  "suggestionTemplate": "补足保护条件、规则例外或能力依据"
}
```

说明：

- `RuleDefinition` 不一定直接可执行。
- 它更像规范化元数据，用于统一输出、覆盖和治理。

### 6.2 `Signal`

`Signal` 是“检测器产生的原始事实信号”，不直接等于最终结论。

```json
{
  "ruleId": "capability-task-mismatch",
  "scopeRef": {
    "chapterId": "chapter-006",
    "paragraphIndex": 2
  },
  "payload": {
    "entityName": "沈玄",
    "powerLevel": "练气一层",
    "taskLabel": "秘境探索"
  },
  "evidence": [
    "可执事仍让沈玄参加宗门试炼，最终环节不是比武，而是进入秘境探索。"
  ],
  "confidence": 0.83
}
```

说明：

- `Signal` 负责保留证据和上下文。
- 同一种 `Signal` 可以被不同命令消费。

### 6.3 `Judgement`

`Judgement` 是“规则系统对信号做出的统一判断”。

```json
{
  "ruleId": "capability-task-mismatch",
  "kind": "soft",
  "severity": "warning",
  "status": "triggered",
  "message": "检测到角色能力与任务门槛可能不匹配：沈玄被卷入秘境探索，但正文缺少规则解释或保护条件。",
  "suggestion": "补足低阶试炼限定、长老带队、护符保护，或明确其已有足够手段。",
  "scopeRef": {
    "chapterId": "chapter-006",
    "paragraphIndex": 2
  },
  "evidence": [
    "可执事仍让沈玄参加宗门试炼，最终环节不是比武，而是进入秘境探索。"
  ]
}
```

说明：

- `Judgement` 是统一对外输出的规则结论对象。
- `review`、`doctor`、`workflow` 都应优先消费 `Judgement`，而不是直接拼各自私有结构。

### 6.4 `ScoreCard`

`ScoreCard` 用于承载质量评估，不和事实校验混在一起。

```json
{
  "scope": "chapter",
  "rubricId": "chapter-review-v1",
  "dimensions": [
    {"id": "plotMomentum", "score": 15, "maxScore": 20},
    {"id": "proseControl", "score": 13, "maxScore": 20}
  ],
  "total": 78,
  "weighted": {
    "profile": "xuanhuan-zh",
    "score": 81
  }
}
```

### 6.5 `GateDecision`

`GateDecision` 用于表达 workflow 是否允许推进。

```json
{
  "gateId": "chapter_review_ready",
  "status": "blocked",
  "blockingRules": [
    "missing-outline-direction",
    "missing-scene-plans"
  ],
  "notes": [
    "章节未通过大纲前置门禁"
  ]
}
```

## 7. 统一执行流水线

建议后续所有相关命令都围绕同一流水线工作：

1. `context build`
   - 读取项目、题材、项目特化约束与当前 scope
2. `signal detect`
   - 各检测器产出原始 `signals`
3. `rule judge`
   - 把 `signals` 归一成 `judgements`
4. `score evaluate`
   - 对章节/场景做质量评分
5. `action synthesize`
   - 基于 `judgements + score` 生成优先动作
6. `gate decide`
   - workflow 需要时生成 `gate decision`

这样：

- `style` 主要消费第 2、3 步
- `consistency` 主要消费第 2、3 步
- `review` 主要消费第 3、4、5 步
- `doctor` 主要消费第 3 步的项目级和全项目级规则
- `workflow` 主要消费第 6 步

## 8. 命令职责收敛

### 8.1 `style`

后续职责：

- 运行 `kind=style` 的规则
- 输出 style 类 `signals/judgements`
- 生成修稿约束和 repair prompt

不应继续承担：

- 章节综合质量评估
- 项目结构检查
- 设定真相层冲突判定

### 8.2 `consistency`

后续职责：

- 运行 `kind=hard` 和 `kind=soft` 的规则
- 输出设定、自洽、合理性层面的 `judgements`

不应继续承担：

- prose 风格评分
- 商业化章节质量评分

### 8.3 `review chapter/scene`

后续职责：

- 消费统一 `judgements`
- 叠加 `rubric` 评分
- 汇总 `priorityActions`
- 输出契约对齐、商业对齐与项目上下文

不应继续直接硬编码越来越多的特判规则。

### 8.4 `doctor`

后续职责：

- 项目级、全项目级规则巡检
- 协议覆盖度、建档完整度、文件结构与资产完整性检查

不应复制 chapter review 的启发式表达，只输出统一结论对象。

### 8.5 `workflow`

后续职责：

- 消费 `gate` 类结论
- 决定阶段是否允许推进

不应重复定义与 `review`、`consistency` 不一致的门槛语义。

## 9. 配置与 pack 模型

### 9.1 pack 分层

建议未来把规则配置整理成三类 pack：

- `core packs`
  - 仓库内建最小集
- `genre packs`
  - 如 `xuanhuan-zh`、`mystery-zh`、`romance-modern-zh`
- `project packs`
  - 当前项目覆盖项

### 9.2 pack 内容

每个 pack 至少可以承载：

- 启用哪些规则
- 规则阈值
- 白名单/例外
- 风格词表
- 题材语域限制
- 任务合理性例外
- 评分加权
- gate 覆盖策略

### 9.3 协议方向

当前可继续沿用：

- `style-profiles.yaml`
  - 作为 style 子系统的先行 pack 入口

后续建议新增统一协议入口，例如：

- `rule-packs.yaml`
- 或 `review-profiles.yaml`

但无论命名如何，都应满足：

1. JSON-compatible YAML
2. 可缺省
3. 缺失时回退 builtin
4. 支持 source 叠加覆盖

## 10. 现有能力归位

### 10.1 `hard`

- 新设定与旧设定冲突
- 已包裹实体未建档
- 导出章节标题泄漏
- 状态/关系硬冲突

### 10.2 `soft`

- 姓名/身份无来源提前揭露
- 能力层级与任务风险不匹配
- 弧线推进缺口
- 逾期悬念未处理

### 10.3 `style`

- 特殊术语复用
- 重复叙事支架
- 题材语域失真

### 10.4 `rubric`

- `review chapter`
- `review scene`
- 后续 `volume review`

### 10.5 `gate`

- `outline check`
- workflow 各阶段 readiness

## 11. 为什么这套设计更稳

因为当前真正的风险不是“规则不够多”，而是：

1. 检测和评分混在一起。
2. 通用规则和题材规则混在一起。
3. 单章检查、全项目检查和 workflow 门禁混在一起。
4. 新问题一来，只能继续往现有命令里塞 if/else。

统一协议之后：

- 增加新规则不会自动制造新架构分支。
- 新题材只需要新增 `genre-pack`，而不是改多个命令。
- `review`、`doctor`、`workflow` 可以共享结论对象。
- 用户能更清楚地区分：
  - 哪些是“真错了”
  - 哪些是“可能不合理”
  - 哪些只是“风格信号”
  - 哪些只是“质量评分”

## 12. 迁移建议

### Phase 1: 统一语义

目标：

- 不大改实现，先统一命名与输出口径

建议动作：

1. 在 `consistency` / `style` / `review` 内部引入统一 `judgement` 概念
2. 给现有信号统一补 `ruleId/source/scope/kind/severity`
3. 让 `review` 优先消费规则结论，而不是直接解读 service 私有字段

### Phase 2: 抽规则注册表

目标：

- 把规则元数据集中管理

建议动作：

1. 引入 builtin rule registry
2. 让 `style-profiles.yaml` 逐渐向统一 pack 结构靠拢
3. 把 `hard/soft/style` 规则统一登记

### Phase 3: pack 化

目标：

- 把题材规则和项目特化规则显式化

建议动作：

1. 抽出 `genre-pack`
2. 引入 `project-pack`
3. 让题材规则不再只在 `style` 中生效，而能影响 `review` / `consistency` / `doctor`

### Phase 4: gate 统一

目标：

- workflow 直接消费规则引擎结果

建议动作：

1. 把 `outline readiness`、`review readiness`、`export readiness` 统一表达为 gate 规则
2. 输出统一 `GateDecision`

## 13. 当前建议

在正式改代码前，后续实现应遵守以下收敛原则：

1. 不再继续零散地往 `review.py` 直接塞新规则。
2. 新增检查时，先判断它属于 `hard/soft/style/rubric/gate` 哪一类。
3. 新增题材检查时，优先设计成 `genre-pack` 可覆盖，而不是永久硬编码。
4. 所有新规则都应能给出：
   - 证据
   - 风险级别
   - 改写建议
5. `doctor`、`review`、`workflow` 未来应共享同一批规则元数据。

## 14. 结论

后续 Story Harness 的“规则系统”不应再被理解为几个彼此独立的小功能，而应收敛为：

- 一套统一规则协议
- 多个规则来源 pack
- 多类规则性质
- 多个命令对同一结论对象的不同消费方式

双层校验仍然保留，但它只是 `source` 轴的一部分。

真正需要落地的是：

- `source x scope x kind`

这套三轴统一设计。
