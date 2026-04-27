# 分层写作 Skill 集成设计

> 日期: 2026-04-27
> 状态: draft
> 目的: 把 `noval-data` 商业成书拆解结果，映射为 Story Canvas 可接入的“两层 skill + 渐进式揭露 + 按需取用”方案。

## 1. 背景

当前 `noval-data/analysis-workbench/` 已经沉淀出两批共 10 本样本的：

- `01-prd-reconstruction`
- `02-outline-and-volume`
- `03-scene-and-beat`
- `07-hook-and-reader-appeal`
- `08-strengths-and-problems`
- `09-prompt-lessons`

这些内容已经足够反推出一组跨题材稳定规则，但如果直接全部塞进单一 skill，会出现三个问题：

1. 上下文过大
2. 题材不相关内容互相干扰
3. agent 容易在不需要的时候提前加载过多细节

因此需要把 skill 设计成分层结构。

## 2. 目标

设计一个适合 Story Canvas 的写作 skill 结构：

1. `普适层`
2. `类型层`
3. 按写作阶段做 `渐进式揭露`
4. 在 adapter 内保持“薄”，不引入并行状态系统

## 3. 设计原则

### 3.1 两层而不是一个大包

- `普适层` 负责跨题材稳定规则
- `类型层` 负责题材特异的连载模型和审查重点

### 3.2 先小后大

- 先加载最少必要规则
- 只有当 genre / platform / phase 明确后，再加载第二层

### 3.3 先结构，后文风

- 先解决 PRD、卷承诺、scene engine、章节增量这些结构问题
- 文风与平台语气暂不作为第一层强规则

### 3.4 Skill 必须保持薄

- 规则只负责“怎么写”和“怎么检查”
- 真正执行仍是:
  - CLI workflow
  - protocol files
  - review / context / outline 命令

## 4. 推荐的 Skill 分层

### 4.1 Layer A: 普适层

适用范围：

- 所有题材
- 所有平台
- 所有写作阶段都会命中，但揭露深度不同

建议包含：

- 标题要交付什么
- 主角异常状态要如何立
- 前三章职责
- 前 20 章接驳大棋盘
- 第一卷承诺必须具体
- `sceneEngine` / `serialLoop` / `章节增量` 的定义
- 常见反模式

推荐来源：

- `noval-data/analysis-workbench/synthesis/writing-playbook.md`
- `noval-data/analysis-workbench/synthesis/review-rule-candidates.md`
- `noval-data/analysis-workbench/synthesis/anti-patterns.md`

### 4.2 Layer B: 类型层

适用范围：

- genre / archetype 已明确
- 需要生成 PRD、outline、scene plan、review 时

建议按 archetype 组织，而不是按单书组织。

当前优先级最高的类型层：

1. `male-cultivation-power`
2. `female-cultivation-growth`
3. `urban-supernatural`
4. `light-novel-romcom`
5. `western-fantasy-lightnovel`
6. `horror-game`
7. `historical-power`
8. `post-apoc-scifi`
9. `entertainment-industry`

每个类型层建议只保留四类信息：

1. `核心读者承诺`
2. `单章 loop`
3. `第一卷交付`
4. `高频风险`

不要把所有样本细节原样搬过去。

## 5. 渐进式揭露策略

### 5.1 立项阶段

只加载：

- 普适层里和 `PRD` 有关的规则
- 一个类型层的：
  - 读者承诺
  - 第一卷承诺
  - scene engine 简版

不加载：

- 详细 scene 规则
- 详细 review 清单

### 5.2 大纲阶段

加载：

- 普适层全部结构规则
- 类型层的：
  - chapter loop
  - volume delivery
  - expansion board

不加载：

- 细颗粒风格提醒
- 长清单式反模式

### 5.3 章节写作阶段

加载：

- 普适层的 scene / 增量规则
- 类型层的：
  - chapter loop
  - 章尾推进
  - 本题材的主增量类型

### 5.4 审查阶段

加载：

- 普适层的 review 规则
- 类型层的高频风险
- 当前 volume 或 current scene 对应的增量检查项

## 6. 按需取用顺序

建议 skill 在内部遵循以下顺序：

1. 判断当前任务阶段
2. 先加载普适层最小规则集
3. 判断 genre / platform / archetype
4. 只叠加一个主要类型层
5. 若进入 chapter/review 阶段，再展开更细粒度 scene / review 规则

这意味着 skill 不是：

- 一次性加载所有题材知识

而是：

- `base rules`
- `genre overlay`
- `phase overlay`

## 7. Story Canvas 中的映射建议

### 7.1 可先落到 adapter 文本层

- 在 `adapters/*/story-harness-writing/SKILL.md` 中声明：
  - 两层 skill 结构
  - progressive disclosure 原则
  - 先 base、再 genre、再 phase 的使用顺序

### 7.2 可后续落到 prompt / pack / profile 层

- `base writing pack`
- `genre overlays`
- `review overlays`

当前仓库里 `prompt_packs.py` 还是图像 prompt pack，不建议直接复用该文件结构给写作层。

写作层更适合后续新增：

- `base writing rules`
- `genre rule packs`
- `phase-specific review packs`

但这一步应等 CLI / protocol 确认需要时再做。

## 8. 当前推荐的最小落地方案

这一轮先做到：

1. `synthesis` 写清楚两层与揭露顺序
2. `adapters` 写清楚 skill 的使用原则

暂不做：

- CLI 字段扩展
- protocol schema 新字段
- 自动化 genre overlay loader

## 9. 风险

### 9.1 风险: 类型层做得太细

- 后果:
  skill 变成样本摘抄，不是规则层

### 9.2 风险: 普适层做得太空

- 后果:
  agent 仍然只能靠自身临场推理

### 9.3 风险: 一次性揭露太多

- 后果:
  上下文膨胀，反而降低有效性

## 10. 结论

商业样本沉淀更适合转成：

- `普适层`
- `类型层`
- `阶段性揭露`

而不是一个“大而全的写作 skill”。

后续真正接入 skill / prompt 时，应把“什么时候加载哪一层”当作一等设计约束。
