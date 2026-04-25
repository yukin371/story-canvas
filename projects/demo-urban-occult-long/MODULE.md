# demo-urban-occult-long 模块说明

> 最后更新: 2026-04-23
> 状态: 当前有效模块文档

## 1. 模块职责

- 提供一个“商业化网站连载长篇”标准样例
- 用于验证 `urban-occult + web-serial + folk-occult + career-fiction` 的定位层是否进入评审链路
- 用于验证长篇项目在 `doctor/analyze/review/context/export` 下的闭环

## 2. Owns

- `project.yaml` 中的长篇定位层、故事契约和商业化 premise
- `outline.yaml` 中的卷级结构、12 章方向、beats 与显式 `scenePlans`
- `entities.yaml` 中的主角组与主线缺席核心
- `chapters/*.md` 中的 12 章卷一正文
- `README.md` 中的验证入口

## 3. 不变量

- 所有 `.yaml` 内容必须保持 JSON-compatible
- 该样例必须维持“长篇连载骨架 + 已写开篇弧线”的项目形状，而不是退化成长一点的短篇
- 已写章节必须维护显式 `scenePlans`
- 评审输出应能保留 `fantasy + urban-occult + web-serial`

## 4. 文档同步触发条件

- 样例定位变化
- 卷级结构变化
- 已写章节数量变化
- 评审/验证入口变化
