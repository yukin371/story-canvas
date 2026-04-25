# 故事约束与情绪协议设计

> 日期: 2026-04-25
> 状态: 设计完成，待实施
> 范围: `project.yaml` / `spec/*.yaml` / `doctor` / `outline check` / `review chapter` / `review scene` / `context refresh`
> 目标样例: `projects/demo-guixu`

## 1. 背景

当前仓库已经有一套“能写完一本书”的基础协议：

- `project.yaml` 已支持 `positioning` / `storyContract` / `commercialPositioning`
- `spec/entities.yaml` 已能承载较丰富的角色卡
- `spec/foreshadowing.yaml` 已有最小伏笔台账
- `review chapter` / `review scene` 已能做启发式评审

但对长篇小说，尤其是《归墟》这种多卷、暗线、设定驱动且角色会持续变化的项目，这套协议仍然不够具体。

用户侧暴露出的核心问题不是“有没有字段”，而是：

1. 只有角色卡，没有稳定的背景/世界观/势力/规则约束
2. 伏笔有“计划内”和“自然长出来”两种来源，但当前台账无法区分
3. 伏笔有短回收、长回收、显性回收、隐性回收等不同策略，当前协议无法表达
4. 角色卡基本是静态画像，缺少“变化中的状态”和“变化原因追溯”
5. 不同题材对约束模块的需求不同，不能强制所有项目都维护势力、法宝、超自然规则
6. 现有契约偏“类型/商业/节奏”，还没有把“希望读者持续体验什么情绪”变成协议

## 2. 现状判断

### 2.1 已有能力

- `project.yaml` 负责作品定位、故事承诺、商业蓝图
- `spec/entities.yaml` 已支持丰富的人物画像
- `arc` 命令已存在，但只覆盖“动机 + 内部冲突 + milestone”的最小角色弧
- `foreshadow` 命令已存在，但台账仍是最小列表
- `review scene` 已有“伏笔与回收”维度，但 `docs/guides/genre-review-rubric.md` 已明确说明它仍是启发式，不等同于结构化账本

### 2.2 当前缺口

以 `projects/demo-guixu` 为例：

- `project.yaml` 已说明类型、卖点、节奏，但没有表达“压迫感/警觉感/释然感”这类读者体验目标
- `spec/entities.yaml` 已写了角色背景、能力、弧线摘要，但没有“当前境界/当前伤势/当前关系温度/已知秘密/最近变化原因”
- `spec/foreshadowing.yaml` 已有 `plannedPayoffChapter`，但没有表达：
  - 这是大纲预埋还是写作中自然生长
  - 期望短期回收还是贯穿全书
  - 期望显性揭露还是让读者先隐约意识到
  - 这条伏笔服务的是哪条主线、哪种情绪或哪位角色弧
- 世界观、势力格局、封印规则、归墟体/守护者血脉/宗门体系等事实，大量散落在 `outline`、`detailed_outlines`、章节正文与导出文件中，没有稳定的“设定真相入口”

## 3. 设计目标

本协议设计解决四件事：

1. 给长篇提供可维护的“故事真相层”，不再把关键约束散落在正文和细纲里
2. 把伏笔、角色变化、世界规则做成可追溯账本，而不是纯人工记忆
3. 允许不同题材选择不同约束模块，避免“现代恋爱也被迫写势力图”
4. 把“读者应持续体验到什么”变成可检查、可提醒、可在评审中消费的协议

非目标：

- 不在本轮直接实现自动抽取世界观或自动证明逻辑正确
- 不把所有创作都收缩成 rigid 模板
- 不要求每个项目一开始就写满所有字段

## 4. 协议总览

建议新增或升级三类协议：

1. `project.yaml`：增加“情绪契约”和“题材模板”
2. `spec/worldbook.yaml`：新增世界/背景/规则/势力/特殊要素真相层
3. `spec/entities.yaml` 与 `spec/foreshadowing.yaml`：升级为“动态角色卡”和“分层伏笔账本”

推荐的分层口径：

- `project.yaml`: 作品级承诺
- `spec/worldbook.yaml`: 世界级事实
- `spec/entities.yaml`: 角色级事实与变化
- `spec/foreshadowing.yaml`: 信息控制与回收计划
- `spec/threads.yaml`: 主线/支线/人物线的汇总入口
- `outline*.yaml`: 章节/场景层的推进计划
- `reviews/*.yaml`: 对上述承诺的启发式检查结果

## 5. Project 协议扩展

### 5.1 新增 `emotionalContract`

用于回答：这本书最主要给读者什么情绪体验。

```json
{
  "emotionalContract": {
    "coreEmotions": [
      "压迫下反制",
      "未知感",
      "局势反转后的爽感",
      "终局释然"
    ],
    "chapterEmotionFloor": [
      "每章至少有一种明确情绪推进，不能纯信息搬运"
    ],
    "forbiddenEmotions": [
      "长时间疲软",
      "空转讲设定导致麻木"
    ],
    "revealPreference": {
      "defaultMode": "partial-inference",
      "allowDirectExplainAtClimax": true
    }
  }
}
```

设计意图：

- `storyContract` 约束“卖点与节奏”
- `emotionalContract` 约束“读者体感”

它们不重复。前者回答“承诺什么”，后者回答“希望读者怎么感受这些承诺”。

### 5.2 新增 `storyTemplate`

用于回答：这个项目到底需要哪些约束模块，哪些不需要。

```json
{
  "storyTemplate": {
    "id": "xianxia-revenge-serial",
    "label": "仙侠重生复仇长篇",
    "modulePolicy": {
      "worldbook": "required",
      "worldRules": "required",
      "factions": "required",
      "artifacts": "optional",
      "powerSystem": "required",
      "foreshadowLedger": "required",
      "characterStateTracking": "required",
      "romanceProgress": "optional"
    },
    "reviewFocus": [
      "世界规则兑现",
      "升级/代价一致",
      "伏笔长回收",
      "卷末格局变化"
    ]
  }
}
```

题材差异不通过“if genre == romance then ...”硬编码，而通过模板模块化表达：

- 现代恋爱可以把 `factions/artifacts/powerSystem` 设为 `off`
- 都市异能可以把 `factions` 设为 `optional`、`powerSystem` 设为 `required`
- 玄幻长篇可以把 `worldRules/factions/foreshadowLedger/characterStateTracking` 设为 `required`

## 6. 新增 `spec/worldbook.yaml`

### 6.1 作用

`worldbook.yaml` 是“故事真相层”的世界侧入口，承接：

- 背景
- 世界规则
- 势力
- 地点
- 特殊物品
- 未揭示真相

它不替代大纲，而是给大纲提供稳定约束。

### 6.2 建议结构

```json
{
  "worldbook": {
    "premiseFacts": [
      {
        "id": "wf-001",
        "label": "时间线已偏移",
        "fact": "重生后世界并非按前世重演，蝴蝶效应会持续放大",
        "visibility": "reader-known",
        "status": "active"
      }
    ],
    "worldRules": [
      {
        "id": "rule-001",
        "label": "归墟体代价",
        "rule": "归墟体每次深度共鸣都会提升暴露风险",
        "scope": "global",
        "exceptions": [],
        "revealedChapters": ["chapter-003", "chapter-008"]
      }
    ],
    "factions": [
      {
        "id": "faction-qingyun",
        "name": "青云宗",
        "type": "sect",
        "publicGoal": "招收弟子，稳固苍梧域地位",
        "hiddenAgenda": "",
        "resources": ["护宗大阵", "剑堂", "外门试炼"],
        "relationships": [
          {
            "target": "faction-tianshu",
            "type": "潜在冲突",
            "status": "warming"
          }
        ],
        "status": "active"
      }
    ],
    "locations": [],
    "artifacts": [],
    "mysteries": [
      {
        "id": "mystery-ye-bloodline",
        "question": "叶清漪为何对归墟域封印产生感应",
        "truthOwner": "worldbook",
        "intendedRevealScope": "volume",
        "status": "partial"
      }
    ]
  }
}
```

### 6.3 设计原则

- `worldRules` 只记录“稳定约束”，不记录章节摘要
- `factions` 只记录“长期有效关系”，短期行动留给 `timeline` / `outline`
- `mysteries` 用来承接“真相尚未揭露，但作者已知”的部分

## 7. 升级 `spec/entities.yaml`

### 7.1 现状问题

当前角色卡更像“设定档案”，而不是“进行中的角色状态”。

对长篇而言，一个角色至少有三层信息：

1. 相对稳定的底层画像
2. 当前章节时点的可变状态
3. 这些变化为什么发生

### 7.2 建议结构

保留现有 `profile`，新增 `state`, `changeLog`, `knowledge`, `powerTrack`。

```json
{
  "entities": [
    {
      "id": "char-shen-xuan",
      "name": "沈玄",
      "type": "character",
      "profile": {
        "traits": ["冷静隐忍", "谋定后动"],
        "background": "前世为天枢宗首席弟子……",
        "coreMotivation": "复仇顾长渊，阻止归墟域封印崩塌"
      },
      "state": {
        "chapterId": "chapter-021",
        "statusTags": ["暴露风险上升", "主动出击阶段"],
        "powerLevel": {
          "publicLevel": "筑基后期",
          "trueLevel": "归墟体深度觉醒中"
        },
        "injuries": [],
        "resources": ["封印碎片", "阵法图纸"],
        "relationships": [
          {
            "target": "char-ye-qingyi",
            "type": "伙伴/知己",
            "intensity": 78,
            "trust": 82
          }
        ]
      },
      "knowledge": {
        "knownTruths": ["顾长渊受白九殇影响"],
        "unknownTruths": ["叶清漪守护者血脉的完整真相"]
      },
      "changeLog": [
        {
          "id": "chg-001",
          "chapterId": "chapter-008",
          "field": "state.powerLevel.trueLevel",
          "from": "潜伏",
          "to": "封印碎片共鸣后增强",
          "reason": "秘境中获得归墟域封印碎片"
        }
      ],
      "arc": {
        "theme": "从单线复仇到承担苍生责任",
        "milestones": []
      }
    }
  ]
}
```

### 7.3 字段分工

- `profile`: 稳定画像，不随章节频繁变化
- `state`: 当前状态，可被后续命令更新
- `knowledge`: 角色知道什么、不知道什么，避免“作者知道但角色不该知道”
- `changeLog`: 变化追溯
- `arc`: 长线人物弧

这比当前仅有的 `arc` 更完整，也能解释“变强/变弱/被陷害/受伤/关系变化”的来源。

## 8. 升级 `spec/foreshadowing.yaml`

### 8.1 现状问题

当前结构只够回答“有没有埋”和“大概哪章回收”，不够回答：

- 这条伏笔是大纲时定的，还是正文长出来的
- 它服务的是哪条线
- 读者应该什么时候“隐约意识到”
- 应该显性揭露还是让读者自行拼出来
- 如果到期未回收，是否构成真正风险

### 8.2 建议结构

```json
{
  "foreshadows": [
    {
      "id": "fs-004",
      "title": "归墟体是封印活钥匙",
      "origin": {
        "type": "outline-seeded",
        "source": "vol-001 planning"
      },
      "plantPoints": [
        {
          "chapterId": "chapter-003",
          "sceneId": "",
          "signalType": "concept-hint",
          "visibility": "implicit"
        }
      ],
      "payoffPlan": {
        "window": {
          "type": "long",
          "targetChapterStart": "chapter-024",
          "targetChapterEnd": "chapter-025"
        },
        "style": "explicit-reveal",
        "readerRealizationMode": "infer-before-confirm"
      },
      "lineBinding": {
        "threads": ["main-revenge", "seal-collapse"],
        "entities": ["char-shen-xuan", "char-gu-changyuan", "char-bai-jiushang"],
        "worldRules": ["rule-001"]
      },
      "emotionGoal": [
        "命运逼近感",
        "真相落地时的原来如此"
      ],
      "status": "planted",
      "payoffPoints": []
    }
  ]
}
```

### 8.3 关键新增字段

- `origin.type`: `outline-seeded` / `emergent`
- `plantPoints`: 一条伏笔允许多次种下
- `payoffPlan.window.type`: `short` / `mid` / `long`
- `payoffPlan.style`: `explicit-reveal` / `partial-reveal` / `background-payoff`
- `readerRealizationMode`: 
  - `surprise-on-reveal`
  - `infer-before-confirm`
  - `never-explicitly-confirmed`
- `emotionGoal`: 这条伏笔希望引发什么情绪

这样才真正支持你说的几种情况：

- 大纲预设伏笔
- 人物自然生长出的伏笔
- 短回收
- 全书长回收
- 明说
- 半明半暗
- 不主动揭露，只让读者逐步意识到

## 9. `threads.yaml` 的定位调整

当前 `threads.yaml` 为空，建议把它提升为“线索/主线/人物线索引”，而不是继续闲置。

推荐结构：

```json
{
  "threads": [
    {
      "id": "main-seal-collapse",
      "label": "封印崩塌主线",
      "type": "main",
      "status": "active",
      "relatedForeshadows": ["fs-001", "fs-004", "fs-005"],
      "relatedEntities": ["char-shen-xuan", "char-bai-jiushang"],
      "targetPayoffScope": "book"
    }
  ]
}
```

这样 `foreshadowing` 不再是孤立列表，而能挂到主线/人物线/支线上。

## 10. 情绪体验如何进入评审链路

### 10.1 `outline check`

读取：

- `storyTemplate.modulePolicy`
- `emotionalContract.chapterEmotionFloor`

用途：

- 判断当前章节是不是只有信息，没有情绪推进
- 判断该题材必须具备的世界/势力/角色状态模块是否已经准备好

### 10.2 `doctor`

读取：

- `storyTemplate.modulePolicy`
- `worldbook`
- `entities.state/changeLog`
- `foreshadowing.payoffPlan`

用途：

- 缺少 required 模块时给 warning/error
- 伏笔到期未处理时提醒
- 角色已显著变化但未写 `changeLog` 时提醒

### 10.3 `review chapter` / `review scene`

新增但仍保持启发式：

- 读取 `emotionalContract`
- 读取当前章节范围内“应接近回收窗口”的伏笔
- 读取活跃角色的 `state`

输出应从“这章写得好不好”进一步提升为：

- 这章有没有兑现目标情绪
- 该回收的伏笔是否开始回收
- 角色状态变化是否有代价、有因果

### 10.4 `context refresh`

应优先加载：

- 当前卷相关 `worldRules`
- 活跃 `factions`
- 当前章相关 `threads`
- 活跃角色的 `state`
- 已到窗口的 `foreshadows`

这样上下文不是“把所有设定全塞给模型”，而是“只给当前创作最需要的约束片段”。

## 11. 对《归墟》的迁移建议

### 11.1 第一优先级

- 增加 `project.emotionalContract`
- 新建 `spec/worldbook.yaml`
- 升级 `spec/foreshadowing.yaml`

原因：

- 《归墟》最大问题不是没人物，而是设定真相和长伏笔分散

### 11.2 第二优先级

- 升级 `spec/entities.yaml` 为动态角色卡
- 启用 `threads.yaml` 记录主线/人物线

原因：

- 《归墟》角色状态与关系会明显变化，尤其是：
  - 沈玄：实力、暴露风险、目标重心
  - 叶清漪：从变数到锚点，再到守护者血脉觉醒
  - 宋怀瑾：摇摆、愧疚、站队
  - 顾长渊：操控者到棋子

### 11.3 《归墟》建议情绪契约

```json
{
  "emotionalContract": {
    "coreEmotions": [
      "局势失控下的冷静反制",
      "蝴蝶效应带来的未知感",
      "暗线逐步拼合的原来如此",
      "终局放下后的释然"
    ],
    "forbiddenEmotions": [
      "重复升级导致麻木",
      "长时间讲设定导致疲软"
    ]
  }
}
```

### 11.4 《归墟》建议题材模板

```json
{
  "storyTemplate": {
    "id": "xianxia-rebirth-revenge-longform",
    "modulePolicy": {
      "worldbook": "required",
      "worldRules": "required",
      "factions": "required",
      "artifacts": "optional",
      "powerSystem": "required",
      "foreshadowLedger": "required",
      "characterStateTracking": "required"
    }
  }
}
```

## 12. 命令与 owner 建议

### 12.1 Protocol 层

- `protocol/schema.py`
  - 新增 `project.emotionalContract`
  - 新增 `project.storyTemplate`
  - 新增 `worldbook`
  - 升级 `entities`
  - 升级 `foreshadowing`
- `protocol/files.py`
  - 新增 `worldbook` 到 `spec` 可解析状态文件

### 12.2 Commands 层

- `init`
  - 支持初始化 `emotionalContract` 与 `storyTemplate`
- `foreshadow`
  - 从 `plant/resolve/list` 升级为支持 `origin/payoff style/window`
- `entity`
  - 新增 `state-update` / `state-history`
- `doctor`
  - 支持 story-template-aware 校验

### 12.3 Services 层

- `context_lens.py`
  - 支持活跃世界规则、活跃伏笔窗口、角色状态切片
- `story_review.py`
  - 读取 `emotionalContract` / `foreshadowing` / `entity state`
- 若后续拆新 service，建议：
  - `services/story_constraints.py`
  - `services/foreshadow_engine.py`
  - `services/entity_state_engine.py`

## 13. 协议落地矩阵

### 13.1 状态域与 owner

| 状态域 | 文件 | owner | 作用 |
|------|------|------|------|
| `project.emotionalContract` | `project.yaml` | `protocol/schema.py` | 读者情绪体验承诺 |
| `project.storyTemplate` | `project.yaml` | `protocol/schema.py` | 决定哪些约束模块 required / optional / off |
| `worldbook` | `spec/worldbook.yaml` | `protocol/schema.py` + `protocol/files.py` | 世界真相层 |
| `entities.state` / `entities.changeLog` | `spec/entities.yaml` | `protocol/schema.py` | 角色动态状态与追溯 |
| `foreshadowing.origin/payoffPlan` | `spec/foreshadowing.yaml` | `protocol/schema.py` | 伏笔来源、窗口、显隐策略 |
| `threads` | `spec/threads.yaml` | `protocol/schema.py` | 主线/支线/人物线索引 |

### 13.2 命令面消费矩阵

| 命令/模块 | 应读取 | 用途 |
|------|------|------|
| `init` | `emotionalContract`, `storyTemplate` | 初始化作品级约束 |
| `doctor` | `storyTemplate`, `worldbook`, `entities.changeLog`, `foreshadowing.payoffPlan` | 结构与到期风险检查 |
| `outline check` | `storyTemplate`, `emotionalContract` | 写前门禁 |
| `context refresh` | `worldbook`, `threads`, `entities.state`, `foreshadowing` | 加载当前章最小必要约束 |
| `review chapter` | `emotionalContract`, `entities.state`, `foreshadowing` | 启发式评估情绪兑现与回收进度 |
| `review scene` | `emotionalContract`, `foreshadowing` | 局部场景的伏笔/情绪检查 |
| `entity` | `entities.state`, `entities.changeLog` | 状态更新与历史查询 |
| `foreshadow` | `foreshadowing.origin`, `foreshadowing.payoffPlan` | 伏笔台账管理 |

### 13.3 最小 schema 切片

建议不要一次把全部字段打满，而按以下最小切片落地：

#### Slice A: 作品级约束

- `project.emotionalContract`
- `project.storyTemplate`

#### Slice B: 世界真相层

- `worldbook.premiseFacts`
- `worldbook.worldRules`
- `worldbook.factions`

#### Slice C: 角色动态层

- `entities.state`
- `entities.changeLog`

#### Slice D: 伏笔账本增强

- `foreshadowing.origin`
- `foreshadowing.plantPoints`
- `foreshadowing.payoffPlan`

`v1.0` 最低要求是 Slice A + B + D 可以被 `doctor` / `context refresh` / `review` 基础消费。

## 14. 兼容迁移策略

### 14.1 老项目回填原则

- 缺失 `emotionalContract` 时回填空默认值
- 缺失 `storyTemplate` 时回填 `default` 模板或 `modulePolicy = optional`
- 缺失 `worldbook.yaml` 时允许加载为空状态
- 旧版 `entities.yaml` 没有 `state/changeLog` 时，保持 profile-only 模式
- 旧版 `foreshadowing.yaml` 没有 `origin/payoffPlan` 时，回填为最小兼容结构

### 14.2 不做一次性 breaking change

不建议在 `v1.0` 前：

- 强制所有旧项目立即补全 `worldbook`
- 强制所有角色都必须拥有 `state`
- 强制所有伏笔都必须立即细化到 `payoffPlan`

更稳的口径是：

- schema 可兼容
- `doctor` 先 warning
- 只有 `storyTemplate.modulePolicy = required` 的项目才逐步变成硬门禁

### 14.3 《归墟》作为重协议试点

《归墟》适合作为重协议试点，但不应要求所有项目都达到 `demo-guixu` 的维护密度。

建议口径：

- `demo-short-story`: 轻协议基线
- `demo-urban-occult-long`: 商业长篇基线
- `demo-guixu`: 重规则 + 长伏笔 + 角色动态基线

## 15. 实施顺序

### P0：协议落盘

- schema / file path / load-save 兼容
- 老项目缺省回填

### P1：静态检查

- `doctor`
- `outline check`

### P2：创作上下文

- `context refresh`
- `entity` / `foreshadow` 命令增强

### P3：评审闭环

- `review chapter`
- `review scene`

顺序理由：

- 先有协议，再有检查
- 先有检查，再让评审消费
- 先把“记得住”解决，再优化“判得准”

## 16. 验收口径

### 16.1 协议层完成的最低判断

以下条件满足时，才算“故事约束协议已经不是纯设计稿”：

- schema 与文件路径已落地
- 老项目可兼容加载
- 至少一个命令会真正消费新字段，而不是只写文档
- 至少一个样例项目写入新结构

### 16.2 `v1.0` 口径下的最低消费闭环

- `doctor` 能检查 `storyTemplate` required 模块
- `context refresh` 能加载最小的 `worldbook` / `entities.state` / `foreshadowing`
- `review chapter` 能引用 `emotionalContract` 或伏笔窗口

如果这三项都还没落地，就不能宣称“完整、有效的故事管理能力”已经完成。

## 17. 风险

### 17.1 过度结构化

风险：
作者被迫维护太多字段，创作负担过重。

缓解：

- 所有新模块都走 `storyTemplate.modulePolicy`
- `required` 才强校验，`optional` 只提醒，`off` 直接跳过

### 17.2 状态漂移

风险：
正文已变化，但 `entity state` / `foreshadow ledger` 未更新。

缓解：

- `doctor` 做弱提醒
- `context refresh` 优先提示“已到回收窗口但未处理”的项目

### 17.3 评审幻觉

风险：
把启发式评审误当成真实证明器。

缓解：

- 文档和输出中继续保留“启发式”口径
- 不把 `review scene` 冒充为逻辑证明器

## 18. 结论

这个设计的核心不是再多加几张表，而是把小说工程从：

- “只有角色和章节”

推进到：

- “有作品承诺”
- “有世界真相层”
- “有动态角色状态”
- “有带回收策略的伏笔账本”
- “有按题材启用的模块约束”
- “有面向读者情绪体验的协议”

对于《归墟》这类作品，真正需要的不是更大的 prompt，而是更清楚的真相入口、更明确的回收策略，以及能解释“为什么此刻该让读者感到紧张、怀疑、爽、释然”的结构化约束。
