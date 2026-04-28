# 命灯照骨 项目模块说明

> 最后更新: 2026-04-26
> 状态: 当前有效模块文档

## 1. 模块职责

- 提供《命灯照骨》这个玄幻长篇样例工程
- 用于验证“代价驱动升级 + 长篇连载 + 规则约束写作”能否跑通真实卷级闭环
- 作为 `review / projection / context / style / consistency` 的长期回归样例

## 2. Owns

- `project.yaml` 中的定位层、故事契约、情绪契约和商业定位
- `outline.yaml`、`detailed_outlines.yaml` 中的卷章结构、beats 与 `scenePlans`
- `worldbook.yaml`、`entities.yaml`、`threads.yaml`、`foreshadowing.yaml` 中的故事真相层
- `chapters/*.md` 中的作者向正文
- `projections/`、`reviews/`、`workflow.yaml` 中的过程状态

## 3. 不变量

- 所有 `.yaml` 内容必须保持 JSON-compatible
- 正文、结构化状态、评审结果必须分层，禁止把 canon 直接写进 projection/review 文件绕过决策
- 每章都要有显式 `scenePlans`，并在正文稳定后回填合理段落边界
- 故事推进必须同时兑现三条主线压力：残灯真相、自我侵蚀、外部追查
- 正文不得退化成“把细纲改写成 prose”；人物选择要在既有约束下自然成立
- 每次关键借灯、试探或突破都必须留下可追溯后果，不能出现无成本爽点

## 4. 文档同步触发条件

- 项目定位或故事契约变化
- 卷结构或章节组织方式变化
- 机器检查闭环发生变化
- 样例的核心验证目标变化
