# demo-urban-occult-long

`demo-urban-occult-long` 是仓库当前用于展示“商业化网站连载长篇样例”的 canonical 工程。

它不替代短篇样例的回归职责，而是补足另一块空白：

- 短篇样例负责验证命令链路和风格权重切换
- 这个长篇样例负责验证“项目定位 -> 卷级大纲 -> 单元案 -> 一幕评审 -> 上下文刷新”的真实长篇工作方式

## 项目定位

- 书名：`夜巡收煞录`
- 主类型：`fantasy`
- 子类型：`urban-occult`
- 风格标签：`web-serial`、`folk-occult`、`career-fiction`
- 目标读者：`qidian-reader`、`urban-fantasy-reader`、`folk-occult-reader`
- 目标平台：`qidian`

一句话 premise：

殡仪馆夜班接运员被迫接过父亲留下的城隍夜巡牌，在现代都市里处理民俗异案、追查旧城隍印失窃案，并一步步摸到父亲失踪背后的真相。

核心 hook line：

接尸抬到空棺的当夜，他被迫上岗做城隍夜巡。

连载蓝图：

- 更新节奏：`日更两章`
- 单章目标：最低 `2000` 字，建议 `3000` 字
- 钩子栈：`career-entry-hook`、`unit-case-payoff`、`mainline-escalation`、`cliffhanger-end`
- 连载模型：`2到3章一个单元异案，持续抬升旧城隍印、父亲失踪和执牌晋升三条主线`

## 为什么选这个方向

- 现有样例已经覆盖通用短篇、西幻轻小说短篇和玄幻短篇，但还缺一个更接近真实商业连载的长篇样例
- “都市玄幻 + 民俗志怪 + 职业线”适合做 `2-3` 章一个单元案，同时又能稳定抬主线
- 这种结构更适合验证 Story Canvas 工作流下的 `scenePlans`、连续性评审、伏笔管理和上下文刷新

## 当前样例范围

- 卷一：`第一卷 城隍夜班`
- 卷级骨架：12 章
- 已写正文：卷一 12 章
- 已维护：每章方向、beats、显式 `scenePlans`

## 当前基线观察

- `doctor --root projects/demo-urban-occult-long` 当前通过，结构检查 `errors=0`、`warnings=0`
- `outline.yaml` 当前维持 12 章卷级骨架，12 章都带显式 `scenePlans`
- `chapter-001` 已回补到 `2278` 字，章节回顾当前基线分为 `94/100`，加权后为 `97.25/100`
- `chapter-002` 已回补到 `3282` 字，章节回顾当前基线分为 `83/100`，加权后为 `83/100`
- `chapter-003` 已回补到 `3821` 字，章节回顾当前基线分为 `87/100`，加权后为 `89.75/100`
- `chapter-004` 已回补到 `3285` 字，章节回顾当前基线分为 `88/100`，加权后为 `89.75/100`
- `chapter-005` 已回补到 `3642` 字，章节回顾当前基线分为 `84/100`，加权后为 `84.25/100`
- `chapter-006` 已回补到 `3979` 字，章节回顾当前基线分为 `83/100`，加权后为 `81.5/100`
- `chapter-007` 已回补到 `3630` 字，章节回顾当前基线分为 `87/100`，加权后为 `87.5/100`
- `chapter-008` 已回补到 `4195` 字，章节回顾当前基线分为 `84/100`，加权后为 `87.5/100`
- `chapter-009` 章节回顾当前基线分为 `83/100`，加权后为 `82.25/100`
- `chapter-010` 章节回顾当前基线分为 `83/100`，加权后为 `82.25/100`
- `chapter-011` 章节回顾当前基线分为 `84/100`，加权后为 `83/100`
- `chapter-012` 章节回顾当前基线分为 `91/100`，加权后为 `95/100`
- `chapter-010 / scene-3` 当前基线分为 `81/100`
- `chapter-011 / scene-2` 当前基线分为 `83/100`
- `chapter-011 / scene-3` 当前基线分为 `78/100`
- `chapter-012 / scene-2` 当前基线分为 `86/100`
- `chapter-012 / scene-3` 当前基线分为 `80/100`
- `chapter-005 / scene-2` 当前基线分为 `80/100`
- `chapter-005 / scene-3` 当前基线分为 `87/100`
- `chapter-006 / scene-2` 当前基线分为 `79/100`
- `chapter-006 / scene-3` 当前基线分为 `84/100`
- `chapter-007 / scene-2` 当前基线分为 `95/100`
- `chapter-007 / scene-3` 当前基线分为 `88/100`
- `chapter-008 / scene-2` 当前基线分为 `91/100`
- `chapter-008 / scene-3` 当前基线分为 `80/100`
- `context refresh --chapter-id chapter-012` 当前可正常刷新到 `执牌上任`
- `stats --root projects/demo-urban-occult-long` 当前显示 `chaptersBelowMinimum=0`、`chaptersAtOrAboveMinimum=12`、`chaptersAtOrAboveRecommended=11`
- 当前残留重点不是章节过短，而是 `chapter-001` 仍低于建议字数线，以及评审启发式对个别商业钩子维度仍偏保守

## 适合验证的能力

- `doctor` 是否认可长篇项目结构和定位层
- `chapter analyze` 是否能从职业叙事与民俗正文里提实体和状态
- `review chapter` 是否能保留 `urban-occult + web-serial + folk-occult + career-fiction`
- `review scene` 是否能对显式一幕评估连续性、逻辑、伏笔和场景功能
- `context refresh` 是否能在连续章节后维持活跃角色与上下文
- `export` 是否能导出已经存在的长篇正文

## 推荐验证命令

```powershell
$env:PYTHONPATH='src'
python -m story_canvas doctor --root projects/demo-urban-occult-long
python -m story_canvas chapter analyze --root projects/demo-urban-occult-long --chapter-id chapter-012
python -m story_canvas review chapter --root projects/demo-urban-occult-long --chapter-id chapter-012
python -m story_canvas review scene --root projects/demo-urban-occult-long --chapter-id chapter-012 --scene-index 2
python -m story_canvas review scene --root projects/demo-urban-occult-long --chapter-id chapter-012 --scene-index 3
python -m story_canvas chapter suggest --root projects/demo-urban-occult-long --chapter-id chapter-012
python -m story_canvas review apply --root projects/demo-urban-occult-long --chapter-id chapter-012 --all-pending --decision accepted
python -m story_canvas projection apply --root projects/demo-urban-occult-long --chapter-id chapter-012
python -m story_canvas context refresh --root projects/demo-urban-occult-long --chapter-id chapter-012
python -m story_canvas export --root projects/demo-urban-occult-long --format markdown --output projects/demo-urban-occult-long/manuscript.md
python -m unittest tests.smoke.test_demo_urban_occult_long_sample -v
```

## 预期阅读感

- 开场就带职业质感，不先长篇空转讲设定
- 每章都有案件推进或主线认知抬升
- 每 `2-3` 章能完成一个单元异案结算
- 章节末尾保留追读钩子，适配网站连载节奏

## 后续扩展方式

- 卷一已经完成，若继续扩写，优先新建卷二骨架而不是回头把卷一拖成长中篇
- 每补完一章，按 `outline check -> analyze -> review chapter -> review scene -> suggest/apply -> projection -> context refresh` 闭环跑一次
- 若继续往真实商业作品推进，下一步应优先决定是继续写卷二，还是再对 `chapter-001` 做一次建议字数线层面的精修
- 不要把它改写成单次完结中篇；它的设计目标就是连载型长篇样例
