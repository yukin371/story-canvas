# 写作工作流痛点修复设计

> 日期: `2026-04-29`
> 状态: `proposed`
> 范围: `workflow / review / writing sample / review workbench`

## 1. 背景

本轮 `projects/xiaoshidi-bailan` 的真实实跑已经把“卷级内容闭环”和“人工审查放行”明确拆开，但也再次暴露出若干工具层痛点：

1. 工具能跑，不代表判断口径可靠。
2. 章节 / 场景评审的局部信号会污染卷级判断。
3. workflow gate 已经能拦人，但给出的阻塞原因仍混有噪音或上下文缺失。

本设计不直接改代码，先把本轮最值得修的痛点收敛成可执行方案，供后续实现按优先级推进。

## 2. 本轮适用 pain ids

- `AIF-003` 状态产物刷新不一致
- `AIF-005` 真实闭环命令编排过碎
- `AIF-006` 多命令并行写入不适合批量建档
- `AIF-010` 卷级预检未消费卷目标 / 章数承诺
- `AIF-011` 本地 UI 审查工作区缺少核心卷审视图且项目切换会残留旧章节
- `AIF-012` 章节/场景评审会对已兑现 beat 稳定误报 `outlineDeviation`

## 3. 设计目标

1. 让 `workflow status`、`review preflight`、`review chapter/scene` 的结论更接近真实创作状态，而不是只反映“命令是否执行过”。
2. 让 volume gate 先消费结构化卷目标，再消费局部 review 信号，避免单个 noisy rule 把卷审判断带偏。
3. 让 review workbench 至少具备“人工不用退回文件系统也能完成首轮卷审”的最小能力。
4. 让后续实现优先修“会导致错误判断”的痛点，而不是先修“只是多点几下”的痛点。

## 4. 优先级排序

### P0: `AIF-012` 已兑现 beat 误报 `outlineDeviation`

#### 为什么先修

- 它直接制造错误结构判断。
- 它会污染 chapter review、scene review、volume preflight 三层输出。
- 它会诱导作者为了迎合检测器去重写已经成立的正文。

#### 设计

1. 把 beat 命中判断从“只有 warning 结果”改为“先产出 coverage evidence，再做 judgement”。
2. 在 `chapter analyze` 或独立 coverage 函数中生成 `beatCoverage`：
   - `beatId`
   - `matchedParagraphs`
   - `matchedSceneIndexes`
   - `matchedSnippets`
   - `matchConfidence`
   - `missReason`
3. `review chapter` 只对 `matchConfidence < threshold` 的 beat 产生 `outlineDeviation`。
4. `review scene` 不再机械复制整章所有 beat warning。
   - 只显示与当前 scene 段落范围相交的 beat miss。
5. `outlineDeviation` 的 payload 必须带至少一项：
   - 命中段落证据
   - 未命中原因
   - 被排除原因

#### Canonical owner

- `outline.yaml` / `detailed_outlines.yaml`: beat 与 scene 真相
- review 层: 只消费 coverage，不再自行黑箱推断

#### 验证

- `review chapter --chapter-id chapter-002`
- `review chapter --chapter-id chapter-003`
- `review scene --chapter-id chapter-003 --scene-index 1`
- 新 smoke test:
  - 已兑现 beat 不应触发 `outlineDeviation`
  - scene review 只报告 scene-local miss

### P1: `AIF-010` volume preflight 不消费卷目标 / 章数承诺

#### 问题本质

当前 `volumeStructureCheck.closure-readiness` 只验证“卷尾章是否有正文、伏笔是否没爆表”，没有验证“这是不是该卷承诺的小故事交付”。

#### 设计

1. 不再尝试从自然语言 `paceContract` 直接硬解析全部卷目标。
2. 增加结构化卷级契约字段，建议放在 `outline.yaml` 的 volume 节点下：
   - `closureContract.requiredChapterCount`
   - `closureContract.requiredDeliveries[]`
   - `closureContract.requiredPayoffs[]`
   - `closureContract.minCoreCastCount`
   - `closureContract.allowHumanReviewPrereqs[]`
3. `project.yaml.storyContract.paceContract` 继续保留为面向人类的文字承诺；
   `outline.yaml.volumes[].closureContract` 作为 repo-native gate 输入。
4. `review preflight` 新增 `volumeContractCheck`：
   - `pass / risk / missing`
   - `missingDeliveries[]`
   - `missingChapterCount`
5. `workflow status --volume-id` 的 `volume_preflight_ready` 必须先看 `volumeContractCheck`，再看 scene / style / self-review。

#### Canonical owner

- 结构化卷级 gate 真相：`outline.yaml` 的 volume 节点
- 人类描述性承诺：`project.yaml.storyContract`

#### 验证

- `review preflight --volume-id volume-001`
- `workflow status --volume-id volume-001`
- 新 smoke test:
  - 单章卷壳 + `requiredChapterCount=3` 时不得通过 `closure-readiness`
  - 内容已成三章闭环时允许进入下一 gate

### P1: `AIF-003` context / workflow 摘要不同步

#### 问题本质

`context refresh` 已更新最新 hash，但 `workflow status/run` 仍可能继续读旧 hash，调用方无法判断是命令漏跑还是摘要层滞后。

#### 设计

1. `workflow status/run` 不再持有独立的 context hash 副本。
2. workflow 层统一从最新 `context-lens` 或其 canonical metadata 读取：
   - `chapterContentHash`
   - `updatedAt`
   - `chapterId`
3. 若 workflow 读到的 context 缺章或缺 hash，应返回：
   - `missing-context`
   而不是继续比较旧快照。
4. 若要保留 cache，只允许 cache metadata，不允许 cache参与 gate 判断的 hash 真值。

#### Canonical owner

- context 真相：`context-lens.yaml` / refresh 产物
- workflow: 只读，不复制 hash 真值

#### 验证

- `context refresh --chapter-id chapter-003`
- `workflow status --chapter-id chapter-003`
- 新 smoke test:
  - refresh 后 workflow 读取同一 hash

### P2: `AIF-011` review workbench 缺少卷审最小视图

#### 设计目标

让人工 reviewer 至少能在 UI 内完成以下动作，而不是退回文件系统：

1. 看角色卡详情
2. 看世界设定摘要
3. 看卷结构与章节 phase
4. 看最新 review packet / volume-self summary
5. 切项目时不残留旧 chapter

#### 设计

1. `ProjectSummary` 明确暴露：
   - `entities.profile`
   - `worldbook.entries`
   - `volumes[].chapters`
   - `reviewPackets[]`
   - `latestVolumeSelfReviewSummary`
2. `ReviewWorkbenchPane` 增加四个只读面板：
   - 角色详情
   - 世界设定
   - 卷结构
   - 审查包预览
3. `selectedChapter` 身份键改为：
   - `projectRoot + chapterId`
4. 资料面板先做只读展开，不在第一版同时承担编辑职责。

#### 验证

- 本地切换两个都含 `chapter-001` 的项目
- UI 内核对 `xiaoshidi-bailan` 的角色、worldbook、volume-001、review packet

### P2: `AIF-005` / `AIF-006` 闭环编排仍过碎

#### 设计

1. 给会写状态的命令补 `writesProjectState=true` 元数据。
2. `workflow status` 的 `orchestrationPlan` 输出区分：
   - `safeReadCommands`
   - `mustRunSerially`
3. 后续可选增加 repo-native 串行执行器：
   - `workflow run --chapter-id <id> --profile chapter-closure`
   - 第一版只按固定顺序串行调用，不做并行
4. 在没有执行器前，至少先把“这些命令会写状态，不能并行”变成命令元数据，而不是靠调用方踩坑记忆。

#### 验证

- `workflow status --chapter-id chapter-003`
- `workflow status --volume-id volume-001`
- 新 smoke test:
  - orchestration plan 明确区分 serial steps

## 5. 推荐实现顺序

1. `AIF-012`
2. `AIF-010`
3. `AIF-003`
4. `AIF-005` / `AIF-006`
5. `AIF-011`

理由：

- 前三项直接影响“系统是不是在说真话”。
- 后两项更多影响“系统好不好用、审查是否顺手”。

## 6. 非目标

1. 不在这一轮引入新的平行 workflow 状态文件。
2. 不把自然语言合同解析做成黑箱 NLP gate。
3. 不为了压误报去修改 `xiaoshidi-bailan` 已成立的正文。
4. 不在第一版 UI 修复里同时引入可写编辑器。

## 7. 建议拆票

1. `review: add beat coverage evidence and scene-local outline deviation`
2. `workflow/review: add structured volume closure contract`
3. `workflow: unify context hash source with context refresh`
4. `workflow: expose serial-write command metadata`
5. `ui: add review workbench detail panes and chapter identity fix`

## 8. 本轮结论

本轮最重要的不是再证明一次“命令能跑”，而是把以下事实固定下来：

1. `volume-001` 的内容闭环已经成立。
2. 当前未放行人工审查，主要是 `styleReadability` 和局部修稿问题，不是再缺章节。
3. 后续工具修复优先级应先围绕“减少误判”，再围绕“减少操作碎片”。
