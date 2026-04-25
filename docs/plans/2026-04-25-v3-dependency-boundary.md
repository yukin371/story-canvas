# v3 外部依赖边界补充说明

> 日期：2026-04-25
> 状态：Superseded by `ADR-002`
> 关联文档：`docs/v3-plan.md`

## 1. 说明

本文件记录 v3 依赖边界的早期讨论。其核心结论已经被正式吸收进：

- `docs/adr/ADR-002-optional-dependencies-and-providers.md`
- `docs/ARCHITECTURE_GUARDRAILS.md`
- `docs/v3-plan.md`

## 2. 保留原因

保留本文件仅用于追溯当时的设计判断来源，包括：

- 为什么不应继续把所有算法、词表、提示词都硬编码在仓库内
- 为什么需要把 side-effecting provider client 和 `services/` 分层
- 为什么依赖策略应从“是否允许第三方依赖”改成“base + extras + packs”的分层问题

## 3. 当前有效结论

以 `ADR-002` 为准：

- `base install` 继续保持 stdlib-only
- 第三方库只允许作为 optional dependencies 引入
- `providers/` 是外部 API / SDK / optional dependency wrapper 的 canonical owner
- 词表、字典、prompt、review profile 允许通过 packs 外部化，但必须保留 builtin fallback
