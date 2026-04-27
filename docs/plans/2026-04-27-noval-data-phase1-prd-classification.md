# noval-data 书籍 Phase 1 PRD 分类计划

> 日期: 2026-04-27
> 状态: 已执行
> 关联入口: `docs/roadmap.md`
> 关联规则:
> - `docs/plans/2026-04-24-prd-and-production-workflow-design.md`
> - `docs/plans/2026-04-27-writing-quality-workflow-prd.md`
> - `docs/plans/2026-04-27-functional-improvement-phasing.md`

## 1. 目标

围绕 `noval-data/` 中的真实书籍测试集，输出一套可直接服务 Story Canvas 创作第一阶段 PRD 的分类结果，重点回答：

- 这本书主要写给谁看
- 它靠什么卖点吸引读者
- 它更像哪一种立项 archetype
- Phase 1 PRD 在立项时应优先写清哪些字段

## 2. 输入范围

- `noval-data/*.txt`
- 书名
- 开头简介 / 文案 / 前若干段正文中可直接提取的高置信度信号

## 3. 输出范围

- `noval-data/MODULE.md`
- `noval-data/phase1-prd-catalog.json`
- `noval-data/phase1-prd-analysis.md`
- `.gitignore` 中对原始数据集文本的忽略规则

## 4. 分类口径

按“书籍立项 PRD”而不是“工程实现计划”分类，核心字段包括：

- 主类型 / 子类型
- 风格标签
- 目标平台
- 目标读者
- 写作目的
- 连载模型 / 读者承诺
- 置信度

## 5. 方法

1. 先按题材与读者承诺抽象出 PRD archetype。
2. 再把每本书映射到 archetype，并保留必要的书目级差异说明。
3. 最后总结当前数据集对 `v1.0` 样例矩阵的支持度与缺口。

## 6. 风险与限制

- 本轮不通读全书，只基于高置信度开头信号分类。
- 来源站点噪音、编码差异和标题营销语会影响判断，因此对模糊项标注 `medium` / `low` 置信度。
- 不复制原文大段内容，只保留必要的衍生元数据与分析结论。
