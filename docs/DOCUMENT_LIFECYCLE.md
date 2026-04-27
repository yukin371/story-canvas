# Story Canvas 文档生命周期规则

> 最后更新: 2026-04-22
> 状态: 当前有效文档治理规则

## 1. 目的

本文件用于防止文档腐化、入口发散和历史资料误导当前开发。

## 2. 文档类别

| 类别 | 作用 | 是否可作为当前执行依据 |
|------|------|------|
| `docs/PROJECT_PROFILE.md` | 记录高置信度项目事实 | 否 |
| `docs/roadmap.md` | 记录当前真实状态 | **是**（唯一入口） |
| `docs/ARCHITECTURE_GUARDRAILS.md` | 记录长期架构边界 | 否 |
| 模块 `MODULE.md` | 记录模块职责与不变量 | 否 |
| `docs/plans/YYYY-MM-DD-*.md` | 临时实施方案 | 否 |
| `docs/adr/ADR-*.md` | 长期架构决策 | 否 |
| `docs/plans/*-design.md` | 设计背景材料 | 否（背景材料） |
| `docs/templates/` | 模板套件 | 否（参考模板） |
| `docs/AI_REPO_*.md` | 仓库初始化规则 | 否（引导文档） |

## 3. 文档状态

- **Current**: 当前唯一入口 → `docs/roadmap.md`
- **Background**: 可引用的背景材料 → PROJECT_PROFILE, ARCHITECTURE_GUARDRAILS, MODULE.md
- **Historical**: 仅供回溯 → 已完成的 plans, 旧 design docs
- **Template**: 模板 → `docs/templates/`

## 4. 更新触发条件

- 技术栈变化
- 当前阶段变化（v0.1 → v0.2 等）
- 模块职责变化
- 接口或依赖边界变化
- 验证门禁变化
- 发布方式变化

## 5. 降级规则

若文档不再是当前依据，应执行以下之一:

1. 补"历史状态说明"到文件头部
2. 收敛为 archive 正文 + stub 入口
3. 被新的当前入口替代

## 6. 禁止事项

- 禁止并列维护多个当前执行入口
- 禁止让历史文档继续使用"当前状态"口吻但不补说明
- 禁止长期堆积 plan 而不收敛
- 禁止删除仍有回溯价值的文档

## 7. 命名约定

- 设计 / 计划: `docs/plans/YYYY-MM-DD-<topic>.md`
- ADR: `docs/adr/ADR-XXX-<topic>.md`
- 模块文档: `src/<package>/MODULE.md`
