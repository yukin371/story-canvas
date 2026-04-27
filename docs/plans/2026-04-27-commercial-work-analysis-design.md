# 商业成书拆解工程设计文档

> 日期: 2026-04-27
> 状态: 草稿
> 关联需求: `docs/plans/2026-04-27-commercial-work-analysis-requirements.md`
> 关联目录: `noval-data/`

## 1. 设计目标

把“分析几本典型商业作品”收敛成可持续维护的工程，而不是一次性的笔记堆积。

本设计重点回答四个问题：

1. 文件夹怎么拆
2. 每本书怎么拆
3. 多本书怎么横向归纳
4. 结论如何接回 skill / prompt / tool

## 2. 设计原则

### 2.1 单一真相源

- `noval-data/` 是本工程的工作区。
- 原始书目只作为本地输入。
- 跟踪文件只保存衍生结论、结构化摘要、模板化分析。

### 2.2 先逐书，再横向，再工具化

- 不直接从“很多书”跳到“很多规则”。
- 必须先保留逐书证据，再做横向总结，再决定哪些进入 skill / tool。

### 2.3 面向 Story Canvas 流程拆解

逐书分析必须尽量映射到 Story Canvas 自己的流程：

- `PRD`
- `outline`
- `scene / beat`
- `entity / world / foreshadow`
- `review / style / consistency`

这样后续才能自然回灌，而不是再翻译一次。

### 2.4 观察 / 判断 / 建议分层

每份分析都要尽量区分：

1. `观察`
   书里客观上做了什么
2. `判断`
   为什么这样有效或失手
3. `建议`
   哪些值得转成可复用写法

## 3. 目录结构设计

建议在 `noval-data/` 下新增一个独立工作台：

```text
noval-data/
├── archetypes/                       # 现有原始数据分类目录
├── phase1-prd-catalog.json
├── phase1-prd-analysis.md
├── review-index.md
│
└── analysis-workbench/
    ├── README.md
    ├── templates/
    │   ├── book-analysis-template.md
    │   ├── angle-summary-template.md
    │   ├── source-card.template.json
    │   └── prompt-rule-candidate-template.md
    │
    ├── books/
    │   └── <book-slug>/
    │       ├── 00-source-card.json
    │       ├── 01-prd-reconstruction.md
    │       ├── 02-outline-and-volume.md
    │       ├── 03-scene-and-beat.md
    │       ├── 04-characters.md
    │       ├── 05-foreshadowing-and-threads.md
    │       ├── 06-world-factions-and-entities.md
    │       ├── 07-hook-and-reader-appeal.md
    │       ├── 08-strengths-and-problems.md
    │       ├── 09-prompt-lessons.md
    │       └── 10-open-questions.md
    │
    ├── angles/
    │   ├── prd/
    │   ├── outline/
    │   ├── scenes/
    │   ├── characters/
    │   ├── foreshadowing/
    │   ├── world-factions/
    │   ├── hooks/
    │   ├── prose-craft/
    │   └── weaknesses/
    │
    ├── synthesis/
    │   ├── writing-playbook.md
    │   ├── prompt-skill-candidates.md
    │   ├── review-rule-candidates.md
    │   ├── anti-patterns.md
    │   └── sampling-roadmap.md
    │
    └── indexes/
        ├── sample-selection.md
        ├── progress-board.md
        └── cross-book-matrix.md
```

## 4. 逐书目录设计

### 4.1 `00-source-card.json`

作用：

- 记录这本书为什么被选进来
- 记录基本元数据和分析状态

建议字段：

```json
{
  "title": "",
  "sourceFile": "",
  "archetype": "",
  "targetPlatform": "",
  "whySelected": [],
  "analysisStatus": "planned",
  "priority": "high",
  "confidence": "medium",
  "sampleScope": {
    "chaptersRead": [],
    "volumesCovered": [],
    "notes": ""
  }
}
```

### 4.2 `01-prd-reconstruction.md`

反推这本书在立项阶段最可能长什么样：

- 面向谁
- 核心卖点
- 写作目的
- 平台预期
- 连载模型
- 第一卷承诺

### 4.3 `02-outline-and-volume.md`

关注：

- 卷级目标
- 主线 / 支线
- 第一卷闭环
- 第二卷展开方式
- 大纲推进和世界扩张的关系

### 4.4 `03-scene-and-beat.md`

关注：

- 黄金三章怎么铺
- 章节承接 / 交付
- 场景切换
- 章尾钩子
- 细纲是否被机械执行

### 4.5 `04-characters.md`

关注：

- 主角驱动力
- 主角的压力 / 欲望 / 选择
- 关键配角功能
- 关系推进方式
- 人物辨识度来源

### 4.6 `05-foreshadowing-and-threads.md`

关注：

- 伏笔类型
- 埋设时机
- 回收节奏
- 主线 / 支线线程
- 疑点密度是否过载

### 4.7 `06-world-factions-and-entities.md`

关注：

- 世界规则 onboarding
- 势力层级
- 组织关系
- 关键物件 / 身份 / 地点 / 规则实体
- 哪些信息必须写前注入

### 4.8 `07-hook-and-reader-appeal.md`

关注：

- 为什么读者会继续看
- 爽点 / 压抑 / 兑现怎么分布
- 标题、简介、开篇、章尾、卷尾分别怎么钩人
- 平台化消费点是什么

### 4.9 `08-strengths-and-problems.md`

必须同时写：

- 优秀的部分
- 没做好的部分
- 可复用的地方
- 不建议照抄的地方

### 4.10 `09-prompt-lessons.md`

只写可转成工具资产的内容：

- prompt 片段
- skill 写法要点
- review 检查点候选
- style / consistency / doctor 候选项

### 4.11 `10-open-questions.md`

记录：

- 当前读得还不够、不能下定论的地方
- 需要补样本或补章节的地方
- 不应过早工具化的争议点

## 5. 横向角度目录设计

`angles/` 不是逐书复制，而是按一个问题聚合多本书的对照结果。

例如：

- `angles/hooks/first-three-chapters.md`
- `angles/characters/protagonist-drive.md`
- `angles/foreshadowing/payoff-rhythm.md`
- `angles/world-factions/onboarding-budget.md`
- `angles/weaknesses/common-failures.md`

每份横向文档建议固定结构：

1. 分析问题
2. 对照样本
3. 共性规律
4. 例外情况
5. 可进入 skill / tool 的候选结论

## 6. 综合沉淀层设计

### 6.1 `writing-playbook.md`

面向人，回答“好的写法到底长什么样”。

### 6.2 `prompt-skill-candidates.md`

面向 skill，回答“哪些经验应该进入写作提示”。

### 6.3 `review-rule-candidates.md`

面向工具，回答“哪些问题值得进入 review / style / consistency / doctor”。

### 6.4 `anti-patterns.md`

专门收集：

- 商业作品里也常见但不建议复用的写法
- 容易让 agent 学歪的套路
- 容易误判成“成功经验”的平台噪音

## 7. 文件命名与 slug 规则

`books/<book-slug>/` 建议：

- 使用稳定英文 slug
- 不直接使用超长中文标题
- 保留一个映射索引，方便从原始文件名回查

示例：

- `books/qing-bu-yao-da-rao-wo-xiu-xian/`
- `books/wo-bu-shi-xi-shen/`
- `books/quan-yuan-lian-ai-xi-ju/`

## 8. 工作流程设计

### Step 1: 选书

在 `indexes/sample-selection.md` 记录：

- 为什么选它
- 它代表什么 archetype
- 它最值得分析的角度是什么

### Step 2: 建逐书目录

只先建模板文件，不要求一步写满。

### Step 3: 先做 PRD / Hook / Volume

原因：

- 这三层最直接服务 skill 收敛
- 也是最容易先形成可用结论的部分

### Step 4: 再做角色 / 伏笔 / 势力 / world

这是把“故事能不能长期成立”拆出来的关键层。

### Step 5: 写 strengths / problems / prompt lessons

逐书产出必须以“可转写”为终点，而不是结束于作品总结。

### Step 6: 周期性写横向归纳

不要等全部书做完才总结。建议每完成 2-3 本，就写一轮横向总结。

## 9. 与 Skill / Tool 的对接边界

### 9.1 可以直接反哺 skill 的内容

- 写前约束
- 章节推进提醒
- 钩子与章尾提醒
- 人物塑造禁忌
- 信息投放节奏提醒

### 9.2 可以作为工具候选规则的内容

- onboarding 缺失
- 章尾无有效推进
- 角色目标不清
- 伏笔密度过高但回收不足
- scene 只是机械执行细纲

### 9.3 暂不直接工具化的内容

- 过于依赖题材语感的判断
- 平台偏好的细腻微差
- 单本书特有的成功气质

## 10. 第一批样本建议

建议第一批控制在 5 本左右：

1. `请不要打扰我修仙`
2. `开局长生万古，苟到天荒地老`
3. `我不是戏神`
4. `全员恋爱喜剧，凭什么就我单身`
5. `魔女大人，请不要再复活我了`

理由：

- 覆盖玄幻男频、都市超凡、日轻恋爱、西幻轻小说
- 既有强商业钩子，也有明显不同的读者承诺
- 有利于快速拉开“写法差异”，避免第一批样本过于同质

## 11. 风险与防呆

### 11.1 风险：分析越写越散

防呆：

- 强制模板
- 强制索引
- 强制每本都要有 `prompt-lessons`

### 11.2 风险：读书笔记太主观

防呆：

- 区分观察 / 判断 / 建议
- 标记置信度
- 保留 `open-questions`

### 11.3 风险：横向总结脱离证据

防呆：

- 横向文档必须回链到逐书目录
- 不允许无来源抽象结论直接进入工具规则候选

## 12. 当前建议

当前不建议立刻大规模开拆所有书，而建议按下面顺序推进：

1. 先确认本设计文档
2. 再落 `analysis-workbench/` 目录骨架与模板
3. 再选第一批 5 本书
4. 先做每本书的：
   - `source-card`
   - `PRD`
   - `hook`
   - `volume`
5. 第一轮横向总结后，再补角色 / 势力 / 伏笔 / prompt lessons 深拆

这样更符合“先定结构，再做内容，再做方法沉淀”的节奏。
