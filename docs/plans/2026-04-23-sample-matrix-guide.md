# 样例矩阵入口收口

> 日期: 2026-04-23
> 状态: 已完成

## 目标模块

- `docs/guides/*`
- `README.md`
- `docs/plans/*`

## 现有 owner

- 指南 owner: `docs/guides/*`
- 首页入口 owner: `README.md`
- 样例项目 owner: `projects/demo-short-story/*`、`projects/demo-light-novel-short/*`

## 影响面

- 样例工程的发现路径
- README / quickstart / workflow 三处是否继续并行维护样例说明
- 不修改 CLI 行为，不新增依赖

## 计划改动

1. 新增 `docs/guides/sample-matrix.md`
2. 把 README、quickstart、workflow 中的样例说明收敛为摘要 + 链接
3. 为后续玄幻等题材样例预留统一登记入口

## 验证方式

- 读取 `docs/guides/sample-matrix.md`
- 对照 `projects/demo-short-story/README.md`、`projects/demo-light-novel-short/README.md`、`docs/roadmap.md`
- 运行 `git diff --check -- README.md docs/guides/quickstart.md docs/guides/creative-workflow.md docs/guides/sample-matrix.md docs/plans/2026-04-23-sample-matrix-guide.md`

## 验证结果

- 新增了统一的样例矩阵页，已覆盖通用短篇基线、风格化短篇基线和后续 TBD 入口
- README、quickstart、creative-workflow 已统一指向样例矩阵页
- 文档已明确：新增题材样例时，先登记矩阵，再决定是否进入首页

## 残留风险

- 玄幻等更多样例仍未落地，矩阵中的 `TBD` 还只是预留位
- 首页虽然已收口，但仍保留了两个样例命令块；后续样例继续增多时，README 仍需进一步压缩
