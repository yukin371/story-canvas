# adapters 模块说明

> 最后更新: 2026-04-28
> 状态: 当前有效模块文档

## 1. 模块职责

- 维护 Story Canvas 面向外部 AI 宿主的 adapter 源文件
- 把仓库内真实工作流翻译成宿主可执行的 skill / prompt / reference 文档
- 在保持 adapter “薄”的前提下，提供与仓库真实工作流一致的写法指导与用具指导
- 明确哪些协议文件要读、哪些命令要跑、何时算流程完成
- 维护 adapter 的分层设计：前置 brainstorm 层、普适写作层、workflow gate 层、类型/tag overlay 层、插图层、WebUI 参与层

## 2. Owns

- `adapters/README.md`
- `adapters/ADAPTER_ARCHITECTURE.md`
- `adapters/codex-skill/story-harness-brainstorm/*`
- `adapters/codex-skill/story-harness-writing/*`
- `adapters/claude-code/story-harness-brainstorm/*`
- `adapters/claude-code/story-harness-writing/*`
- `adapters/codex-skill/story-canvas-imagegen/*`
- `adapters/claude-code/story-canvas-imagegen/*`

## 3. 不变量

- adapter 必须保持“薄”，执行层仍是 `story-canvas` CLI
- adapter 不得和仓库真实能力口径冲突
- adapter 必须说明 canonical workflow，而不是只罗列零散命令
- adapter 必须说明运行 fallback、关键协议文件、停止条件
- 对卷级审查，adapter 若宿主支持 subagent / 新线程 / 独立通道，必须优先要求无上下文独立编辑审查，避免同线程自评
- adapter 可以整合外部写作 skill 的方法论，但不得引入并行真相源或独立状态系统
- imagegen 类 adapter 也必须消费仓库导出的 batch manifest，并通过 CLI 回录结果，不能自己直接写 `illustrations.yaml`
- 写作类 adapter 必须支持分层加载：主 skill + references，不得把普适写法、workflow gate、tag overlay、宿主说明无差别堆进单文件
- 写作类 adapter 可以把语料 overlay 翻译成风格执行规则，但不得把 overlay 写成新的项目状态、审查 gate 或固定命令清单
- 写作类 adapter 在项目起步与章节起步时，必须优先消费 CLI 返回的 `startGuide` / gate 输出，再由 skill 组织解释；不得绕过 CLI 自行发明平行 bootstrap 流程
- WebUI 只能作为人类更好参与的辅助层，不能被写成强制工作流前提

## 4. 文档同步触发条件

- CLI 工作流变化
- 协议文件布局变化
- 新增章节/场景评审或回归步骤
- 新增图片批量导出 / 回录工作流
- adapter 的默认 prompt 或 skill 触发规则变化
- 语料分析沉淀出新的 tag / 类型 overlay
- CLI-only 与 WebUI-assisted 使用形态边界变化
