# 2026-04-29 AI 实施痛点长期追踪治理

## 背景

近期真实流程已经不止一次暴露出同一类问题：

1. 临时痛点被写进 `docs/plans/*.md`，但后续缺少统一回看入口。
2. 新一轮实施前，agent 往往需要重新翻多份历史 plan，才能判断哪些痛点还存在。
3. 某些临时审查或缺口记录实际上已经被代码和 CLI 收口，但文档仍停留在“待实施/当前缺口”的口吻。

这会增加 AI 的上下文负担，也会让历史文档继续冒充当前有效输入。

## 适用规则

- 当前执行入口：`docs/roadmap.md`
- 文档生命周期：`docs/DOCUMENT_LIFECYCLE.md`
- docs 模块不变量：`docs/MODULE.md`
- 仓库级规则：`AGENTS.md`

## 目标模块

- `docs/tracking/`
- `docs/DOCUMENT_LIFECYCLE.md`
- `AGENTS.md`
- 必要的历史 `docs/plans/*.md`

## 计划改动

1. 新建一个长期有效的 AI 实施痛点追踪文档，作为后续真实实施前的固定检查入口。
2. 把“实施前检查痛点 tracker、实施后回写状态”的要求写入仓库规则。
3. 对已经被收口或已完成迁移的临时痛点/审查文档补历史状态说明，避免继续以“当前缺口”口吻误导。

## 验证方式

1. 新 tracker 必须能区分：
   - 当前活跃痛点
   - 已解决并归档的历史痛点
   - 仅作为来源的历史临时文档
2. `AGENTS.md` 与 `docs/DOCUMENT_LIFECYCLE.md` 必须明确：
   - 何时检查 tracker
   - 何时把临时文档降级为历史资料
3. 至少 3 份历史 plan 要补充清晰的历史状态头。

## 需要同步的文档

- `AGENTS.md`
- `docs/MODULE.md`
- `docs/PROJECT_PROFILE.md`
- `docs/DOCUMENT_LIFECYCLE.md`
- 新增 `docs/tracking/ai-friction-tracker.md`

## 风险

- 若把 tracker 写成第二个 roadmap，会违反“唯一当前入口”规则。
- 若不区分“活跃痛点”与“历史来源”，后续仍会继续翻大量旧 plan。

## 回滚路径

- 本轮只新增治理文档和历史状态说明，不改代码协议。
- 若 tracker 结构不合适，可只回退规则同步，保留历史状态头和来源链路。
