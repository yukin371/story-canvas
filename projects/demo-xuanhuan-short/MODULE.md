# demo-xuanhuan-short 模块说明

> 最后更新: 2026-04-23
> 状态: 当前有效模块文档

## 1. 模块职责

- 提供一个“玄幻网文短篇”标准样例
- 用于验证 `xuanhuan + web-serial + targetAudience` 是否进入评审链路
- 用于验证短篇在 `doctor/analyze/review/export` 下的完整闭环

## 2. Owns

- `project.yaml` 中的定位层与故事契约
- `outline.yaml` 中的 3 章结构、beats 与 `scenePlans`
- `chapters/*.md` 中的样例正文
- `README.md` 中的验证入口

## 3. 不变量

- 所有 `.yaml` 内容必须保持 JSON-compatible
- 必须维持 3 章完结短篇的项目形状
- 每章至少 2 个显式 `scenePlans`
- 评审输出应能保留 `fantasy + xuanhuan + web-serial`

## 4. 文档同步触发条件

- 样例定位变化
- 章节结构变化
- 评审/验证入口变化
