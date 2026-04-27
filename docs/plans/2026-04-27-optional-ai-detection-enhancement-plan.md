# 外部 AI 检测增强计划

> 日期: 2026-04-27
> 状态: 草稿
> 关联当前入口: `docs/roadmap.md`
> 关联文档:
> - `docs/adr/ADR-002-optional-dependencies-and-providers.md`
> - `docs/plans/2026-04-26-writing-review-gap-log.md`
> - `docs/plans/2026-04-26-workflow-gap-notes.md`
> - `docs/plans/2026-04-26-writing-quality-loop.md`

## 1. 背景

当前仓库已经具备一条可运行的 `style -> review -> workflow` 质量链，但在真实写作审查中，人工持续发现大量“单句不一定错、通篇看非常像 AI”的问题，主要集中在：

- 高频支架句复用
  - `不是……是……`
  - `像……`
  - `不重/不轻/不偏/不倚`
  - 短句切断后再递进
- 抽象递进与故作深沉腔
- 章节/提纲元信息泄漏进正文
- POV 可见性 / 可知性越界
- 方案文档腔之外的更多“句法层 AI 味”

这些问题说明：

1. 仅靠现有 builtin heuristics 还不够。
2. 仅做“AI 率”判断也不够，因为用户真正要修的是具体问题，而不是一个模糊概率。
3. 需要考虑引入外部增强能力，但必须遵守现有依赖边界。

## 2. 目标

1. 在不破坏 `base install` 零依赖基线的前提下，增强 AI 风格检测能力。
2. 让外部增强优先服务“可解释问题检测”，而不是只输出黑盒 `AI probability`。
3. 把人工已经稳定发现的问题转成更强的 repo-native 规则。
4. 保留 builtin fallback，确保离线 CLI 主闭环不失效。

## 3. 非目标

- 不把第三方库升级为 base install 默认依赖。
- 不引入必须联网才能工作的检测能力作为核心前置。
- 不把“AI 作者身份识别”当成唯一或主要质量判断。
- 不在本轮直接接入重量级中文大模型推理链。
- 不在本轮改动故事协议真相层格式。

## 4. 当前边界结论

### 4.1 已允许的方向

根据 `ADR-002`：

- `base install` 继续保持 stdlib-only
- 第三方库可以作为 optional dependency 引入
- `providers/` 是 optional dependency wrapper 的 canonical owner
- `services/style_detector.py` 可以保留 builtin fallback，并消费外部 scorer / similarity 增强

### 4.2 当前不应直接采用的方向

- 直接引入“某黑盒 AI 检测库”，然后把其分数当成核心判断
  - 原因:
    - 可解释性弱
    - 中文小说场景稳定性未知
    - 难以告诉作者“具体哪里假、为什么假、怎么改”
- 直接把联网模型判定接入主闭环
  - 原因:
    - 违背离线可验证基线
    - 会让回归与测试变脆

## 5. 问题分层

### 5.1 适合继续由 builtin heuristics 负责的问题

- 章节/卷/提纲元信息泄漏
- POV 可见性越界
- 方案文档腔
- worldbook / consistency 类设定冲突
- 明确词表驱动的题材语域失真

这些问题可解释性强、规则边界清楚，继续由仓库内规则主导更稳。

### 5.2 适合用 optional dependency 增强的问题

- 句式骨架近似度
- 邻近段落的承重句复用密度
- 高频 `像……` 比喻模板复用
- 抽象人物反应句聚类
- 段落间相似开头/相似转折/相似校准句统计
- 风格漂移前后文相似度对比

这些问题的共同点是：

- 单条规则很难覆盖
- 但它们又不是纯语义理解问题
- 适合通过文本近似、句法骨架比较、聚类统计来增强

### 5.3 暂不建议依赖外部库解决的问题

- 复杂人物逻辑是否成立
- 反派是否有魅力
- 第一卷复杂度是否过高
- 世界观引导是否足够

这些问题更接近结构审查和故事判断，不适合寄希望于“检测库直接看出来”。

## 6. 推荐技术路线

### 路线 A: 轻量文本近似增强

优先级: `P0`

方向:

- 复用已存在的 `style-local` extra
- 以轻量文本近似库增强：
  - 句式骨架相似度
  - 重复支架句聚类
  - 邻近段落句法重复密度

适合解决:

- 高频支架句复用
- 抽象递进句法反复出现
- “单句看可用、连起来很假”的问题

优点:

- 可解释
- 离线可运行
- 与现有 `style_detector.py` 兼容度高

缺点:

- 仍然主要是启发式
- 很难直接理解深层语义

### 路线 B: 本地可选中文 NLP / 分词增强

优先级: `P1`

方向:

- 仅作为 optional dependency
- 用于更稳定地提取句法骨架、修饰链和比喻密度

适合解决:

- 中文短句切分不稳
- 比喻链、抽象名词链统计不稳

优点:

- 能提高中文文本结构识别质量

缺点:

- 依赖更重
- fallback 设计和测试成本更高

### 路线 C: 黑盒 AI authorship detector

优先级: `P3`

当前建议:

- 不作为主线
- 最多只作为辅助实验项

原因:

- 它最多告诉我们“像 AI”
- 但我们真正要的是：
  - 哪类句法支架过密
  - 哪些段落像提纲执行稿
  - 哪些反应句过于抽象
  - 哪些地方该怎么改

## 7. 推荐落地方向

### Phase 0: 先补规则清单，不急着接库

- 把已人工稳定发现的问题先收敛成明确 rule categories
- 按“builtin 可做 / external 值得增强 / 暂不适合检测”三类分桶
- 明确每类规则的 evidence、message、suggestion 结构

交付物:

- 规则清单
- 句式样例集
- 风险等级划分

### Phase 1: 在 `style_detector.py` 接轻量 optional similarity enhancer

- 保持 builtin fallback
- 外部增强仅参与：
  - 句法骨架近似度
  - 高频支架句密度统计
  - 邻近段落重复聚类
- 不改 CLI 协议，只增强 `styleAnalysis.patternResults / judgements`

推荐 owner:

- wrapper: `src/story_harness_cli/providers/`
- 消费: `src/story_harness_cli/services/style_detector.py`

### Phase 2: 把增强结果接入 `review chapter` 与卷级自审

- 把“支架句过密”“抽象反应过密”“相似段落过密”接进：
  - `priorityActions`
  - `contractAlignment.risks`
  - `ruleJudgements`
- 卷级自审时增加“AI 风格密度摘要”，而不是只报单章

### Phase 3: 再评估是否需要更重的中文结构增强

- 只有当 Phase 1 证明确实存在稳定瓶颈时再做
- 不在当前实验阶段提前引重依赖

## 8. 文件级影响预估

### In Scope

- `pyproject.toml`
- `src/story_harness_cli/providers/`
- `src/story_harness_cli/services/style_detector.py`
- `src/story_harness_cli/services/story_review.py`
- `tests/smoke/test_style_detector.py`
- `tests/smoke/test_review_chapter.py`

### Maybe In Scope

- `commands/style.py`
- `docs/PROJECT_PROFILE.md`
- `src/story_harness_cli/providers/MODULE.md`
- `src/story_harness_cli/services/MODULE.md`

### Out of Scope

- `worldbook` 协议重构
- `workflow` 状态机重写
- Web UI
- 外部联网检测服务作为核心能力

## 9. 验收标准

### 最低验收

- 缺失 optional dependency 时，`style` / `review` 仍可运行
- 外部增强能稳定提升至少一类真实问题的检出率
- 输出仍然是具体 rule / evidence，而不是只有一个黑盒分数

### 一般验收

- 对以下问题至少补强其中两类：
  - 高频支架句复用
  - 抽象递进句
  - 校准句密度
  - 相邻段落同构句法
- 误报率没有明显高到不可用
- 真实样稿中的至少若干人工案例能被新规则命中

### 理想验收

- 卷级自审能输出“AI 风格高风险段落”而不是泛泛而谈
- 可以区分：
  - 词汇问题
  - 句法支架问题
  - 结构元信息问题
  - 视角边界问题

## 10. 验证计划

- 单元测试:
  - builtin fallback 路径
  - optional dependency 可用路径
  - 依赖缺失回退路径
- 真实样例回归:
  - 使用当前人工审查中已记录的高风险句子
  - 至少覆盖：
    - `不是……是……`
    - `像……`
    - `不重/不轻/不偏/不倚`
    - 抽象递进句
- 输出验证:
  - 必须验证 evidence 和 suggestion 是否可供作者直接改稿

## 11. 风险与回滚

### 风险

- 过度依赖相似度，导致误伤正常修辞复现
- 中文短句切分不稳，导致密度统计噪声偏大
- 引入 optional dependency 后，测试矩阵变复杂
- 若输出只剩“像 AI”，仍然无法直接帮助修文

### 回滚路径

- 所有外部增强都必须是可拔掉的 optional path
- 一旦误报过高，可单独关闭某类 enhancer，不影响 builtin 主链
- `style_detector.py` 应继续保留纯 builtin 最小可用检测

## 12. 当前建议执行顺序

1. 先补 `Phase 0`
2. 再做 `Phase 1`
3. 然后用真实样稿回归
4. 最后才决定是否需要更重依赖

理由:

- 当前最大问题不是“没有库”，而是“规则分类还不够稳定”
- 先把人工已发现问题固化成规则集合，再决定哪些值得交给外部增强，风险最低

## 13. 2026-04-28 当前落地状态

### 13.1 本轮已完成

- 已把首批中文高频 AI 风格规则落到 repo-native `style` 主链：
  - `contrastFlipPattern`
  - `analogicalPivotPattern`
  - `templateCatchphrasePattern`
  - `paragraphReadability`
- 新规则已接入：
  - `style check`
  - `review chapter`
  - `review scene`
  - 统一 `patternResults / judgements / ruleJudgements`
- 已同步：
  - `services/rule_registry.py` 规则元数据
  - `services/MODULE.md`
  - `commands/MODULE.md`
- 已完成测试回归：
  - 相关 smoke tests 通过
  - 全量 `PYTHONPATH=src python -m unittest discover -s tests` 通过

### 13.2 本轮实现判断

- 当前方向成立：优先把人工稳定发现的中文句式问题转成内建规则，而不是先接黑盒 detector。
- `paragraphReadability` 已开始对真实样例章节评级产生影响，说明它不只是展示信号，而是真正进入了质量基线。
- 长篇样例中部分章节评级从 `strong` 下调到 `solid`，已同步回归基线；这属于审查标准收紧，不是功能回退。

### 13.3 当前未完成

- 尚未落地更高一层的 `clusteredAIPhrasing` 聚合信号。
- 句式规则目前仍是启发式正则 + 密度阈值，还没有引入 optional similarity/backend 增强。
- 还未把外部来源矩阵里的 `Vale / textlint` optional adapter 真正实现进 `providers/`。
- 还没有把这些新规则显式转成卷级汇总信号，例如：
  - 首卷 AI 风格密度摘要
  - 重点问题段落热区
  - 卷级修稿动作草案

### 13.4 下次续做建议顺序

1. 继续收敛中文高频 AI 句式规则：
   - 减少误报
   - 扩充漏报样式
2. 补 `clusteredAIPhrasing`，把多个轻度命中聚成更高价值的卷级风险。
3. 评估是否引入 `Vale` 或 `textlint` 作为 optional backend，而不是直接上黑盒 authorship detector。
4. 再考虑实验性 `SeqXGPT / Binoculars` 热区信号是否值得挂到 `styleAnalysis.extensions.experimental`。
