# demo-light-novel-short

用于验证 Story Harness CLI 在“风格驱动短篇样例”上的两类能力：

- 定位层里的 `subGenre + styleTags + targetAudience`
- 端到端评审链路是否会保留并输出这些风格信号

## 项目定位

- 标题：`星铃与见习龙`
- 体量：3 章完结短篇
- 主类型：`fantasy`
- 子类型：`western-fantasy`
- 风格标签：`light-novel`、`short-fiction`
- 目标读者：`ya-reader`、`light-novel-reader`

## 适合验证的能力

- `review chapter` 是否在 `weightedScores.profile` 中保留 `light-novel`
- `projectContext.positioning` 与 `contractAlignment` 是否带出风格化定位
- `review scene` 是否能在轻快西幻短篇里评估场景功能、连续性与伏笔
- `doctor` 是否认可当前定位层字段与项目结构
- `export` 是否能正常导出完整稿件

## 当前基线观察

- `chapter-001` 章节回顾当前基线分为 `74/100`，加权后为 `77.25/100`
- `chapter-002` 章节回顾当前基线分为 `74/100`，加权后为 `76.65/100`
- `chapter-003` 章节回顾当前基线分为 `77/100`，加权后为 `78.95/100`
- `chapter-001 / scene-1` 已从低分片段优化到 `71/100`
- `chapter-001 / scene-2` 当前是一幕级最佳片段，得分 `89/100`
- 当前最顽固的低分维度已经从“冲突张力”转移到“情节推进 / 人物压力”，说明样例已从能跑提升到可优化闭环

## 推荐验证命令

```powershell
$env:PYTHONPATH='src'
python -m story_harness_cli doctor --root projects/demo-light-novel-short
python -m story_harness_cli chapter analyze --root projects/demo-light-novel-short --chapter-id chapter-001
python -m story_harness_cli review chapter --root projects/demo-light-novel-short --chapter-id chapter-001
python -m story_harness_cli review scene --root projects/demo-light-novel-short --chapter-id chapter-001 --scene-index 1
python -m story_harness_cli export --root projects/demo-light-novel-short --format markdown --output projects/demo-light-novel-short/manuscript.md
```

## 自动化回归入口

```powershell
$env:PYTHONPATH='src'
python -m unittest tests.smoke.test_demo_light_novel_short_sample -v
```

## 预期观察点

- `review chapter` 的 `weightedScores.profile` 应包含 `primaryGenre=fantasy`、`subGenre=western-fantasy`
- `review chapter` 的 `weightedScores.profile.styleTags` 应包含 `light-novel`
- `review scene --scene-index 1` 应聚焦“孵化事故”这一幕的功能、逻辑和风格承诺
- `doctor` 不应报结构性 error
