# Story Canvas 工程治理规范

> 最后更新: 2026-04-22
> 状态: 当前有效工程治理文档

> 命名说明: 文档面对外使用 `Story Canvas`，但 `story-harness` CLI 与 `story_harness_cli` 包路径仍处于兼容保留状态

## 1. 目的

本文件用于定义仓库的最低工程门禁与提交流程。

## 2. 规则生命周期

### 2.1 开发前规则发现

- 非平凡改动开始前，必须整理一份“适用规则”摘要。
- “适用规则”至少应覆盖：
  - `docs/roadmap.md` 当前入口
  - `docs/ARCHITECTURE_GUARDRAILS.md` 中的 owner / dependency guardrail
  - 目标模块 `MODULE.md` 的职责、不变量和常见坑
  - CLI / schema / 输出结构 / 文件协议兼容性
  - 必要时补充 ADR、plan 和现有测试基线
- 如果规则缺失，允许写 `TBD`，但必须附确认路径；不允许直接用抽象工程口号替代。

### 2.2 开发中规则遵循

- 实现应优先遵守 canonical owner、既有不变量和协议边界。
- 禁止因为“想更 clean”或“更符合 SOLID”而单独发起改动；必须翻译成仓库内可验证的风险：
  - 重复实现
  - 平行真相源
  - 依赖方向错误
  - undocumented exception
  - breaking change
  - 测试 / 文档同步失败
- 如果本轮新增规则例外、owner 变化或边界变化，必须同步对应文档。

### 2.3 PR 审查口径

- PR 或自审必须围绕“适用规则”展开，而不是围绕抽象风格好恶。
- 每个非平凡 PR 至少回答：
  - 本次改动受哪些规则约束
  - 改动是否跨越 canonical owner 或依赖方向
  - 是否引入 breaking change、行为变化或新的规则例外
  - 是否产生重复规则定义、重复配置入口或平行真相源
  - 验证、文档同步和残留风险是什么
- 评审意见必须尽量引用具体文件、规则或不变量；“不够 clean code / 不够 SOLID”不能作为独立 blocker。

## 3. 分支与合并策略

- 默认开发分支: `main`
- 默认发布分支: `main`
- 允许的合并方式: squash merge, merge commit
- 禁止的合并方式: force push to main

## 4. Required Checks

- build: `pip install -e .` 成功（当前因 SSL 问题用 `PYTHONPATH=src` 替代）
- test: `PYTHONPATH=src python -m unittest discover -s tests` 全部通过
- lint: TBD（建议 ruff，待启用）
- security: TBD（零依赖项目，安全风险较低）
- docs: 若涉及边界、owner、协议、输出或治理口径变化，相关文档必须同步

## 5. Review 规则

- 至少需要几位 reviewer: TBD（单人维护项目，暂无强制 reviewer 数量）
- CODEOWNERS 是否启用: 否
- 哪些目录必须 owner review: TBD
- 什么情况下禁止自合并:
  - breaking change 未说明
  - 适用规则未列出
  - 验证结果缺失
  - 边界变化但文档未同步

## 6. 提交规则

- commit message 格式: Conventional Commits `<type>(<scope>): <description>`
- 是否采用 Conventional Commits: 是
- 是否允许空 body: 是（小改动可省略 body）
- 禁止的 trailer / 元信息: `Co-Authored-By:`, `Pair-Programmed-By:`, AI 工具签名

## 7. 本地治理防线

- `pre-commit` hook: 已提供 `.githooks/pre-commit`，检查敏感文件、AI 协作者标识和明显产物误提交；还会基于 staged files 提示本次改动 likely 受哪些规则约束，并对可能遗漏的文档同步给出 warning
- `commit-msg` hook: 已提供 `.githooks/commit-msg`，调用 `scripts/check_commit_message.sh` 校验 Conventional Commits 与禁用 trailer
- commit template: TBD
- PR template: 使用 `.github/pull_request_template.md` 显式记录适用规则、验证结果与残留风险

## 8. CI 治理防线

- 提交信息校验: 已在 `.github/workflows/ci.yml` 中校验 push / pull_request 范围内的 commit message
- 协作者标记校验: TBD
- PR 描述校验: 已在 `.github/workflows/ci.yml` 中校验非 draft PR 的 `Applicable Rules`、`Review Checklist`、`Validation`、`Risks`
- branch protection / rulesets: TBD

## 9. 版本与发布

- 版本策略: Semantic Versioning（当前 `0.1.0`）
- prerelease 规则: TBD
- breaking change 处理方式: 在 commit message 和 CHANGELOG 中标注 `BREAKING CHANGE`
- release note owner: 维护者

## 10. 安全与依赖治理

- secret 管理策略: 不将 secrets 写入仓库
- 依赖升级策略: 零外部依赖，无需升级
- 安全扫描策略: TBD（零依赖项目风险低）
- 高风险目录: `adapters/`（涉及宿主文件系统写入）

## 11. 待确认项

- CI 平台选型与配置: TBD（确认路径：维护者决定）
- lint 工具选型: TBD（建议 ruff）
- 发布到 PyPI 的流程: TBD
