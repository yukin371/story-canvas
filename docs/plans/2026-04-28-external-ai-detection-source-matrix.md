# 外部 AI 检测规则源矩阵

> 日期: 2026-04-28
> 状态: 草稿
> 关联入口: `docs/roadmap.md`
> 关联文档:
> - `docs/adr/ADR-002-optional-dependencies-and-providers.md`
> - `docs/plans/2026-04-27-optional-ai-detection-enhancement-plan.md`
> - `docs/plans/2026-04-28-writing-quality-feature-matrix.md`

## 1. 目的

回答一个更具体的问题：

- 外部开源仓库里，是否存在值得我们吸收的 AI 风格检测规则、豁免机制、审查框架或实验性检测后端
- 如果有，哪些适合直接转成 repo-native 规则，哪些适合做 `extras/providers`，哪些只适合作参考

本文件不直接承诺引入依赖，只做来源筛选和接入优先级判断。

## 2. 结论先行

有，但要分三类看：

1. **最值得吸收的是“规则包 / lint 框架”的设计思路，不是黑盒 AI 率模型。**
2. **对你这轮最痛的中文小说问题，仍然要以 repo-native 规则为主。**
   - 例如 `不是……是……` 高频翻转
   - `不像……更像……`
   - 正文出现 `第xx章`
   - POV 越界
   - 首卷疑点堆积、回收率过低
3. **外部仓库最适合补的是三件事：**
   - 规则组织方式
   - 白名单 / 豁免机制
   - 句式重复、可读性、套话密度这类“风格辅助信号”

因此推荐路线不是“接一个 AI detector 就完了”，而是：

1. 先把高价值规则转成我们的内建 detector
2. 再把成熟框架作为可选增强后端
3. 最后才评估黑盒 authorship detector 是否值得保留为实验项

## 3. 适用边界

受当前架构约束：

- `base install` 仍必须 stdlib-only
- 核心 `style -> review -> workflow` 闭环必须离线可跑
- 外部能力只能走 `extras` / `packs` / `providers`
- `services/` 只能消费规则结果，不能直接耦合外部网络服务
- `review-rules.yaml` 仍应是项目级规则启停与豁免真相源，不应并行发明第二套运行时规则配置

因此下文所有“可接入”都指：

- 要么转成仓库内置规则
- 要么做成可选 backend
- 不接受“核心流程必须联网调用外部 detector”

## 4. 候选来源矩阵

| 来源 | 链接 | 类型 | 语言适配 | 对当前痛点价值 | 推荐接法 | 判断 |
|------|------|------|------|------|------|------|
| `textlint-rule-preset-ai-writing` | <https://github.com/textlint-ja/textlint-rule-preset-ai-writing> | AI 写作规则包 | 日文为主 | 对“模板味、宣传腔、机械句式”很有参考价值 | 借规则分类与命中解释，不直接运行时依赖 | `P0` 借思路 |
| `textlint` | <https://github.com/textlint/textlint> | 文本 lint 框架 | 多语言框架 | 对规则组织、局部禁用、注释豁免、规则包生态有高价值 | 学习规则包与 ignore/allow 机制；必要时后续做外部 adapter | `P0` 借架构 |
| `Vale` | <https://github.com/vale-cli/vale> | prose lint 框架 | 英文强，规则机制通用 | 对规则分级、样式包、CI 集成、例外控制有价值 | 可作为 `providers/` 下的 optional CLI backend | `P1` 可选后端 |
| `proselint` | <https://github.com/amperser/proselint> | prose lint 规则集 | 英文 | 对“弱词、套话、赘余、口癖”规则命名与粒度很有参考价值 | 借 rule taxonomy，不建议直接接中文运行时 | `P1` 借规则名录 |
| `write-good` | <https://github.com/btford/write-good> | 轻量风格检查器 | 英文 | 对“给作者可执行改写建议”的输出风格有价值 | 借消息结构与 suggestion 形式 | `P1` 借输出形态 |
| `textlint-rule-preset-ja-technical-writing` | <https://github.com/textlint-ja/textlint-rule-preset-ja-technical-writing> | 技术写作规则包 | 日文 | 对句长、重复、模糊表达、冗长表述有参考价值 | 借阈值设计、allowlist、细粒度 rule 开关 | `P1` 借规则机制 |
| `novel-writer-style-cn` | <https://github.com/lsg1103275794/novel-writer-style-cn> | 中文写作/风格分析项目 | 中文 | 对中文句长、节奏、段落长度、情感/风格刻画更贴近中文写作 | 只适合作规则灵感或离线实验，不宜直接绑定主链 | `P1` 中文参考 |
| `chinese-copywriting-guidelines` | <https://github.com/sparanoid/chinese-copywriting-guidelines> | 中文文案规范 | 中文 | 对标点、空格、术语、排版卫生有价值，但不解决小说 AI 味核心问题 | 可转成 pack 级格式规则 | `P2` 辅助规则 |
| `Binoculars` | <https://github.com/ahans30/Binoculars> | LLM authorship detector | 以英文研究语境为主 | 可作为“整章可疑度”实验信号，但不可解释性弱 | 只允许作为可选实验 backend | `P3` 实验项 |
| `DetectGPT` | <https://github.com/eric-mitchell/detect-gpt> | 研究型 detector | 英文研究语境 | 更偏研究复现，不适合直接服务修稿 | 不建议接入主链 | `P3` 不优先 |
| `SeqXGPT` | <https://github.com/Jihuai-wpy/SeqXGPT> | 细粒度 AI 文本检测 | 多语种研究导向 | 若要做“段落/句子热区”实验有潜力，但依赖重 | 只适合作离线批量实验或评估集工具 | `P3` 实验项 |
| `LLM-generated-Text-Detection` | <https://github.com/NLP2CT/LLM-generated-Text-Detection> | 研究/综述型集合 | 多语种 | 适合作持续观察检测领域，不是直接可接产品 | 做 watchlist，不做集成对象 | `P3` 观察项 |

## 5. 对我们当前痛点的命中度

### 5.1 适合直接借来落地为 repo-native 规则的

| 我们的问题 | 外部来源 | 可借内容 | 为什么不直接依赖它 |
|------|------|------|------|
| 中文高频 AI 句式 | `textlint-rule-preset-ai-writing`、`proselint`、`write-good` | 高频套话分类、message/suggestion 结构、重复密度思路 | 语言不匹配；中文网文句法要本地化改写 |
| 白名单 / 豁免 | `textlint`、`Vale`、`ja-technical-writing` | rule enable/disable、scope exemption、allowlist 机制 | 我们已有 `review-rules.yaml` 真相源，不应外包 |
| 手机阅读段落过长 | `Vale`、`ja-technical-writing`、`novel-writer-style-cn` | 句长、段长、可读性阈值 | 小说段落规则要按题材定制，不能照搬技术写作阈值 |
| 风格口癖复用 | `proselint`、`write-good` | 套话、弱化词、冗余表达的细粒度 rule 命名 | 中文人物对白和叙述腔混在一起，需要我们自己按场景拆 |

### 5.2 仍然必须由我们自己做的

| 我们的问题 | 为什么必须自己做 |
|------|------|
| `第xx章`、`这一卷`、`上一章` 等正文元信息泄漏 | 这是小说正文边界问题，不是通用 prose lint 的强项 |
| POV 越界 | 需要结合小说视角、动作桥接词、感知词，本质是叙事边界规则 |
| 首卷复杂度预算 / 疑点回收率 / 爽点兑现 | 这是故事结构 gate，不是外部 detector 的通用能力 |
| 伏笔债务、设定 onboarding、角色状态延续 | 需要消费我们自己的 story protocol 真相层 |
| `@{}` 实体包裹、人物/势力/物品建档闭环 | 这是本项目独有协议问题，外部仓库无法替代 |

### 5.3 只适合做实验后端的

| 来源 | 原因 |
|------|------|
| `Binoculars` | 更像“这段像不像模型生成”，无法直接告诉作者该改哪句 |
| `DetectGPT` | 研究价值高于产品价值，中文小说场景稳定性不明 |
| `SeqXGPT` | 潜力在细粒度热区，不在可解释修稿规则；依赖也偏重 |

## 6. 推荐吸收方式

### Phase A: 先借规则，不加依赖

优先吸收：

1. `textlint-rule-preset-ai-writing`
2. `textlint`
3. `Vale`
4. `proselint`
5. `write-good`

落地方向：

- 扩充我们自己的中文高频 AI 句式簇
- 补更多 `message/evidence/suggestion` 模板
- 完善 `review-rules.yaml` 的白名单思路
- 给 `style/review` 增加更清晰的 rule taxonomy

适合立刻转成本地规则的簇：

1. `contrastFlipPattern`
2. `analogicalPivotPattern`
3. `templateCatchphrasePattern`
4. `paragraphReadability`
5. `clusteredAIPhrasing`

### Phase B: 做可选 backend，而不是主链依赖

首选：

1. `Vale`
2. `textlint`

原因：

- 都是成熟 lint 框架
- 强项在规则执行、样式包、豁免与 CI 集成
- 比黑盒 AI detector 更符合“给出具体可修问题”的目标

建议接法：

- 放在 `providers/` 下做 optional CLI/backend wrapper
- `commands/style.py` 负责装配
- `services/style_detector.py` 负责统一结果归并
- 缺失依赖时自动回退 builtin path

### Phase C: 只把黑盒 detector 留作卷级实验信号

适用对象：

1. `Binoculars`
2. `SeqXGPT`
3. `DetectGPT`

建议限制：

- 不进入章节 gate 阻塞
- 不作为单条规则结论
- 只允许挂在 `styleAnalysis.extensions.experimental` 或卷级实验报告
- 必须附上“不可解释，不可单独作为修稿依据”的标识

## 7. 建议功能映射

| 下一步功能 | 最值得参考的外部来源 | 备注 |
|------|------|------|
| 中文 AI 高频句式簇 | `textlint-rule-preset-ai-writing`、`proselint`、`write-good` | 借分类与提示语，不借语言实现 |
| 规则豁免协议 | `textlint`、`Vale` | 继续坚持白名单，不走黑名单 |
| 段长/句长/可读性 | `Vale`、`ja-technical-writing`、`novel-writer-style-cn` | 需要按小说题材定阈值 |
| 外部可选 lint backend | `Vale`、`textlint` | 优先于黑盒 AI authorship detector |
| 实验性 AI 疑似热区 | `SeqXGPT`、`Binoculars` | 仅做实验性附加信号 |

## 8. 当前推荐结论

如果只选一批最值得马上用的开源来源：

1. `textlint-rule-preset-ai-writing`
2. `textlint`
3. `Vale`
4. `proselint`
5. `write-good`

原因不是它们能直接解决中文网文问题，而是它们最适合帮助我们补齐：

- 规则分类方式
- 白名单 / 豁免机制
- 证据与修稿建议输出结构
- 句式复用与可读性辅助信号

如果只选一批值得持续观察、但不该现在直接上主链的：

1. `SeqXGPT`
2. `Binoculars`
3. `DetectGPT`

## 9. 对当前项目的直接建议

结合这轮调研，最合理的执行顺序是：

1. 先在本仓库补中文高频 AI 句式簇
2. 再把 `paragraphReadability` 与段长/句长阈值补进 `style/review`
3. 再评估是否需要一个 `Vale` 或 `textlint` optional adapter
4. 最后才决定要不要保留 `SeqXGPT/Binoculars` 这类实验 detector

换句话说：

- **现在最该做的是“借规则、借机制、借输出形态”**
- **不是马上把黑盒 detector 接进主流程**

## 10. 资料入口

- `textlint-rule-preset-ai-writing`: <https://github.com/textlint-ja/textlint-rule-preset-ai-writing>
- `textlint`: <https://github.com/textlint/textlint>
- `Vale`: <https://github.com/vale-cli/vale>
- `proselint`: <https://github.com/amperser/proselint>
- `write-good`: <https://github.com/btford/write-good>
- `textlint-rule-preset-ja-technical-writing`: <https://github.com/textlint-ja/textlint-rule-preset-ja-technical-writing>
- `novel-writer-style-cn`: <https://github.com/lsg1103275794/novel-writer-style-cn>
- `Chinese Copywriting Guidelines`: <https://github.com/sparanoid/chinese-copywriting-guidelines>
- `Binoculars`: <https://github.com/ahans30/Binoculars>
- `DetectGPT`: <https://github.com/eric-mitchell/detect-gpt>
- `SeqXGPT`: <https://github.com/Jihuai-wpy/SeqXGPT>
- `LLM-generated-Text-Detection`: <https://github.com/NLP2CT/LLM-generated-Text-Detection>
