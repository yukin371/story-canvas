# PRD 与 AI 风格治理 / 插图策略对齐

> 日期: 2026-04-25
> 状态: 已完成
> 关联: `docs/templates/PRD.template.md`, `docs/plans/2026-04-24-prd-and-production-workflow-design.md`, `docs/v3-plan.md`

## 1. 背景

当前仓库已经分别具备：

- workflow 显式状态机命令组
- AI 风格检测的最小可用实现
- illustration provider 的最小骨架

但 PRD 层仍然只把这些能力当作“工具细节”，没有把它们正式提升为小说产品规格的一部分。

这会导致两个直接问题：

1. “AI 检测”只在成文后打分，缺少“生成时约束”这一产品要求
2. “AI 生图”只在技术蓝图里出现，PRD 没有说明何时需要文生图、何时需要图生图、如何审核和落资产

## 2. 结论

### 2.1 当前 PRD 覆盖情况

结论：**未完整揽括。**

- `docs/templates/PRD.template.md` 目前只有一般质量门禁，没有“AI 起稿约束 -> 生成后检测 -> 超阈值修复”的闭环规格
- 现有 PRD 模板也没有“视觉资产 / 插图策略”章节，因此无法在产品层定义：
  - 是否启用插图
  - 文生图还是图生图
  - 参考图来源
  - 成本、频率、审核边界

### 2.2 技术设计覆盖情况

结论：**部分覆盖，但口径未收敛。**

- `docs/v3-plan.md` 已有 style feature 和 illustration feature
- 但 style 仍偏“检测器”视角，缺少“生成时约束 + 生成后修复”的完整闭环
- illustration 仍把 OpenAI model 写得过于具体，容易和真实部署环境漂移

## 3. 设计决策

### 3.1 AI 风格治理属于 PRD 级需求

PRD 必须明确：

- 项目采用人工主写、AI 辅助还是 AI 起稿
- 生成时必须注入哪类 style constraints
- 发布前允许的 `styleAnalysis` 阈值
- 超阈值后的修复路径和停止条件

原因：这决定的是“产品可接受的文本风格边界”，不是单纯实现细节。

### 3.2 插图策略属于 PRD 级需求

PRD 必须明确：

- 插图目标：角色设定图、章节高潮插图、宣传图、封面概念图
- 生成模式：文生图 / 图生图
- 参考图来源：角色设定、历史资产、手绘草图、摄影参考
- 审核规则：人物一致性、时代/服饰正确性、剧透边界、平台合规

原因：这决定的是“该作品是否把视觉资产视为正式产出物”，不是单纯 provider 选型。

### 3.3 OpenAI image model 不写死在协议里

当前用户环境明确可使用 `gpt-image-2`。

同时，官方公开文档中的 GPT Image 家族型号可能与具体部署环境存在差异。因此设计口径改为：

- 协议和 CLI 允许任意 `model` 字符串
- PRD 可以写“当前成本优先时使用 `gpt-image-2`（若部署环境可用）”
- provider 不在 schema 层硬编码固定模型枚举

### 3.4 文生图与图生图都纳入 v3 范围

illustration feature 不再只按“文生图 prompt 生成”设计，而是统一使用：

- `mode=text-to-image`
- `mode=image-to-image`

并在请求层补齐：

- `inputImages`
- `mask`
- `referencePolicy`

## 4. 本轮落地

- 更新 PRD 模板，新增：
  - `AI 协作与风格控制`
  - `视觉资产与插图策略`
- 更新 PRD 流程设计文档，明确这两项是 PRD 级规格，而不只是工程实现
- 更新 `docs/v3-plan.md`：
  - style 改为“约束 -> 检测 -> 修复”闭环
  - illustration 改为“model 可配置 + 文生图/图生图双模式”
- 更新 `projects/demo-urban-occult-long/PRD.md` 作为示例

## 5. 验证

- `git diff --check -- docs/templates/PRD.template.md docs/plans/2026-04-24-prd-and-production-workflow-design.md docs/v3-plan.md projects/demo-urban-occult-long/PRD.md docs/plans/2026-04-25-prd-style-and-illustration-alignment.md`
- 关键术语复检：
  - `style constraints`
  - `style repair`
  - `text-to-image`
  - `image-to-image`
  - `gpt-image-2`
