# 小说工程初始化规范

> 最后更新: 2026-04-23
> 目的: 在项目初始化阶段就声明作品定位、目标读者和故事承诺，把小说按“工程项目”管理

## 1. 为什么要在初始化时确定这些信息

如果把小说当工程项目，`类型`、`目标群体`、`故事承诺` 就相当于软件项目里的：

- 技术栈
- 目标用户
- 产品承诺
- 验收标准

它们不应该只存在于作者脑中，也不应该等到写了几章之后再反推。

在 Story Canvas 里，这些信息现在统一落在 `project.yaml` 的三个块中：

- `positioning`
- `storyContract`
- `commercialPositioning`

## 2. 数据结构

```json
{
  "title": "雾港疑案",
  "genre": "奇幻",
  "defaultMode": "driving",
  "activeChapterId": "chapter-001",
  "positioning": {
    "primaryGenre": "fantasy",
    "subGenre": "xuanhuan",
    "styleTags": ["light-novel", "web-serial"],
    "targetAudience": ["male-young-adult", "web-serial-reader"]
  },
  "storyContract": {
    "corePromises": ["升级成长明确", "每三章至少一个兑现点"],
    "avoidances": ["长时间无主线推进"],
    "endingContract": "阶段性胜利+保留更大危机",
    "paceContract": "快节奏"
  },
  "commercialPositioning": {
    "premise": "宗门弃子在残卷指引下踏上升级复仇之路",
    "hookLine": "废柴少爷觉醒残卷传承，每三章一跃迁，步步掀翻旧秩序。",
    "hookStack": ["upgrade-payoff", "cliffhanger-end"],
    "benchmarkWorks": ["升级流玄幻长篇", "宗门竞争成长文"],
    "targetPlatform": "qidian",
    "serializationModel": "强升级主线 + 阶段性地图扩张 + 卷末晋阶兑现",
    "releaseCadence": "日更两章",
    "chapterWordFloor": 2000,
    "chapterWordTarget": 3000
  }
}
```

## 3. 字段解释

### 3.1 positioning

用于回答“这部作品是什么，写给谁”。

| 字段 | 含义 | 示例 |
|------|------|------|
| `primaryGenre` | 主类型 | `fantasy`, `mystery`, `romance` |
| `subGenre` | 子类型 | `xuanhuan`, `western-fantasy`, `space-opera` |
| `styleTags` | 风格/市场标签 | `light-novel`, `web-serial`, `grimdark` |
| `targetAudience` | 目标读者 | `male-young-adult`, `female-adult`, `ya-reader` |

### 3.2 storyContract

用于回答“这部作品向读者承诺什么，不承诺什么”。

| 字段 | 含义 | 示例 |
|------|------|------|
| `corePromises` | 持续输出的核心卖点 | `感情拉扯强`, `高频反转`, `升级成长明确` |
| `avoidances` | 明确避免的体验 | `长时间无主线推进`, `世界观讲课过重` |
| `endingContract` | 结局形态承诺 | `HE`, `开放但情感闭合`, `阶段性胜利` |
| `paceContract` | 整体节奏承诺 | `慢热`, `中速`, `快节奏` |

### 3.3 commercialPositioning

用于回答“这部作品要如何作为商业连载交付”。这不是 marketing 附件，而是工程约束。

| 字段 | 含义 | 示例 |
|------|------|------|
| `premise` | 一句话 premise / 电梯陈述 | `夜班接尸人继承城隍夜巡牌` |
| `hookLine` | 对外可复用的核心钩子 | `接尸抬到空棺的当夜，他被迫上岗做城隍夜巡。` |
| `hookStack` | 持续制造追读动力的钩子栈 | `career-entry-hook`, `cliffhanger-end` |
| `benchmarkWorks` | 对标作品或参考样板 | `都市职业捉诡文`, `民俗单元案连载文` |
| `targetPlatform` | 主要投放平台 | `qidian`, `jjwxc` |
| `serializationModel` | 连载推进模型 | `2到3章一个单元异案，持续抬升主线阴谋` |
| `releaseCadence` | 更新频率承诺 | `日更两章`, `周更五章` |
| `chapterWordFloor` | 单章最低交付字数 | `2000` |
| `chapterWordTarget` | 单章建议目标字数 | `3000` |

## 4. init 命令写法

最小示例：

```powershell
uv run story-canvas init --root .\demo --title "Fog Harbor" --genre "Mystery"
```

带完整定位信息的示例：

```powershell
uv run story-canvas init `
  --root .\demo `
  --title "雾港疑案" `
  --genre "奇幻" `
  --primary-genre fantasy `
  --sub-genre xuanhuan `
  --style-tag light-novel `
  --style-tag web-serial `
  --target-audience male-young-adult `
  --target-audience web-serial-reader `
  --core-promise "升级成长明确" `
  --core-promise "每三章至少一个兑现点" `
  --avoidance "长时间无主线推进" `
  --ending-contract "阶段性胜利+保留更大危机" `
  --pace-contract "快节奏" `
  --premise "宗门弃子在残卷指引下踏上升级复仇之路" `
  --hook-line "废柴少爷觉醒残卷传承，每三章一跃迁，步步掀翻旧秩序。" `
  --hook-stack upgrade-payoff `
  --hook-stack cliffhanger-end `
  --benchmark-work "升级流玄幻长篇" `
  --target-platform qidian `
  --serialization-model "强升级主线 + 阶段性地图扩张 + 卷末晋阶兑现" `
  --release-cadence "日更两章" `
  --chapter-word-floor 2000 `
  --chapter-word-target 3000
```

## 5. 使用建议

### 5.1 初始化时先填到什么程度

建议至少填：

- `primaryGenre`
- `targetAudience`
- `corePromises`
- `paceContract`

如果你已经明确更细的市场定位，再填：

- `subGenre`
- `styleTags`
- `endingContract`
- `avoidances`

如果你准备按商业连载方式交付，再补：

- `premise`
- `hookLine`
- `hookStack`
- `targetPlatform`
- `serializationModel`
- `releaseCadence`
- `chapterWordFloor`
- `chapterWordTarget`

### 5.2 如何和类型评审表配合

- `positioning` 负责定义作品类别
- [genre-review-rubric.md](/E:/Github/story-harness-cli/docs/guides/genre-review-rubric.md) 负责定义这一类别应该怎么评
- `review chapter` 现已读取这些字段，额外输出 `weightedScores`、`contractAlignment` 与 `commercialAlignment`

### 5.3 如何理解 `genre` 与 `primaryGenre`

- `genre`: 保留给项目的人类可读总类目，兼容现有仓库用法
- `primaryGenre`: 更适合机器处理，建议使用稳定英文枚举或约定俗成的 slug；`init` 默认会把常见 genre 自动归一

示例：

- `genre = "奇幻"`
- `primaryGenre = "fantasy"`
- `subGenre = "xuanhuan"`

## 6. 推荐工作流

初始化时：

1. 先选主类型
2. 再选子类型或风格标签
3. 明确目标读者
4. 写下卖点和禁忌项
5. 如果是商业连载，写下 premise、hook、平台和更新节奏
6. 再开始 outline / chapter 工作流

写作中：

1. 用 `storyContract` 检查是否偏离承诺
2. 用 chapter review 看工艺质量
3. 后续再用类型化 review 看“产品是否还像原来承诺的那个作品”

## 7. 当前边界

目前仓库已支持：

- 在 `init` 时写入 `positioning` 与 `storyContract`
- 在 `init` 时写入 `commercialPositioning`
- 老项目加载时自动补齐缺省字段
- `review chapter` 依据 `primaryGenre` / `subGenre` / `styleTags` / `commercialPositioning.targetPlatform` 输出 `weightedScores`
- `review chapter` 输出 `projectContext`、`contractAlignment` 与 `commercialAlignment`
- `review scene` 已输出场景级 `projectContext`、`contractAlignment` 与 `commercialAlignment`
- `outline scene-detect` 可把启发式候选场景落成显式 `scenePlans`
- `doctor` 对缺失的定位层/故事契约字段给出提示
- `doctor` 对商业连载项目额外检查 `premise`、hook、平台、连载模型、更新节奏和章节字数目标

目前尚未支持：

- 更细粒度的场景级伏笔/连续性/逻辑自动校验
