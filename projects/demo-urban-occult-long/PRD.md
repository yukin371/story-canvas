# PRD: 夜巡收煞录

> 最后更新: 2026-04-24
> 产品阶段: 开发中（卷一已完稿）
> Story Canvas 版本: v0.2

---

## 1. 产品定义

| 字段 | 内容 |
|------|------|
| 书名 | 夜巡收煞录 |
| 主类型 | `fantasy` |
| 子类型 | `urban-occult` |
| 风格标签 | `web-serial` / `folk-occult` / `career-fiction` |
| 目标平台 | 起点中文网 |
| 目标读者 | 18-30 岁男性，偏好都市玄幻、民俗志怪、职业线题材的网文读者 |
| 目标字数 | 50 万字（多卷连载） |

### 1.1 一句话 premise

> 殡仪馆夜班接运员意外继承父亲留下的城隍夜巡差事，在一座现代都市里处理民俗异案、追查旧城隍印失窃案，并一步步摸到失踪父亲留下的真相。

### 1.2 hook line

> 接尸抬到空棺的当夜，他被迫上岗做城隍夜巡。

### 1.3 核心卖点

1. **每章结尾保留追读钩子** — 适配日更连载节奏，章章有悬念
2. **2-3 章一个单元异案** — 节奏紧凑，持续制造小高潮
3. **职业线 + 民俗志怪双重硬核设定** — 殡葬行业真实质感 + 中式民俗异案体系

---

## 2. 商业连载蓝图

| 字段 | 内容 |
|------|------|
| 连载模型 | 网站连载型长篇，2-3 章一个单元异案，持续抬升主线 |
| 更新频率 | 日更两章 |
| 单章字数底线 | 2000 字 |
| 单章字数建议 | 3000 字 |
| 钩子栈 | `career-entry-hook`, `unit-case-payoff`, `mainline-escalation`, `cliffhanger-end` |
| 对标作品 | 都市职业捉诡文 / 民俗单元案连载文 / 中式志怪成长文 |

### 2.1 故事契约

- 核心承诺:
  - 每 2-3 章解决一个单元异案并抬升主线认知
  - 职业流程必须持续制造冲突、线索和代价
  - 每章结尾保留一个足以支撑连载追读的钩子
- 避免事项:
  - 只堆民俗设定不推动案件
  - 主角长期被动旁观
- 结局承诺: 卷一完成从临时夜巡到正式执牌人的跃迁，并确认父亲失踪与旧城隍案有关
- 节奏承诺: 中快节奏

### 2.2 AI 协作与风格控制

| 字段 | 内容 |
|------|------|
| 生成模式 | AI 辅助，作者定方向与终审，允许局部 AI 起稿后精修 |
| 默认 style profile | `web-serial-zh` |
| 生成时约束 | 禁止连续 3 段相似开头；减少“微微/缓缓/不禁”等模糊副词；避免空转抒情盖过案件推进 |
| 发布前风格门槛 | `styleAnalysis.totalDeduction <= 3` |
| 超阈值修复策略 | 先跑 `style constraints`，针对问题段落重写，再用 `style check` 或 `review chapter` 复检 |

- 写前要求:
  - 起稿 prompt 需要显式带入本章追读钩子、职业线推进和当前风格约束
  - AI 不得只写氛围句而不推进案件信息
- 写后要求:
  - `review chapter` 中的 `styleAnalysis` 视为正式门禁结果
  - 若风格扣分过高，必须先修复再进入发布态

### 2.3 视觉资产与插图策略

| 字段 | 内容 |
|------|------|
| 插图目标 | 角色设定图、卷级宣传图、章节高潮插图 |
| 生成模式 | 文生图为主，图生图用于角色定稿后延续一致性 |
| 首选 adapter | OpenAI |
| 首选 model | 当前部署环境可用时优先 `gpt-image-2` |
| 参考图来源 | 人物设定卡、已采用角色图、作者手绘草图 |
| 频率与预算 | 每卷 2-4 张重点图；单章只在高潮节点出图 |
| 审核规则 | 人物职业属性、民俗器物、都市时代感和剧透边界必须人工复核 |

- 资产要求:
  - 正式采用的插图必须保留 prompt、reference、model 和生成时间
  - 图生图只能基于本项目已确认的角色资产或作者提供草图

---

## 3. 产出物标准

### 3.1 卷级结构

| 卷 | 章节范围 | 卷标题 | 主要事件 |
|----|---------|--------|---------|
| 卷一 | ch-001 ~ ch-012 | 城隍夜班 | 主角接手夜巡牌，处理首批异案，发现旧城隍印线索 |
| 卷二 | ch-013 ~ ch-024 | TBD | TBD |

### 3.2 文件组织规范

当前使用扁平结构（v0.2 协议），后续迁移至分层结构（v0.3）。

当前结构:
```
demo-urban-occult-long/
├── project.yaml          # 定位数据（含商业蓝图）
├── outline.yaml          # 大纲（12 章卷级骨架 + scenePlans）
├── entities.yaml         # 人物设定
├── timeline.yaml         # 时间线
├── threads.yaml          # 主线/支线
├── structures.yaml       # 结构定义
├── branches.yaml         # 分支管理
├── chapters/             # 正文
├── proposals/            # 写前提案
├── reviews/              # 评审记录
├── projections/          # 投影与上下文
├── logs/                 # 运行日志
├── manuscript.md         # 导出（markdown）
└── PRD.md                # 本文件
```

### 3.3 章节要求

- 每章必须维护显式 `scenePlans`
- 每章必须通过 `doctor` 检查
- 字数不低于 2000 字，建议 3000 字

---

## 4. 质量门禁

### 4.1 提交前检查（每章）

| 检查项 | 命令 | 通过条件 |
|--------|------|---------|
| 结构完整性 | `doctor` | errors=0, warnings=0 |
| 写前约束 | `style constraints` | 已确认本章风格约束与商业钩子要求 |
| 章节分析 | `chapter analyze` | 实体提取正常 |
| AI 风格检测 | `style check` 或 `review chapter` 中 `styleAnalysis` | `totalDeduction <= 3` |
| 章节评审 | `review chapter` | 加权分 >= 80/100 |
| 一幕评审 | `review scene` | 每个 scene >= 75/100 |
| 一致性 | `consistency check` | 无冲突 |

### 4.2 单卷交付检查

- [ ] 所有章节通过提交前检查
- [ ] `stats` 显示无低于 2000 字的章节
- [ ] `outline check` 通过
- [ ] `export` 成功生成卷正文

### 4.3 当前基线评分

| 章节 | 基线分 | 加权分 |
|------|--------|--------|
| ch-001 | 94 | 97.25 |
| ch-002 | 83 | 83 |
| ch-003 | 87 | 89.75 |
| ch-004 | 88 | 89.75 |
| ch-005 | 85 | 84.5 |
| ch-006 | 83 | 81.5 |
| ch-007 | 87 | 87.5 |
| ch-008 | 85 | 87.75 |
| ch-009 | 83 | 82.25 |
| ch-010 | 83 | 82.25 |
| ch-011 | 84 | 83 |
| ch-012 | 91 | 95 |

全部达到 80 分以上的交付标准。

---

## 5. 验收标准

### 5.1 单章交付条件

1. `doctor` 通过（errors=0）
2. `review chapter` 加权分 >= 80
3. `styleAnalysis.totalDeduction <= 3`
4. 字数 >= 2000
5. `context refresh` 可正常刷新到下一章

### 5.2 单卷交付条件（卷一当前状态）

1. ✅ 卷内所有章节通过单章交付条件
2. ✅ `stats` 显示 `chaptersBelowMinimum=0`、`chaptersAtOrAboveRecommended=11`
3. ✅ `export` 可导出完整卷正文
4. ✅ 主线/支线状态与 `outline.yaml` 一致

### 5.3 完结交付条件

1. 所有卷通过单卷交付条件
2. 故事契约中的核心承诺全部兑现
3. 结局承诺兑现
4. 全文导出成功

---

## 6. 工具支撑

### 6.1 推荐写作闭环

```
outline check → style constraints → chapter write / AI draft → style check →
review chapter → review scene → style repair / chapter suggest → review apply →
projection apply → context refresh → workflow advance → (下一章)
```

### 6.2 命令矩阵

| 阶段 | 命令 | 用途 |
|------|------|------|
| 规划 | `outline propose/promote/check` | 大纲管理 |
| 场景 | `outline scene-add/scene-list/scene-detect` | 场景边界维护 |
| 细纲 | `outline beat-add/beat-complete/beat-list` | 细纲追踪 |
| 风格 | `style check/constraints/report` | 生成约束、风格检测与聚合 |
| 分析 | `chapter analyze` | 章节分析（实体提取） |
| 评审 | `review chapter/scene` | 章节与一幕评审 |
| 状态机 | `workflow status/run/advance/reset/export` | 显式推进当前 gate |
| 建议 | `chapter suggest` | 生成改进建议 |
| 应用 | `review apply` | 应用/拒绝变更请求 |
| 投影 | `projection apply` | 更新投影 |
| 插图（v3 规划） | `illustration prompt/generate/list/config` | 章节图、角色图和图生图资产管理 |
| 上下文 | `context refresh/show` | 刷新写作上下文 |
| 检查 | `doctor` | 项目结构校验 |
| 统计 | `stats` | 项目统计 |
| 导出 | `export --format md/txt/json` | 多格式导出 |

---

## 7. 当前状态

### 7.1 进度

| 指标 | 值 |
|------|-----|
| 活跃卷 | 卷一（已完成） |
| 已完成章节 | 12/12（卷一） |
| 活跃章节 | chapter-012（卷一最后一章） |
| 总字数 | 全部达到底线，11/12 达到建议线 |

### 7.2 已知问题

- chapter-001 仍低于建议字数线（2278 字 vs 3000 字建议），质量评分已达标
- 评审启发式对个别商业钩子维度仍偏保守
- 长篇规格文件未拆分，后续卷增加后需要按卷拆分（见 v0.3 路线）

### 7.3 下一步

- 决定是否继续写卷二，或对卷一做精修
- 若继续卷二，优先创建卷二骨架，不要回头拖长卷一
- 评估迁移到分层文件结构（spec/drafts/workflow/exports）
