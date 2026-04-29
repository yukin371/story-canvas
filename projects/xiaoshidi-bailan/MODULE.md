# 小师弟只想摆烂，师姐们却全疯了 项目模块说明

> 最后更新: 2026-04-29
> 状态: 当前有效模块文档

## 1. 模块职责

- 提供《小师弟只想摆烂，师姐们却全疯了》这个欢乐玄幻宗门样例工程
- 用于验证“反常修炼机制 + 师姐误会升级 + 宗门危机打脸”能否跑通真实章节闭环
- 作为 `status / chapter analyze / context refresh / review chapter / review scene / workflow` 的写作回归样例

## 2. Owns

- `project.yaml` 中的定位层、故事契约、情绪契约和商业定位
- `outline.yaml`、`detailed_outlines.yaml` 中的卷/章节方向、beats 与 `scenePlans`
- `worldbook.yaml`、`entities.yaml` 中的宗门、对手和反常修炼规则
- `chapters/*.md` 中的样例正文
- `projections/`、`reviews/`、`workflow.yaml` 中的过程状态

## 3. 不变量

- 所有 `.yaml` 内容必须保持 JSON-compatible
- 第一章必须同时建立主角异常机制、破落宗门处境和师姐误判链
- 当前 `volume-001` 已扩成真实三章开卷样例，且卷级内容闭环已成立；但在风格与可读性修整、卷级 gate 放行前，仍不得把它误判成“已可送人工审查的正式首卷”
- 显式 `scenePlans` 的段落边界必须与正文当前段落号保持同步
- 正文中的关键人物、势力、地点与规则引用应优先保持在可追踪引用链内
- 章节闭环结论以 CLI 产物为准，不手工维护平行 workflow 真相

## 4. 文档同步触发条件

- 项目定位或核心承诺变化
- 章节结构、段落边界或 `scenePlans` 组织方式变化
- worldbook / entity onboarding 规则变化
- 闭环验证目标或已知 workflow 风险变化
