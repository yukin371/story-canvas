# 2026-04-29 Agent Writing Workflow E2E

## 目标

- 用真实 CLI 流程验证一次“repo-local skill + 项目工具 + 卷级闭环 + 人类审查交接”。
- 明确区分：
  - `author`：写作与修稿执行
  - `editor`：卷级独立审查与放行判断

## 适用规则

- 当前执行入口：`docs/roadmap.md`
- Canonical 写作规则：`docs/guides/writing-rules.md`
- Canonical 卷级自审规则：`docs/guides/volume-self-review.md`
- Canonical 流程：`docs/guides/creative-workflow.md`
- Repo-local Codex skill：`.codex/skills/story-harness-writing/`
- 架构护栏：adapter 只做流程与规则适配，仓库协议与 CLI 仍是真相源

## 测试范围

1. 在隔离项目中跑一次真实起步：
   - `status`
   - `context refresh`
   - `outline check`
2. 用 skill 规则组织 author 行为，完成至少一个可视为卷级小故事单元的正文与章级闭环。
3. 运行卷级流程：
   - `review preflight`
   - `review volume-self-template`
   - `review volume-self`
   - `workflow status --volume-id`
   - `export --format review-packet --volume-id`
4. 用 fresh-context editor pass 做独立编辑审查。

## 项目策略

- 新建隔离项目，避免污染现有样例工程。
- 优先做短卷 / 小故事单元，降低无关变量。
- 所有可复核结论都以仓库产物落盘为准。

## 验证

1. skill 规则已被显式读取并用于起步判断。
2. CLI gate 实际运行，不靠口头模拟。
3. 卷级自审结果成功写入。
4. review packet 成功导出，可供人类审查。
5. 独立编辑结论与风险摘要可复核。

## 风险

- 当前仓库工作树已存在大量未提交改动，因此测试项目必须隔离。
- 新项目正文质量不代表仓库最终写作上限，本轮主要验证“流程能否被代理稳定执行并交接给人类”。

## 执行结果

- 已创建隔离项目：`projects/agent-volume-e2e-20260429`
- 已通过 repo-local skill + CLI 完成两章 author 流程、章级 review/revise/recheck、卷级 preflight、volume-self-template、review packet 导出。
- 已引入多代理分工：
  - `Kant` 作为 fresh-context `editor` 完成独立卷审，结论为 `revise`
  - `Volta` 作为 workflow auditor 校验 gate 与交接条件
- 已落盘卷级自审输入：`projects/agent-volume-e2e-20260429/reviews/volume-001-self-review.yaml`
- `python -m story_canvas review volume-self --root .\projects\agent-volume-e2e-20260429 --volume-id volume-001 --input .\projects\agent-volume-e2e-20260429\reviews\volume-001-self-review.yaml`
  - 成功写入
  - `closureStatus=closed`
  - `finalAllowHumanReview=false`
  - gate failures:
    - `volume-self-review-declared-blocked`
    - `volume-self-review-editor-verdict-blocking`
- `python -m story_canvas workflow status --root .\projects\agent-volume-e2e-20260429 --volume-id volume-001`
  - `volume_preflight_ready=ready`
  - `volume_tooling_gate=ready`
  - `human_review_ready=blocked-by-volume-self-review`
  - repair coverage: `complete`
  - 弱项维度: `对手塑造` / `冲突升级`
- 已重新导出审查包：`projects/agent-volume-e2e-20260429/reviews/volume-001-review-packet.md`

## 结论

- 这次真实流程证明：
  - repo-local skill 可以在开工前提供规则入口
  - CLI 能把 author / editor / auditor 结果统一收束到卷级 gate
  - 多代理参与后可以形成可复核证据链，而不是口头声称“已审过”
- 当前版本尚未通过 `human_review_ready`
  - 主要不是工具链失效，而是独立编辑真实判定该卷仍需修稿
  - 因此这是一次“流程真实挡下未达标版本”的有效 E2E 测试，而不是一次放行样例
