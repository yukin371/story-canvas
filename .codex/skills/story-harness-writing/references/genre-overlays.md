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
4. `references/overlays/female-cultivation-growth.md`
5. `references/overlays/school-romcom.md`
6. `references/overlays/horror-game.md`
7. `references/overlays/historical-power.md`
8. `references/overlays/gender-bender-yuri.md`
9. `references/overlays/urban-supernatural-mystery.md`
10. `references/overlays/academy-supernatural-action.md`
11. `references/overlays/evil-path-cultivation.md`
12. `references/overlays/mystery-supernatural-horror.md`

## Available With Scope Guard

以下 overlay 已可用，但当前证据覆盖的是更窄变体，使用时不要外推成整类题材圣经：

1. `references/overlays/historical-court-politics.md`
   - 当前更贴近 `低位入局 + 暗中起盘` 的驸马 / 质子 / 厂卫 / 债务官场变体
2. `references/overlays/post-apoc-scifi.md`
   - 当前更贴近 `废土底层上升 / 特区秩序 / 现代末世团队生存`
3. `references/overlays/acg-fanfic-action.md`
   - 当前更贴近 `熟悉 IP + 外来体系改线 + 动作牌桌改写`

加载规则：

1. 优先只加载一个主 overlay
2. `western-fantasy + light-novel` 这类已稳定组合，可直接使用组合 overlay
3. 若使用 `Available With Scope Guard` 中的 overlay，先确认项目主承诺是否真的落在该范围里
4. 若项目混合多个 tag，但仓库还没有对应组合 overlay，宁可回退普适层，也不要拼接多份半成熟 overlay

## Close Calls

以下几组最容易选错主包。先看“单章持续在卖什么”，再决定。

1. `urban-occult-web-serial` vs `urban-supernatural-mystery`
   - 如果持续卖点是职业现场、办事流程、禁忌规矩、单元案结算，用 `urban-occult-web-serial`
   - 如果持续卖点是主角身份异常、核心意象、世界规则谜团双线推进，用 `urban-supernatural-mystery`
2. `horror-game` vs `mystery-supernatural-horror`
   - 如果持续卖点是副本规则、求生压力、通关与例外项，用 `horror-game`
   - 如果持续卖点是异事上门、民俗法门、设坛破局、入行成长，用 `mystery-supernatural-horror`
3. `xuanhuan-web-serial` vs `female-cultivation-growth` vs `evil-path-cultivation`
   - 如果持续卖点是压制、反压、境界和资源门槛，用 `xuanhuan-web-serial`
   - 如果持续卖点是女主改命、旧关系解构、新归属重建，用 `female-cultivation-growth`
   - 如果持续卖点是禁忌求生、代价型变强、黑暗秩序压迫，用 `evil-path-cultivation`
4. `school-romcom` vs `gender-bender-yuri`
   - 如果持续卖点是对象选择、校园互动、关系增量，用 `school-romcom`
   - 如果持续卖点是旧身份与新身体冲突、关系重排、情绪黏性，用 `gender-bender-yuri`
5. `historical-power` vs `historical-court-politics`
   - 如果持续卖点是项目落地、军政经营、战局与地盘变化，用 `historical-power`
   - 如果持续卖点是低位入局、暗中起盘、牌桌位次抬升，用 `historical-court-politics`
6. `post-apoc-scifi` vs `academy-supernatural-action`
   - 如果持续卖点是生存压力、秩序牌桌、据点和资源盘，用 `post-apoc-scifi`
   - 如果持续卖点是觉醒分层、学院筛选、公开兑现和更高舞台门票，用 `academy-supernatural-action`
7. `light-novel-western-fantasy` vs `acg-fanfic-action`
   - 如果持续卖点是原创西幻轻小说式角色互动、小冒险和轻快奇观，用 `light-novel-western-fantasy`
   - 如果持续卖点是熟悉 IP、外来体系改线、原作秩序重排，用 `acg-fanfic-action`

## Fallback Rule

如果一部作品同时像两个 overlay，但你无法明确判断主承诺：

1. 先退回 `writing-universal.md`
2. 只吸收一个 overlay 的少量高置信约束
3. 不要把两个完整 overlay 生硬叠加
4. 优先等 scene、章节样稿或用户平台目标更明确后再选主包

## Still TBD

以下内容仍属 `TBD`，应以真实语料分析和回归验证后再补：

1. 娱乐圈 / 职业成长 overlay
2. `lord-building`
3. `political-intrigue-fantasy`
4. `wuxia-jianghu`
5. `mystery-detective`

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
