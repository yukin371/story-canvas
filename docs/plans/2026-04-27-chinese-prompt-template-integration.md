# 中文提示词模板集成计划

> 日期: 2026-04-27
> 状态: draft
> 目标: 把 `E:\Github\chinese-novelist-skill` 中值得保留的方法，吸收到 Story Canvas 当前写作流程里，并保持当前仓库协议与文档为唯一真相源。

## 1. 背景

`noval-data` 已经沉淀出两批 10 本商业样本的：

- PRD 反推
- 卷结构分析
- 场景节拍分析
- 钩子与读者吸引分析
- 优点 / 问题 / prompt lessons

这些结果已经足够支撑一套更强的中文写作提示词骨架。

另一方面，`chinese-novelist-skill` 已经验证了三件事确实有用：

1. 分阶段问答
2. 直接可用的规划模板
3. 对开篇、章节、钩子的显式提醒

但它也带着另一套项目目录、状态文件和流程假设，不适合原样并入当前仓库。

## 2. 本轮结论

### 2.1 应吸收的部分

- 第一阶段分层问答骨架
- 从“核心定位”到“深度定制”的渐进式提问顺序
- 大纲、章节、审查的通用模板表达方式
- 开篇钩子、章节推进、章尾续追等实操提醒

### 2.2 不应吸收的部分

- 它自己的项目目录结构
- 它自己的状态文件真相源
- 并行于 Story Canvas protocol 的流程定义
- 任何要求 adapter 持有核心状态的设计

## 3. 设计约束

### 3.1 中文优先

- 面向中文小说时，prompt 正文、提问、改写要求、审查意见默认使用中文
- 英文仅保留给内部别名、程序字段、schema 映射

### 3.2 两层结构

- `Layer A / 普适层`
  - 跨题材稳定规则
- `Layer B / 类型层`
  - 题材专有承诺、loop、风险

### 3.3 渐进式揭露

- 立项阶段只揭露 PRD 所需字段
- 大纲阶段再揭露卷承诺、前 20 章接驳、大纲推进规则
- 章节与审查阶段再揭露 scene 增量、章尾钩子、反模式清单

### 3.4 adapter 保持薄

- 模板只定义“问什么、怎么问、怎么生成、怎么审”
- 不引入新的协议文件真相源
- 不改写当前 CLI / protocol 的 owner 关系

## 4. 本轮落地产物

1. `docs/templates/writing/intake-layered.template.md`
   - 中文优先的立项问答模板
   - 吸收分层问答，但改写为 Story Canvas 的 PRD 字段口径
2. `docs/templates/writing/prompt-skeletons.template.md`
   - 通用中文 prompt 骨架
   - 覆盖 PRD / 大纲 / 章节 / 评审
3. `docs/templates/writing/genre-overlay.template.md`
   - 类型层模板
   - 规定一个题材 overlay 应只包含哪些最小字段

## 5. 字段映射原则

优先使用中文字段名对模型下发，必要时保留内部别名：

- `主角异常状态` -> `abnormalState`
- `核心反差` -> `coreContrast`
- `读者承诺` -> `readerPromise`
- `第一卷承诺` -> `firstVolumePromise`
- `场景引擎` -> `sceneEngine`
- `连载循环` -> `serialLoop`
- `扩张棋盘` -> `expansionBoard`

## 6. 后续建议

### 6.1 先做的

- 基于现有 10 本样本，继续补 `genre overlay`
- 把高频中文提醒收敛成 review overlay
- 让 adapter 明确“当前阶段只加载哪一层”

### 6.2 暂不做的

- 新增 protocol schema 字段
- 新增独立 prompt pack 加载器
- 新增平行于当前 workflow 的项目状态文件

## 7. 验收标准

1. 新模板全部采用中文优先表述
2. 新模板明确区分普适层与类型层
3. 新模板可直接服务 PRD / 大纲 / 章节 / 评审四类任务
4. 文档没有把 `chinese-novelist-skill` 变成新的 canonical workflow
