# demo-short-story

用于验证 Story Canvas 工作流在“短篇完整项目”上的两类能力：

- 生成与回顾质量
- 端到端功能链路

## 项目定位

- 标题：`纸灯巷回声`
- 体量：3 章完结短篇
- 主类型：`mystery`
- 子类型：`urban-mystery`
- 风格标签：`short-fiction`

## 适合验证的能力

- `chapter analyze` 的实体识别、状态候选、关系候选
- `chapter suggest` / `review apply` / `projection apply` 的单章 loop
- `review chapter` 的定位层加权评分与契约对齐
- `review scene` 的显式 `scenePlans` 评审
- `doctor` 的项目结构校验
- `export` 的成品导出

## 已验证覆盖

- 3 章均已跑通 `chapter analyze`、`review chapter`、`context refresh`
- 6 幕均已跑通 `review scene`，覆盖每章 2 个显式 `scenePlans`
- 项目级命令 `doctor`、`review apply`、`projection apply`、`export` 已验证可用
- 自动化 smoke test 已接入 `tests/smoke/test_demo_short_story_sample.py`

## 当前基线观察

- `chapter-001` 章节回顾当前基线分为 `70/100`，主要暴露“冲突张力偏弱”
- `chapter-002` 章节回顾当前基线分为 `78/100`，是三章里推进最明确的一章
- `chapter-003` 章节回顾当前基线分为 `67/100`，结尾章依然会暴露“张力与人物压力不足”
- `chapter-002` 的 `chapter analyze` 当前会产出 2 个 `snapshotCandidates`，适合验证状态抽取
- 6 幕评审里最稳定的高分片段是 `chapter-002 / scene-2`，当前基线分为 `80/100`
- 多数一幕评审会把“伏笔与回收”列为优先改进项，适合验证片段级规则是否正常触发

## 推荐验证命令

```powershell
$env:PYTHONPATH='src'
python -m story_canvas doctor --root projects/demo-short-story
python -m story_canvas chapter analyze --root projects/demo-short-story --chapter-id chapter-001
python -m story_canvas chapter suggest --root projects/demo-short-story --chapter-id chapter-001
python -m story_canvas review apply --root projects/demo-short-story --chapter-id chapter-001 --all-pending --decision accepted
python -m story_canvas projection apply --root projects/demo-short-story --chapter-id chapter-001
python -m story_canvas context refresh --root projects/demo-short-story --chapter-id chapter-001
python -m story_canvas review chapter --root projects/demo-short-story --chapter-id chapter-001
python -m story_canvas review scene --root projects/demo-short-story --chapter-id chapter-001 --scene-index 1
python -m story_canvas export --root projects/demo-short-story --format markdown --output projects/demo-short-story/manuscript.md
```

## 全量回归命令

```powershell
$env:PYTHONPATH='src'
python -m story_canvas doctor --root projects/demo-short-story

foreach ($chapter in 'chapter-001', 'chapter-002', 'chapter-003') {
  python -m story_canvas chapter analyze --root projects/demo-short-story --chapter-id $chapter
  python -m story_canvas review chapter --root projects/demo-short-story --chapter-id $chapter
  python -m story_canvas context refresh --root projects/demo-short-story --chapter-id $chapter
}

foreach ($pair in @(
  @('chapter-001', 1), @('chapter-001', 2),
  @('chapter-002', 1), @('chapter-002', 2),
  @('chapter-003', 1), @('chapter-003', 2)
)) {
  python -m story_canvas review scene --root projects/demo-short-story --chapter-id $pair[0] --scene-index $pair[1]
}

python -m story_canvas review apply --root projects/demo-short-story --chapter-id chapter-001 --all-pending --decision accepted
python -m story_canvas projection apply --root projects/demo-short-story --chapter-id chapter-001
python -m story_canvas export --root projects/demo-short-story --format markdown --output projects/demo-short-story/manuscript.md
```

## 自动化回归入口

```powershell
$env:PYTHONPATH='src'
python -m unittest tests.smoke.test_demo_short_story_sample -v
```

## 预期观察点

- `chapter-001` 应该能稳定识别 `沈禾 / 陆川 / 沈岚 / 陈启明`
- `review chapter` 应该给出“小体量回收线索”和“情感回响”相关契约判断
- `review scene --scene-index 1` 应聚焦“雨夜来信”这一幕的功能、连续性和钩子
- `doctor` 不应报结构性 error
