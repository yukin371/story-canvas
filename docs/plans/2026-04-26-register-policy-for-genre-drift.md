# 题材语域失真护栏计划

> 日期: 2026-04-26
> 状态: 进行中
> 范围: `services/style_detector.py` / `protocol/style_profiles.py` / `commands/style.py` / `services/story_review.py` / 对应 smoke tests

## 1. 背景

当前项目已经能检查 AI 风格、特殊术语复用和设定冲突，但还缺少一类更贴近题材阅读体验的问题：

1. 正文可能出现与题材语域明显不符的词汇，例如玄幻正文里直接出现“优先级”“框架”“版本迭代”这类现代项目管理或软件工程口径。
2. 这类问题不一定是句式层面的 AI 痕迹，却会明显破坏沉浸感，属于“题材失真”。
3. 这类约束不应只靠人工记忆或外部 agent，应该进入系统内建约束、修稿提示与 review 消费链路。
4. 同时，还存在“前世的记忆 / 前世的经验 / 前世的判断”这类重复叙事支架问题，它不是单个脏词，而是相同表达骨架被反复套用。

## 2. 目标

1. 在 style detection 中新增“题材语域失真”检查。
2. 规则保持外置可覆盖，通过 `style-profiles.yaml` 管理，而不是把禁用词硬编码死在命令层。
3. 对“重复叙事支架”采用结构启发式检测，而不是继续把更多词堆进字典。
3. 让该信号同时进入：
   - `style check`
   - `style constraints`
   - `style repair`
   - `review chapter` / `review scene` 的 style 消费链路
4. 为玄幻/仙侠这类题材提供 builtin 默认 profile，并允许项目自行放宽或替换。

## 3. 本轮只做什么

### 3.1 profile 层

- 为 builtin profile 增加 `registerPolicy`
- 新增 `xuanhuan-zh` builtin profile
- 支持项目级 `style-profiles.yaml` 覆盖 `registerPolicy`

### 3.2 detection 层

- 在 `style_detector.py` 新增“题材语域失真”模式
- 初始只抓最明显的现代项目管理 / 软件工程话语
- 支持例外白名单，避免误伤现代修仙、都市异能等混合题材
- 在 `style_detector.py` 增加“叙事支架复用”启发式，优先抓取 `X的记忆 / X的经验 / X的判断` 这类被反复套用的抽象说明框架

### 3.3 command / review 层

- `style` 系列命令在未显式指定 profile 时，按项目定位自动选 profile
- 让 review 通过现有 styleAnalysis / proseControl / priorityActions 自动消费新信号

## 4. 非目标

- 不做全题材的大而全禁用词库
- 不做深层语义分类器
- 不判断“所有现代词都不允许”，只处理高置信度的语域失真词
- 不在本轮引入第三方 NLP 依赖

## 5. 验证方式

- `python -m unittest tests.smoke.test_style_detector tests.smoke.test_style_profiles tests.smoke.test_style_command tests.smoke.test_review_chapter`
- `python -m unittest discover -s tests`

## 6. 风险

- 词表过宽会误伤混合题材
- auto profile 若选择过激，可能让 style 命令结果与旧习惯不同
- review 层若只间接消费 style 约束，可能需要补测试保证信号不会被后续重构吃掉
