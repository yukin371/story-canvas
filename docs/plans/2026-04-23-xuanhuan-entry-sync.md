# 玄幻样例入口同步

> 日期: 2026-04-23
> 状态: 已完成

## 目标模块

- `README.md`
- `docs/guides/*`
- `docs/plans/*`

## 现有 owner

- 首页入口 owner: `README.md`
- 指南 owner: `docs/guides/*`
- 玄幻样例 owner: `projects/demo-xuanhuan-short/*`

## 影响面

- 用户是否能从首页和 quickstart 直接发现玄幻样例
- 样例矩阵之外的默认入口体验
- 不修改 CLI 行为，不新增依赖

## 计划改动

1. 在 `README.md` 增加 `demo-xuanhuan-short` 入口
2. 在 `docs/guides/quickstart.md` 增加玄幻样例运行和 fallback
3. 保持“首页/quickstart 只给入口，细节仍以下沉文档为准”这一边界

## 验证方式

- 读取 `README.md` 与 `docs/guides/quickstart.md`
- 对照 `projects/demo-xuanhuan-short/README.md` 与 `docs/guides/sample-matrix.md`
- 运行 `git diff --check -- README.md docs/guides/quickstart.md docs/plans/2026-04-23-xuanhuan-entry-sync.md`

## 验证结果

- 首页已补上 `demo-xuanhuan-short` 的直接运行入口
- quickstart 已补上玄幻样例的直接运行方式与 fallback
- 文档已明确：`demo-xuanhuan-short` 用于验证 `xuanhuan + web-serial` 权重与短篇升级驱动

## 残留风险

- README 现在已经有 4 条 quickstart 入口，后续样例继续增加时仍需要进一步压缩
- 样例详细说明依然分散在各自样例 README 中，后续需要继续以样例矩阵为统一入口
