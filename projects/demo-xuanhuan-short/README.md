# demo-xuanhuan-short

用于验证 Story Canvas 工作流在“玄幻网文短篇样例”上的两类能力：

- `xuanhuan + web-serial` 定位是否进入评审链路
- 玄幻短篇的推进、压制、反压制与小型升级闭环

## 项目定位

- 标题：`炉火照天门`
- 体量：3 章完结短篇
- 主类型：`fantasy`
- 子类型：`xuanhuan`
- 风格标签：`web-serial`
- 目标读者：`qidian-reader`、`progression-fantasy-reader`

## 适合验证的能力

- `review chapter` 是否在 `weightedScores.profile` 中保留 `xuanhuan`
- `review chapter` 是否把“推进 / 张力 / 体系感”推到更高权重
- `review scene` 是否能在玄幻片段里评估场景功能、连续性、伏笔与兑现
- `doctor` 是否认可定位层字段与项目结构
- `export` 是否能正常导出完整稿件

## 当前基线观察

- `doctor --root projects/demo-xuanhuan-short` 当前通过，结构检查 `errors=0`、`warnings=0`
- `chapter-001` 章节回顾当前基线分为 `76/100`，加权后为 `76.15/100`
- `chapter-002` 章节回顾当前基线分为 `87/100`，加权后为 `87/100`
- `chapter-003` 章节回顾当前基线分为 `85/100`，加权后为 `83.8/100`
- `chapter-001 / scene-1` 当前基线分为 `66/100`，已从低分片段抬升到可用片段
- `chapter-002 / scene-1` 当前基线分为 `87/100`，已能稳定体现压名、动机、逻辑与钩子
- `chapter-002 / scene-2` 当前基线分为 `85/100`，已经能稳定体现反压、兑现与场景承接
- `chapter-003 / scene-2` 当前基线分为 `76/100`，已经能稳定体现推进、兑现与钩子
- 这个样例目前既可验证“玄幻权重切换与网文节奏口径”，也已经具备较均衡的三章短篇基线

## 推荐验证命令

```powershell
$env:PYTHONPATH='src'
python -m story_canvas doctor --root projects/demo-xuanhuan-short
python -m story_canvas chapter analyze --root projects/demo-xuanhuan-short --chapter-id chapter-001
python -m story_canvas review chapter --root projects/demo-xuanhuan-short --chapter-id chapter-001
python -m story_canvas review scene --root projects/demo-xuanhuan-short --chapter-id chapter-001 --scene-index 1
python -m story_canvas export --root projects/demo-xuanhuan-short --format markdown --output projects/demo-xuanhuan-short/manuscript.md
```

## 自动化回归入口

```powershell
$env:PYTHONPATH='src'
python -m unittest tests.smoke.test_demo_xuanhuan_short_sample -v
```

## 预期观察点

- `review chapter` 的 `weightedScores.profile` 应包含 `primaryGenre=fantasy`、`subGenre=xuanhuan`
- `review chapter` 的 `weightedScores.profile.styleTags` 应包含 `web-serial`
- `review scene --scene-index 1` 应聚焦“废炉领罚”这一幕的压制建立、体系信息和反击预热
- `doctor` 不应报结构性 error
