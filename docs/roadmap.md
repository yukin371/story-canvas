# 当前路线图

> 最后更新: 2026-04-25
> 状态: 当前唯一执行入口

## 1. 当前发布目标

- `v1.0`: 第一个整体发布版本，目标是把 Story Harness 从“可用 CLI 原型”收敛成“完整、有效的故事工程管理产品”

## 2. v1.0 验收范围

### 2.1 完整故事管理能力

- 项目可按代码仓库思路管理：结构清晰、协议稳定、状态可追溯、可迁移
- 核心管理域完整且可协同：
  - `project.yaml`
  - `outline`
  - `worldbook` / 世界约束
  - `entities`
  - `foreshadowing`
  - `threads`
  - `timeline`
  - `reviews`
  - `projections`
  - `workflow`
- 至少支持短篇与长篇两个真实样例闭环

### 2.2 简单生图管理能力

- 支持章节/角色插图 prompt 生成
- 支持最小可用的图像生成调用与 `--dry-run`
- 支持资产落盘、生成记录、引用关系与基础配置
- 不以复杂编辑能力为 `v1.0` 范围

### 2.3 工作流能力

- 支持显式 workflow 状态推进
- 支持 gate 决策记录、恢复、导出
- 工作流与故事协议一致，不依赖隐式人工记忆

### 2.4 产品边界与命名评估

- 评估仓库与产品命名是否从 `story-harness-cli` 收敛到更通用的 `story-harness`
- 输出明确结论，但不把改名本身作为 `v1.0` 发布前硬阻塞

## 3. v1.0 Active Tracks

### Track 1: 协议收敛为产品级故事管理能力

- 目标: 从“角色 + 大纲 + 章节”升级到“可维护的故事真相层与动态状态层”
- 当前重点:
  - 落稳 `project` / `outline` / `entities` / `foreshadowing` / `threads` / `timeline`
  - 引入更完整的世界/背景/规则约束协议
  - 让角色状态变化和伏笔回收具备追溯能力
- 验收标志:
  - 长篇样例可证明协议不是摆设
  - `doctor` / `outline check` / `context refresh` / `review` 能消费这些协议

### Track 2: 工作流闭环稳定化

- 目标: 把当前写作流程变成可审计、可恢复、可导出的显式状态机
- 当前重点:
  - `workflow status/run/advance/reset/export`
  - gate 结果持久化
  - 与 review / projection / context 的闭环衔接
- 验收标志:
  - 至少一个真实项目跑通规划 -> 写作 -> 审查 -> 投影 -> 导出

### Track 3: 简单生图管理闭环

- 目标: 提供最小可用的插图资产管理，而不是只停留在概念设计
- 当前重点:
  - `illustration prompt/generate/list/config`
  - 文生图 / 图生图最小协议
  - 生成资产与元数据落盘
- 验收标志:
  - 角色图或章节图至少跑通一条真实链路
  - 缺失 provider 或断网时仍能 `dry-run`

### Track 4: 发布基线与样例矩阵

- 目标: 让 `v1.0` 有可对外展示和回归验证的样例基础
- 当前重点:
  - 固化短篇回归样例
  - 固化长篇商业样例
  - 补一个“复杂长篇暗线”样例视角，优先参考 `demo-guixu`
- 验收标志:
  - 至少一短一长稳定通过回归
  - 文档能说明各样例验证了什么

## 4. 当前阻塞

- 本地 `pip install -e .` 仍可能受镜像/证书问题影响
  - 影响: 无法稳定通过已安装命令入口验证
  - 临时路径: 使用 `PYTHONPATH=src python -m story_harness_cli`
- 当前工作树存在大量并行改动
  - 影响: `v1.0` 收口前需要避免路线图与真实代码状态长期分叉

## 5. v1.0 发布判断标准

- 核心协议稳定，旧项目可兼容加载或有明确迁移路径
- CLI 主闭环可离线验证，不依赖外部服务才能工作
- 工作流能力和故事管理能力不是分离孤岛
- 插图能力达到“可管理资产”而不是“只能打一条 prompt”
- 至少一个长篇项目证明工具不是只适合玩具样例

## 6. v1.1 展望

- `v1.1`: 简易 Web UI
- 目标:
  - 提供阅读、审查、简单修改结构化产物的界面
  - 支持查看项目状态、workflow、review、伏笔、角色状态、插图资产
- 边界:
  - Web UI 只是文件协议的可视化壳，不应成为新的真相源
  - 不在这一版追求复杂富文本编辑器或多人协作系统

## 7. v1.2 展望

- `v1.2`: 模板化与自由编排增强
- 目标:
  - 丰富题材模板
  - 管理 prompt packs / 提示词资源
  - 支持 workflow 自由编排
  - 提供默认模板与参考项目
- 前提:
  - `v1.0` 协议稳定
  - `v1.1` UI 已证明对协议只是外壳而非替代

## 8. 历史背景

- `v0.2` 路线中的已完成项仍然有效，构成当前 `v1.0` 的技术起点：
  - timeline / search / causality
  - review chapter / review scene
  - scenePlans 维护闭环
  - positioning / storyContract / commercialPositioning
  - export 多格式、entity graph、样例矩阵
- 这些能力不再单独作为执行入口，而作为 `v1.0` 的既有基础
