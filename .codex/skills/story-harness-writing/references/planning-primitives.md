# Character And Planning Primitives

这是 `story-harness-writing` 的按需 planning reference。

在这些任务里再读取它：

1. 新建主角 / 配角卡
2. 补角色弧线
3. 重做章节方向
4. 重排卷级骨架
5. 想把旧 pure skill 模板字段翻译成 Story Canvas 协议

不要把它当成新的状态模板或强制 schema。真正的真相源仍是仓库协议和项目样例。

证据基础：

1. `projects/demo-light-novel-short/project.yaml`
2. `projects/demo-light-novel-short/entities.yaml`
3. `projects/demo-urban-occult-long/entities.yaml`
4. `projects/demo-urban-occult-long/detailed_outlines.yaml`

## Character Primitives

### 1. 最小角色卡

对 Story Canvas 来说，最小可用人物信息不是 MBTI，而是能支撑行动和评审的字段。

优先级最高的是：

1. `seed.archetype`
2. `seed.hook`
3. `profile.role`
4. `profile.summary`
5. `currentState`
6. `arc.want`
7. `arc.need`
8. `arc.motivation`
9. `arc.milestones`

### 2. 字段该怎么写

#### `seed.archetype`

写角色当前叙事位置，而不是抽象人格学标签。

好例子：

1. `见习邮差`
2. `殡仪馆夜班接运员`
3. `民俗事务科夜巡负责人`

坏例子：

1. `INTJ`
2. `腹黑男主`
3. `美强惨`

#### `seed.hook`

写一条能立刻帮助正文启动的“人味 + 戏味”描述。

它最好回答：

1. 这个人最容易被怎样记住
2. 他的反差、执念或麻烦在哪里

#### `profile.role`

写他在当前项目里的故事功能，例如：

1. 主角
2. 搭档
3. 任务发布者
4. 单元关键证人
5. 前期单元反派
6. 主线缺席核心

#### `profile.summary`

写一到两句“当前可见版本”的人物摘要：

1. 他平时处在什么环境
2. 他现在看起来像什么人
3. 当前弧线的主要摩擦在哪里

#### `currentState`

优先保留会影响当前章行为的状态：

1. `physicalState`
2. `emotionalState`
3. `locationState`
4. `financialState`

如果某个状态不会进入当前几章选择，可以先空着，不要为了填表硬补。

#### `arc.want / need / motivation`

最稳的写法是：

1. `want`: 角色以为自己要什么
2. `need`: 角色真正需要学会或承认什么
3. `motivation`: 为什么这件事此刻非做不可

判断标准：

1. `want` 能推动本卷行动
2. `need` 能支撑成长或关系变化
3. `motivation` 不只是“因为剧情需要”

#### `arc.milestones`

用章节级里程碑记录角色弧线，而不是只记大结论。

每个 milestone 至少说明：

1. `chapterId`
2. `type`
3. `description`

高频有效类型：

1. `inciting-incident`
2. `commitment`
3. `trust`
4. `choice`
5. `growth`
6. `agency`
7. `pressure`
8. `resolution`

### 3. 旧 pure skill 字段的取舍

以下字段若不能直接支撑章节选择、关系变化或 review，就不要优先保留：

1. MBTI
2. 大段外貌履历
3. 不进入当前卷行动的童年轶事
4. 只会制造“设定很全”错觉的抽象性格词

优先把这些旧字段翻译成：

1. 当前习惯
2. 当前恐惧
3. 当前价值排序
4. 当前会咬人的缺陷
5. 当前会推动下一章的关系张力

## Planning Primitives

### 1. 项目层先定什么

在 Story Canvas 里，章节规划不是从“第 1 章写什么”开始，而是先锁：

1. `positioning`
2. `storyContract`
3. 必要时 `commercialPositioning`

至少先说清：

1. 这本书卖的是什么 promise
2. 目标读者期待哪种推进
3. 节奏是快、中快还是慢
4. 什么写法明确要避免

### 2. 章节层最小骨架

与旧 pure skill 的大纲模板相比，Story Canvas 更在乎这些最小骨架：

1. `direction`
2. `beats`
3. `scenePlans`

#### `direction`

一句话写清这章为什么存在。

好方向通常同时包含：

1. 这章要推进哪条线
2. 要把角色推到什么新状态
3. 要把读者送到什么新问题前

#### `beats`

`beats` 不是梗概复述，而是本章不可删除的推进节点。

单章常见数量：

1. 短篇/快章：`2-3`
2. 连载常规章：`3`
3. 高潮章：`3-4`

判断标准：

1. 删掉这个 beat，本章会不会失去关键推进
2. 这些 beat 是否在升级，而不是平移

#### `scenePlans`

每个 scene 至少写：

1. `title`
2. `summary`
3. 段落边界（若已知）

更重要的是隐含回答：

1. 这个场景推进什么
2. 这个场景的主要阻力是什么
3. 这个场景结束后状态变了什么

术语边界：

1. `scenePlans` 里的 `scene` 是章节内场景 / 场次 / 功能段。
2. 传统三幕式、五幕式里的“幕”是 `act`，通常服务卷级、全书级或大型段落结构。
3. 不要把“每章 3 个 scenePlans”说成“每章三幕”；那会混淆 scene review 与 act-level 结构模板。

### 3. 可直接复用的最小结构骨架

#### 三章短篇骨架

适合 `demo-light-novel-short` 这类短弧线：

1. 第 1 章：异常事件 + 任务成立 + 搭档/矛盾立住
2. 第 2 章：阻力升级 + 配合尝试 + 局部成长
3. 第 3 章：最终兑现 + 关系确认 + 新常态

#### `2-3` 章单元案骨架

适合 `demo-urban-occult-long` 这类连载单元：

1. 入口章：异象出现 + 规则不稳 + 主角被拉进局
2. 追查章：线索扩展 + 规则解码 + 风险升级
3. 结算章：截断流程 / 收煞 / 付代价 + 主线抬升

#### 卷一级开局骨架

适合长篇第一卷前段：

1. 先立主角当前生活和异常入口
2. 尽快让主线责任落到主角身上
3. 在前一个单元里给到局部交付
4. 再把更大的制度层或主线层问题抬出来

### 4. 结构模板怎么安全使用

三幕、五幕、英雄之旅之类骨架可以拿来当“检查清单”，不要拿来压平项目差异。

更安全的用法是：

1. 先问项目 promise 是什么
2. 再问卷问题是否在持续升级
3. 再问每章任务是否清楚
4. 最后才看它像不像某个经典结构

### 5. 技法层与 CLI 层怎么配合

结构技法不是新的协议真相源。它应该先被压成 Story Canvas 能执行和检查的字段：

1. 项目 / 卷级技法选择：写进 `PRD.md`、`storyContract`、`paceContract` 或 `structures.yaml`
2. 章节执行：写进 chapter `direction`
3. 关键推进点：写进 `beats`
4. 局部场景功能：写进 `scenePlans.summary`
5. 写后检查：用 `outline check`、`review chapter`、`review scene`、`review preflight` 验证是否落地

推荐拆分：

1. 三幕式 / 五幕式 / 英雄之旅：通常作为卷级或全书级 `act` 模板。
2. “切入悬念，倒叙事件”“意料之外，情理之中”“一箭双雕，一点两面”等：通常作为章节或单元内的叙事技法。
3. `scenePlans`：只负责当前章节内部的可审查场景边界和场景功能，不承担传统 act 命名。

## Translation Rule

把旧 pure skill 的人物模板或大纲模板迁到 Story Canvas 时，优先做“字段降维”：

1. 从抽象人格词降到当前行动驱动
2. 从完整简历降到当前卷有效状态
3. 从通用章节表降到 `direction + beats + scenePlans`
4. 从大而全结构图降到当前卷可执行骨架

如果一个字段不能帮助：

1. 写下一章
2. 审这一章
3. 判断角色是否还像同一个人
4. 判断卷级承诺有没有兑现

那它就不该优先保留。
