# v1.0 验收与故事协议细化计划

> 日期: 2026-04-25
> 状态: 已完成
> 范围: `docs/releases/`、`docs/plans/2026-04-25-story-constraint-protocol.md`

## 1. 目标

本轮补两类文档：

1. `v1.0` 发布验收文档
2. 故事约束协议的可实施细化文档

## 2. 产出物

- `docs/releases/v1.0-acceptance.md`
- 更新 `docs/plans/2026-04-25-story-constraint-protocol.md`

## 3. 补强重点

### 3.1 `v1.0` 验收文档

- 把 `docs/roadmap.md` 中的发布目标变成可打勾清单
- 明确 Must / Should / Out of Scope
- 明确样例矩阵、验证方式、阻塞项、发布结论口径

### 3.2 故事约束协议细化

- 将字段设计推进到协议落地顺序
- 增加 state domain / owner / command surface 对照
- 增加兼容迁移策略
- 增加 `doctor` / `outline check` / `review` / `context refresh` 各自读取哪些字段

## 4. 风险

- 文档可能先于代码实现，必须避免写成“已实现”
- 当前工作树存在大量并行改动，文档需保持为设计与验收口径，避免误导为真实完成态

## 5. 完成条件

- `v1.0` 文档可直接作为发布前 checklist 使用
- 故事约束协议文档可直接拆成后续实现任务
