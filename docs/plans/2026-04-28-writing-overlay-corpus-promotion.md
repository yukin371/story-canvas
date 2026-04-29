# 2026-04-28 Writing Overlay Corpus Promotion

## 1. 背景

- 目标：判断 `noval-data` 现有语料分析资料，哪些已经足够支撑 `story-harness-writing` 的下一层 overlay。
- 范围：只处理 adapter 文档，不改 CLI、协议或 review 规则。
- 原则：
  - 只提升有真实语料支撑的 overlay
  - adapter 保持“薄”，不把分析工作台全文搬入 skill
  - 一个 overlay 只补普适层没有的题材差异

## 2. 证据入口

- `noval-data/basic-sample-gap-matrix.md`
- `noval-data/tag-taxonomy.md`
- `noval-data/review-index.md`
- `noval-data/analysis-workbench/indexes/progress-board.md`
- `noval-data/analysis-workbench/synthesis/genre-overlays/README.md`
- `noval-data/analysis-workbench/synthesis/genre-overlays/*.md`

## 3. 本轮提升到 writing skill 的 overlay

### 3.1 直接提升

1. `female-cultivation-growth`
   - 理由：`3` 本样本，archetype README 与 synthesis overlay 都已形成稳定“改命 + 关系重建 + 修行站位”模型。
2. `school-romcom`
   - 理由：`3` 本样本，单章 loop、固定社交场、关系推进与对白职责都已沉淀。
3. `horror-game`
   - 理由：`2` 本对照样本，规则求生与主角例外项的双线消费点已经稳定。
4. `historical-power`
   - 理由：`4` 本样本，历史经营、军政项目和时代危机绑定方式已经明确。
5. `gender-bender-yuri`
   - 理由：`4` 本样本，身份错位、关系重排、现实锚点与创伤修复模型都已形成。
6. `urban-supernatural-mystery`
   - 理由：`2` 本样本，身份谜团与世界异常双线推进模型已稳定。
7. `academy-supernatural-action`
   - 理由：`2` 本样本，学院筛选、高考/选拔、例外天赋与公开兑现闭环已明确。
8. `evil-path-cultivation`
   - 理由：`2` 本样本，代价型变强、黑暗秩序压迫与摆脱首层控制结构已明确。
9. `mystery-supernatural-horror`
   - 理由：`2` 本样本，民俗异事、法门入行与单元异事接长线真相的写法已沉淀。

### 3.2 带范围护栏提升

1. `historical-court-politics`
   - 当前可覆盖：驸马 / 质子 / 厂卫 / 债务官场 / 低位入局型朝堂权谋。
   - 暂不冒充：纯内阁 / 纯党争 / 更高层帝王心术全覆盖。
2. `post-apoc-scifi`
   - 当前可覆盖：废土底层上升 / 特区秩序 / 现代末世团队生存。
   - 暂不冒充：军事科幻 / 硬科幻 / 大规模军团推演全覆盖。
3. `acg-fanfic-action`
   - 当前可覆盖：熟悉 IP + 外来体系改线、现代学院/都市切口、聊天群/多世界/圣女代行等“动作改线型”同人。
   - 暂不冒充：所有 ACG 同人的统一总纲。

## 4. 本轮暂不提升

1. `entertainment-industry`
   - 原因：当前只有 `1` 本样本，虽已有 seed overlay，但仍容易把综艺/平台创业线误写成整个娱乐圈主 loop。
2. `lord-building`
   - 原因：缺口矩阵明确仍是高优先级缺口。
3. `political-intrigue-fantasy`
   - 原因：当前缺稳定对照样本。
4. `wuxia-jianghu`
   - 原因：当前只有 `1` 本样本，且偏怪异江湖，不能代表更广的武侠底板。
5. `mystery-detective`
   - 原因：当前只有 `1` 本样本，仍缺第二本对照样本来防止被单书绑架。

## 5. 落地方式

1. 更新 `adapters/codex-skill/story-harness-writing/references/genre-overlays.md`
2. 更新 `adapters/claude-code/story-harness-writing/references/genre-overlays.md`
3. 为两宿主新增同名 overlay reference 文件，内容压缩成可执行写法说明
4. 在索引中写清哪些是可直接加载，哪些必须带范围护栏
5. 在索引中补“相近题材如何判主包”，避免多包误叠和误选

## 6. 验证

1. 逐项核对提升名单是否能回链到 gap matrix、review index 和 synthesis overlay
2. 核对 Codex / Claude 两套 writing skill 是否同步
3. 核对 `Still TBD` 是否保留真正弱覆盖项
4. 核对相近 overlay 的分界是否清楚，不把职业民俗、身份谜团、惊悚副本等近邻题材混写
