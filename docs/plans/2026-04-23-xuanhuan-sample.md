# 玄幻短篇样例落地

> 日期: 2026-04-23
> 状态: 已完成

## 目标模块

- `projects/demo-xuanhuan-short/*`
- `tests/smoke/*`
- `docs/guides/*`
- `docs/roadmap.md`
- `docs/PROJECT_PROFILE.md`

## 现有 owner

- 样例矩阵 owner: `docs/guides/sample-matrix.md`
- 风格样例 owner: `projects/demo-light-novel-short/*`
- 通用短篇基线 owner: `projects/demo-short-story/*`
- smoke 样例验证 owner: `tests/smoke/*`

## 影响面

- 把样例矩阵中的 `TBD` 变成真实玄幻基线
- 为 `xuanhuan` 的定位层输出提供真实样例与自动化回归
- 不修改 CLI 行为，不新增依赖

## 计划改动

1. 创建 `demo-xuanhuan-short` 工程骨架
2. 写入 `xuanhuan + web-serial` 定位、3 章结构与显式 `scenePlans`
3. 增加样例说明与模块文档
4. 增加对应 smoke test
5. 同步样例矩阵、路线图与项目画像

## 验证方式

- `python -m story_harness_cli doctor --root projects/demo-xuanhuan-short`
- `python -m story_harness_cli chapter analyze --root projects/demo-xuanhuan-short --chapter-id chapter-001`
- `python -m story_harness_cli review chapter --root projects/demo-xuanhuan-short --chapter-id chapter-001`
- `python -m story_harness_cli review scene --root projects/demo-xuanhuan-short --chapter-id chapter-001 --scene-index 1`
- `python -m unittest tests.smoke.test_demo_xuanhuan_short_sample -v`

## 当前风险

- 玄幻样例如果只换标签不换叙事结构，会导致评审信号不明显
- 新样例必须维持 JSON-compatible YAML 和显式 `scenePlans`

## 验证结果

- `python -m story_harness_cli doctor --root projects/demo-xuanhuan-short` 通过，`errors=0`、`warnings=0`
- `python -m story_harness_cli review chapter --root projects/demo-xuanhuan-short --chapter-id chapter-001` 已输出 `primaryGenre=fantasy`、`subGenre=xuanhuan`、`styleTags=["web-serial"]`
- `python -m story_harness_cli review scene --root projects/demo-xuanhuan-short --chapter-id chapter-001 --scene-index 1` 通过，显式读取 `scenePlans`
- `python -m unittest tests.smoke.test_demo_xuanhuan_short_sample -v` 通过
- 优化后 `chapter-001` 从 `58/100` 提升到 `76/100`，加权分从 `48.85` 提升到 `76.15`
- 优化后 `chapter-002` 从 `67/100` 提升到 `87/100`，加权分从 `61.75` 提升到 `87`
- 优化后 `chapter-003` 从 `61/100` 提升到 `85/100`，加权分从 `57.85` 提升到 `83.8`
- 优化后 `chapter-001 / scene-1` 从 `45/100` 提升到 `66/100`
- 优化后 `chapter-002 / scene-1` 从 `58/100` 提升到 `87/100`
- 优化后 `chapter-002 / scene-2` 从 `60/100` 提升到 `85/100`
- 优化后 `chapter-003 / scene-2` 达到 `76/100`
