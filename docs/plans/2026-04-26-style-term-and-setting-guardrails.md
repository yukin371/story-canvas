# 高频术语与设定入账护栏计划

> 日期: 2026-04-26
> 状态: 进行中
> 范围: `services/style_detector.py` / `services/consistency_engine.py` / `services/projection_engine.py` / `commands/projection.py` / 对应 smoke tests

## 1. 背景

当前项目已经能做章节 style 检查、review 和 consistency check，但仍存在两个明显缺口：

1. AI 写作中常见的“高频特殊词”缺少专门检测，容易在单卷或单章里反复出现，形成突兀感和 AI 痕迹。
2. 故事推进中自然长出的新设定还没有被系统内建地吸纳、比对和预警，仍偏依赖外部 agent 或人工记忆。

## 2. 目标

1. 让系统能检测单章内被高频重复使用的特殊术语/概念词，并进入 style analysis。
2. 让 consistency / projection 能发现正文中新出现的世界设定候选，并把非冲突候选纳入 `worldbook` 的渐进式真相层。
3. 对与既有设定明显冲突的新设定给出结构化 warning / risk，而不是把判断完全交给外部 agent。

## 3. 本轮只做什么

### 3.1 高频术语检查

- 在 `style_detector.py` 新增“高频特殊术语复用”启发式
- 优先抓取：
  - 带书名号/引号强调的概念词
  - 2~8 字、重复次数过高、非通用虚词的术语型短语
- 输出到已有 `styleAnalysis.patternResults`

### 3.2 新设定入账与冲突预警

- 在 `consistency_engine.py` 基于 chapter text + `worldbook` 做最小设定候选提取
- 输出：
  - `settingCandidates`
  - `settingConflicts`
- 在 `projection_engine.py` / `projection apply` 中把“高置信度且未冲突”的候选增量写入 `worldbook.premiseFacts`
- 保持渐进式、可追溯，不直接覆盖既有规则

## 4. 非目标

- 不做完整知识图谱
- 不做跨全书深语义设定推理
- 不把所有新设定都自动升级成 world rule
- 不在本轮引入第三方 NLP 依赖

## 5. 验证方式

- `python -m unittest tests.smoke.test_style_command tests.smoke.test_consistency_engine tests.smoke.test_projection_command`
- `python -m unittest discover -s tests`

## 6. 风险

- 术语检测过敏会误伤正常主题词重复
- 设定候选提取过宽会把普通描写误写入 `premiseFacts`
- projection 自动入账若边界不清，可能制造噪声真相层
