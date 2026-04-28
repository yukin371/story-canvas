# Adapter Architecture

> 最后更新: 2026-04-28
> 状态: 当前 adapter 分层设计

## 1. 目标

本目录下的 adapter 不是单一“写作 skill”或单一“命令指南”，而是面向外部 AI 宿主的分层能力面：

1. 前置探索层
2. 写作方法层
3. 工作流执行层
4. 插图生成层
5. 人类参与层

要求：

1. 保持仓库协议与 CLI 为真相源
2. 允许只用 `agent + CLI` 跑完大多数工作流
3. 支持 `WebUI` 让人类更容易参与，但不强制依赖 WebUI

## 2. 使用形态

### 2.1 CLI-Only Agent Mode

默认形态。只使用：

1. agent
2. `story-canvas` / `story_harness_cli` CLI
3. 仓库协议文件

适用：

1. 章节写作与修订
2. review / style / workflow 闭环
3. 卷级 AI 自审
4. 大多数插图批量导出 / 回录

### 2.2 Human-Assisted WebUI Mode

增强形态。人在本地 WebUI 中参与：

1. 浏览项目状态
2. 浏览 review / packet / context
3. 执行或辅助插图生成
4. 辅助人工审查和创作协作

适用：

1. 人工参与较重的创作协作
2. WebUI-manual 插图工作流
3. 人类更方便地看 review 证据和卷级闭环材料

说明：

1. WebUI 是参与层，不是新的真相源
2. 没有 WebUI 也应能完成主工作流

## 3. Skill Families

### 3.1 Brainstorm Skill

当前前置探索 skill：

1. `story-harness-brainstorm`

职责：

1. 在项目创建前做灵感扩展、方向比较和问题收束
2. 帮用户从零散想法收敛到 `premise / hook / abnormal state / serial loop / first-volume promise`
3. 产出一份可交给 `init` 或后续写作 skill 使用的 `PRD seed`

边界：

1. 不假设项目目录已经存在
2. 不直接改 `project.yaml`、`outline.yaml` 或其他协议文件
3. 不把 brainstorming 伪装成正式大纲或正文起稿
4. 一旦用户进入真实项目执行，应交给 `story-harness-writing`

### 3.2 Writing Skill

当前主 skill：

1. `story-harness-writing`

它内部应继续分层，而不是把所有方法论和命令硬揉成一个平面文档。

#### Layer A: Universal Writing Base

适用于大多数小说项目的普适写作规则：

1. 标题承诺
2. 主角异常态
3. 章级推进
4. scene engine
5. 卷级小闭环
6. 中文叙事常见 AI 风险
7. 人物发动机、缺陷与关系变化
8. 章节规划粒度与 scene 职责
9. hook 编排与兑现节奏

#### Layer B: Workflow Gates

适用于仓库内真实执行的 CLI 工作流：

1. 写前 gate
2. 写后检测
3. 修后复检
4. 卷级 preflight
5. volume self-review
6. independent editor pass
7. human review handoff

#### Layer C: Genre / Tag Overlays

适用于不同题材、平台、tag 的独特写作策略。

当前状态：

1. 仓库正在基于真实小说语料沉淀这层
2. 这一层应按 tag / 类型逐步补齐
3. 在未沉淀前，不应编造“完整类型圣经”

当前设计要求：

1. `story-harness-writing` 主 skill 只保留 overlay 入口与加载规则
2. 具体 overlay 内容放在 `references/genre-overlays.md` 或后续拆分文件
3. overlay 必须以真实语料分析和回归样例为依据

### 3.3 Image Skill

当前主 skill：

1. `story-canvas-imagegen`

职责：

1. 通过 CLI 导出 manifest
2. 支持 `external-agent` 模式
3. 支持 `webui-manual` 模式
4. 通过 CLI 回录，不直接写 `illustrations.yaml`

它不是写作 skill 的附属说明，而是独立 skill family。

## 4. Host Mapping

当前宿主：

1. `codex-skill/`
2. `claude-code/`

要求：

1. 两个宿主目录应共享同一套能力分层
2. 差异只保留在宿主措辞、metadata 和必要交互约束
3. 不允许 Codex / Claude 两套 adapter 在 workflow 设计上长期漂移

## 5. 当前落地策略

### Brainstorm Skill

主 `SKILL.md` 负责：

1. 触发条件
2. 项目创建前边界
3. 轮次推进顺序
4. `PRD seed` 的交付要求

`references/` 负责：

1. 探索轮次
2. 追问骨架
3. 收束输出格式
4. challenger pass 契约
5. 经典题材 / tag 起步索引

### Writing Skill

主 `SKILL.md` 负责：

1. 触发条件
2. 总体定位
3. 加载顺序
4. CLI gate 规则
5. 引用下级 reference 文件

`references/` 负责：

1. `protocol.md`: 协议与布局
2. `writing-universal.md`: 普适写作层
3. `workflow-gates.md`: CLI workflow 层
4. `planning-primitives.md`: 人物字段与章节规划骨架
5. `genre-overlays.md`: 类型 / tag 层索引与当前状态
6. `overlays/*.md`: 已沉淀的题材 / tag 独立 overlay 文件

### Image Skill

主 `SKILL.md` 负责：

1. 触发条件
2. `external-agent` / `webui-manual` 选择规则
3. 回录闭环

`references/` 负责：

1. CLI 命令参考
2. 必要时补协议说明

## 6. 不变量

1. 写作方法层不能替代 workflow gate
2. brainstorm skill 不能伪装成项目内执行层
3. workflow gate 不能替代写作判断
4. image skill 不能直接篡改状态文件
5. WebUI 不能成为强依赖
6. tag / 类型 overlay 只能基于真实语料和回归反馈沉淀
