# docs 模块说明

> 最后更新: 2026-04-23
> 状态: 当前有效模块文档

## 1. 模块职责

- 维护仓库级事实文档、路线图和文档入口
- 记录当前样例、当前执行入口和项目画像
- 为 guides / plans / tracking / protocol 等子模块提供上层导航

## 2. Owns

- `docs/roadmap.md`
- `docs/PROJECT_PROFILE.md`
- `docs/ARCHITECTURE_GUARDRAILS.md`
- `docs/*/`

## 3. 不变量

- `docs/roadmap.md` 是当前唯一执行入口
- `docs/PROJECT_PROFILE.md` 只记录高置信度事实
- 目录级入口文档应指向 canonical 子文档，而不是复制整份内容

## 4. 文档同步触发条件

- 样例工程矩阵变化
- 当前执行入口变化
- 项目定位或仓库拓扑变化
