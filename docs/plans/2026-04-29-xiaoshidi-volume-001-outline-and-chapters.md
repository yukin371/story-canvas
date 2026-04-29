# `xiaoshidi-bailan` 卷级骨架补齐与前三章闭环计划

> 日期: `2026-04-29`
> 状态: `completed`
> 适用项目: `projects/xiaoshidi-bailan`

## 1. 背景

当前 `projects/xiaoshidi-bailan` 已有：

- `project.yaml` 中明确的作品 promise、`paceContract` 与 `endingContract`
- `chapter-001` 的正文与章节闭环基础
- 一个能被 CLI 识别的 `volume-001` 壳

当前缺口：

- 卷级 outline 只有 `chapter-001`，不具备真实卷级闭环所需的 2-3 章连续骨架
- `review preflight` / `workflow status --volume-id` 会把“单章卷壳”误判成具备卷审最低前提
- 项目尚未交付 `paceContract` 中承诺的前三章内容

## 2. 本轮适用规则

- 当前执行入口：`docs/roadmap.md`
  - 真实长篇样例必须证明“章节闭环 ≠ 卷级闭环”
  - `Track 2/3` 要求至少一个长篇项目跑通规划、写作、审查、修正与卷级自审
- 架构护栏：`docs/ARCHITECTURE_GUARDRAILS.md`
  - 样例工程协议真相以项目协议文件为准，不引入平行状态源
- 项目模块不变量：`projects/xiaoshidi-bailan/MODULE.md`
  - 第一章必须承担机制起势与误判链建立
  - 在前三章真正写完前，不得把 `volume-001` 误判成首卷已完结
  - 显式 `scenePlans` 必须与正文段落边界同步
- 写作流程与卷审规则：
  - `docs/guides/creative-workflow.md`
  - `docs/guides/volume-self-review.md`
  - `.codex/skills/story-harness-writing/references/workflow-gates.md`
- 本轮适用 AI friction：
  - `AIF-003` 状态产物刷新不一致
  - `AIF-005` 闭环命令编排过碎
  - `AIF-006` 多命令并行写入会触发 stale snapshot
  - `AIF-010` 卷级预检未消费卷目标 / 章数承诺
  - `AIF-011` UI 无法支撑卷级审查

## 3. 问题记录

### 3.1 已确认问题

1. 之前所谓“卷级闭环完成”实际只是卷级命令链跑通，不是内容闭环完成。
2. 当前 `outline.yaml` 中的 `volume-001` 只有单章，不能支撑章间承接、阶段性胜负和卷内回收判断。
3. 当前 UI 不能完成角色卡 / 世界设定 / 卷结构 / 审查包的一站式核对。

### 3.2 本轮目标

1. 把 `volume-001` 补成真正可执行的三章开卷骨架
2. 完成 `chapter-002`、`chapter-003` 正文
3. 让前三章至少兑现：
   - 主角异常机制展示
   - 第一次外部挑衅
   - 一次清晰打脸
   - 至少两位师姐的强记忆点
   - 宗门内对陆闲价值的阶段性确认

## 4. 卷级设计

### 4.1 卷问题

陆闲能否在黑沙门踩脸、宗门赌约压顶的三天内，一边继续伪装摆烂，一边被迫交出足以保住宗门脸面的第一次破局，并因此失去继续低调混日子的空间。

### 4.2 三章骨架

1. `chapter-001`
   - 负责：机制起势、宗门破落、黑沙门挑衅、祝红绫第一次严重误判
2. `chapter-002`
   - 负责：后果落地、核心师姐团开始围绕陆闲布局、黑沙门进一步试探、第一次阶段性打脸雏形
3. `chapter-003`
   - 负责：公开反击、宗门内身份反转、核心师姐团确认陆闲价值、保留更大格局尾巴

### 4.3 章节承接要求

- `chapter-002` 开头必须直接承接 `chapter-001` 结尾的“被大师姐带走、失去摆烂空间”
- `chapter-003` 开头必须承接 `chapter-002` 留下的“黑沙门第二轮挑衅 / 东侧水井或小比前试压”
- 每章结尾都要同时做到：
  - 回应至少一条旧问题
  - 抬升至少一条新问题

## 5. 本轮改动范围

- 协议层：
  - `projects/xiaoshidi-bailan/outline.yaml`
  - `projects/xiaoshidi-bailan/detailed_outlines.yaml`
  - 必要时 `project.yaml` / `worldbook.yaml` / `entities.yaml`
- 正文层：
  - `projects/xiaoshidi-bailan/chapters/chapter-002.md`
  - `projects/xiaoshidi-bailan/chapters/chapter-003.md`
- 过程记录：
  - 必要时 `docs/tracking/ai-friction-tracker.md`
  - 完成后同步 `projects/xiaoshidi-bailan/MODULE.md`

## 6. 验证计划

按串行方式执行，避免触发 `AIF-006`：

1. `outline check --root projects/xiaoshidi-bailan --chapter-id chapter-002`
2. `outline check --root projects/xiaoshidi-bailan --chapter-id chapter-003`
3. `chapter analyze -> chapter suggest -> review apply -> projection apply -> context refresh -> review chapter -> review scene` 分别对 `chapter-002/003` 串行执行
4. `review preflight --root projects/xiaoshidi-bailan --volume-id volume-001`
5. `workflow status --root projects/xiaoshidi-bailan --volume-id volume-001`
6. 如需，重新生成 `review volume-self-template`

## 7. 风险

- 架构风险：
  - 若只补正文不补卷级 outline，会继续把“项目契约”与“执行骨架”分离
- 重复实现风险：
  - 若同时手工维护多份卷级说明，容易产生平行真相源
- 兼容性影响：
  - 新增章节会改变 `status`、`workflow` 与 volume review 的聚合结果
- 回滚路径：
  - 仅回滚 `projects/xiaoshidi-bailan/*` 与本计划文档即可

## 8. 本轮结果

1. `volume-001` 已从单章卷壳扩成真实三章开卷样例，`chapter-002`、`chapter-003` 正文与细纲边界均已落库。
2. `chapter-002`、`chapter-003` 的 `outline check` 已通过，章节闭环命令链已串行跑完。
3. 卷级 `mention hygiene` 已清零，`review-packet` 已自动刷新，不再卡在 tooling gate。
4. 新的卷级自审已写回：
   - `closureStatus = closed`
   - `allowHumanReview = false`
   - 当前 `workflow status --volume-id volume-001` 已推进到 `human_review_ready`，但被 `styleReadability = 2/5` 与 editor `revise` 阻塞
5. 本轮新增并确认了 `AIF-012`：
   - 已兑现 beat 会被 `review chapter / review scene` 稳定误报为 `outlineDeviation`
