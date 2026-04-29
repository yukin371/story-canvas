# 写作问题补强实施计划

> 历史状态: 2026-04-29 起降级为 `historical-source`
> 说明: 本文是阶段性实施计划，不再承担长期缺口入口职责。残留未收口问题请转查 `docs/tracking/ai-friction-tracker.md`，不要直接复活本文作为当前执行入口。

> 日期: 2026-04-26
> 状态: Historical source
> 关联当前入口: `docs/roadmap.md`
> 关联问题记录:
> - `docs/plans/2026-04-26-writing-review-gap-log.md`
> - `docs/plans/2026-04-26-unintroduced-name-reveal.md`
> - `docs/plans/2026-04-26-capability-task-mismatch.md`
> - `docs/plans/2026-04-26-register-policy-for-genre-drift.md`
> - `docs/plans/2026-04-26-real-writing-validation-matrix.md`

## 1. 背景

当前项目已经把一部分高价值写作问题接入系统主链：

- “姓名/身份无来源提前揭露” 已进入 `consistency -> review`
- “低能力角色参与高风险任务且缺少保护条件” 已进入 `consistency -> review`
- “现代项目管理语汇侵入题材正文” 已部分进入 `style`

但人工审查仍持续发现三类未完全收口的问题：

1. `export` 产物存在章节边界污染风险，旧正文可能把下一章标题串入当前章末尾。
2. `style` 对“方案文档腔”的检测仍偏词项级，缺少段落结构级识别。
3. `consistency` / `worldbook` 尚未显式建模“修炼阶段 -> 突破目标 -> 条件限制”的 progression 链。

这些问题已经足够具体，适合从“问题记录”推进到“分阶段实施”。

## 2. 目标

1. 先修复直接影响阅读结果的导出边界问题。
2. 把“结构化方案腔”从词项级检测提升到段落结构级检测。
3. 为“修炼阶段链条自相矛盾”补最小协议与一致性校验入口。
4. 保持现有 `review` / `consistency` / `style` / `export` 接口兼容，不做重型重构。

## 3. 非目标

- 不在本轮引入第三方 NLP 依赖。
- 不在本轮构建完整修炼体系知识图谱。
- 不在本轮重做 `export` 格式体系。
- 不在本轮把所有题材都扩展成独立 rule pack。

## 4. 问题分层结论

### 4.1 已解决，可转入调优

- `无来源姓名揭露`
  - 现状: 已进入 `consistency -> review` 主链，并有 smoke tests
  - 本轮动作: 不新增入口，只在后续真实样例中继续调误报率
- `低能力角色 vs 高风险任务`
  - 现状: 已进入 `consistency -> review` 主链，并有 smoke tests
  - 本轮动作: 不改主设计，只在后续世界规则协议完善后扩充词表和 safeguard 语义

### 4.2 部分解决，需要补强

- `结构化方案腔`
  - 现状: 已能通过 `registerPolicy` 抓高置信现代项目管理语汇
  - 缺口: 还不能稳定识别 `时间窗口：/目标：/风险：/约束：` 这类标题式方案块
  - 推荐 owner: `services/style_detector.py`
- `导出串章标题`
  - 现状: 已能剥离章节正文中的本章标题
  - 缺口: 还不能稳定发现“上一章正文末尾混入下一章标题”的边界污染
  - 推荐 owner: `commands/export.py`

### 4.3 尚未解决，需要新设计切片

- `修炼阶段链条自相矛盾`
  - 现状: 只有 `settingCandidates / settingConflicts` 的间接覆盖
  - 缺口: 缺少“阶段 -> 目标阶段 -> 突破条件/瓶颈”显式语义
  - 推荐 owner:
    - 协议: `worldbook`
    - 检测: `services/consistency_engine.py`
    - 暴露: `services/story_review.py`

## 5. 实施范围

### 5.1 In Scope

- `src/story_harness_cli/commands/export.py`
- `src/story_harness_cli/services/style_detector.py`
- `src/story_harness_cli/services/consistency_engine.py`
- `src/story_harness_cli/services/story_review.py`
- `src/story_harness_cli/protocol/schema.py`
- `tests/smoke/test_export.py`
- `tests/smoke/test_style_detector.py`
- `tests/smoke/test_consistency_engine.py`
- `tests/smoke/test_review_chapter.py`
- 必要时补 `worldbook` 相关 fixture

### 5.2 Out of Scope

- `workflow` 语义重构
- 新的 CLI 命令族
- Web UI 侧展示
- 插图 / provider 相关能力

## 6. 实施顺序

### Checkpoint A: 导出边界修复

- [x] 在 `export` 侧补一个“章节尾部串入下一章标题”检测/清理策略
- [x] 明确只修正文导出链，不顺带改原始章节文件
- [x] 为“章末正文 + 下一章标题粘连”补 smoke test
- [x] 确认现有多样例导出测试不回归

### Checkpoint B: 结构化方案腔检测补强

- [x] 在 `style_detector.py` 增加“方案文档化段落”启发式
- [x] 初始只抓高置信结构，例如连续出现 `目标：/风险：/约束：/时间窗口：`
- [x] 让新信号进入既有 `styleAnalysis.patternResults`
- [x] 让 `review chapter` 能通过既有 style 消费链路给出优先动作
- [x] 为玄幻题材和 allowlist 留出可放宽口径

### Checkpoint C: 修炼阶段 progression 最小协议

- [x] 在 `worldbook` 设计最小可选结构，用于记录境界序列、瓶颈、突破条件
- [x] 保持缺省兼容，旧项目没有该结构时不得报错
- [x] 在 `consistency_engine.py` 增加“阶段 -> 突破目标”冲突的高置信软校验
- [x] 在 `story_review.py` 暴露对应风险和建议动作
- [x] 先覆盖最明显的仙侠/玄幻语境，不做通用战力系统

### Checkpoint D: 样例回归与误报控制

- [ ] 用最小 fixture 覆盖每项新规则
- [ ] 至少抽一个真实样例章节做回归，确认没有明显过检
- [ ] 回归样例优先对齐 `real-writing-validation-matrix` 中的固定风格项目，避免临时抽样漂移
- [ ] 若误报偏高，优先收紧启发式，不放宽到“几乎不报”

## 7. 优先级

### P0

- `导出串章标题`
- 原因: 这是直接污染最终阅读产物的 bug，修复收益最高，且不依赖新协议

### P1

- `修炼阶段链条自相矛盾`
- 原因: 这是高价值世界规则问题，适合进入 `consistency + worldbook`

### P1

- `结构化方案腔` 的结构检测
- 原因: 设计方向已存在，只差从词项级推进到段落结构级

## 8. 验收标准

### 最低验收标准

- `export` 能防止最常见的串章标题污染进入导出稿
- `style` 能识别至少一种高置信方案块结构
- `consistency` 能识别至少一种高置信修炼阶段链冲突
- 新信号都能进入现有 `review` 风险提示或优先动作

### 一般验收标准

- 旧样例与现有 smoke tests 不因新规则大面积回归
- 新规则支持明确的 allow / fallback 路径
- worldbook 新结构缺省兼容，不强迫旧项目迁移

## 9. 验证计划

- Lint:
  - `ruff format --check src/ tests/`
  - `ruff check src/ tests/`
- Test:
  - `PYTHONPATH=src python -m unittest tests.smoke.test_export`
  - `PYTHONPATH=src python -m unittest tests.smoke.test_style_detector tests.smoke.test_review_chapter`
  - `PYTHONPATH=src python -m unittest tests.smoke.test_consistency_engine tests.smoke.test_review_chapter`
  - 通过后跑 `PYTHONPATH=src python -m unittest discover -s tests`
- Build:
  - 继续以 `PYTHONPATH=src python -m story_harness_cli` 为主
- Security:
  - 无新增第三方依赖

## 10. 风险与回滚

### 风险

- `export` 若清理策略过宽，可能误删正文里本来就合理存在的标题样式文本
- `style` 若方案块检测过敏，可能误伤现代修仙或有意结构化叙事
- `consistency` 若 progression 规则过早泛化，容易把创意例外误判成错误
- `worldbook` 若新结构设计过重，会把本轮从“最小补强”拖成“协议重构”

### 回滚路径

- `export` 的边界修复可单独回退到旧逻辑
- `style` / `consistency` 的新规则应以新增 pattern / soft-check 为主，可独立删除
- `worldbook` 新结构保持 optional，必要时可只保留 schema 默认值而不继续消费

## 11. 文档同步

- 实现完成后同步：
  - `src/story_harness_cli/services/MODULE.md`
  - `src/story_harness_cli/commands/MODULE.md`
  - `src/story_harness_cli/protocol/MODULE.md`
  - 如 worldbook 协议变化明显，再补一份专项设计或 ADR

## 12. 当前建议执行顺序

1. 先做 `Checkpoint A`
2. 再做 `Checkpoint C`
3. 最后补 `Checkpoint B`

理由：

- `export` 是纯 bug，收益直接且风险最可控
- progression 校验需要协议切片，越晚做越容易被别的规则继续拖延
- 方案腔检测已经有 `registerPolicy` 基础，最后补结构层最顺
