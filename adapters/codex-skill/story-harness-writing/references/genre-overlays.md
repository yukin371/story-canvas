# Genre And Tag Overlays

这是 `story-harness-writing` 的类型 / tag overlay 层索引。

## 当前状态

仓库正在基于真实小说语料沉淀这一层。

当前高置信事实：

1. 已有“普适写作层”和“workflow gate 层”
2. 类型 / tag 独特写法仍在持续从真实语料中抽取
3. 这一层还不应该被伪装成完整成品

## 设计原则

overlay 应只补“普适层不会自动给出”的独特写法，例如：

1. 题材承诺
2. 节奏模型
3. 钩子结构
4. 读者期待
5. 风格禁区
6. 世界引导方式
7. 关系推进方式

它不负责重复基础 workflow gate，也不负责重写所有普适写作规则。

## 推荐层次

先按以下粒度沉淀：

1. 平台 / 连载模型
2. 大类型
3. tag / 子类型

推荐加载顺序：

1. `writing-universal.md`
2. `workflow-gates.md`
3. 只加载一个主 overlay

## Available Now

当前已提供、且有仓库样例支撑的 overlay：

1. `references/overlays/xuanhuan-web-serial.md`
2. `references/overlays/urban-occult-web-serial.md`
3. `references/overlays/light-novel-western-fantasy.md`

加载规则：

1. 优先只加载一个主 overlay
2. `western-fantasy + light-novel` 这类已稳定组合，可直接使用组合 overlay
3. 若项目混合多个 tag，但仓库还没有对应组合 overlay，宁可回退普适层，也不要拼接多份半成熟 overlay

## Still TBD

以下内容仍属 `TBD`，应以真实语料分析和回归验证后再补：

1. 女频成长 / 感情推进 overlay
2. 历史权谋 overlay
3. 恐怖游戏 overlay
4. 末世科幻 overlay
5. 娱乐圈 / 职业成长 overlay

确认路径：

1. 基于 `projects/` 中真实样例和外部小说语料分析
2. 从 `review` / `style` / 人工卷级审查中回灌高频问题
3. 形成可验证的 overlay 规则后，再拆分成独立 reference 文件

## 当前执行规则

在 overlay 未沉淀完之前：

1. 先使用普适层
2. 再使用 workflow gate 层
3. 若用户明确指定题材要求，优先匹配已存在 overlay；没有就只补高置信、已知的少量题材约束
4. 不要假装自己已经拥有完整 tag 圣经
