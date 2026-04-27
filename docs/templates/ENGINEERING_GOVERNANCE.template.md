# [仓库名] 工程治理规范

> 最后更新: YYYY-MM-DD
> 状态: 当前有效工程治理文档

## 1. 目的

本文件用于定义仓库的最低工程门禁与提交流程，覆盖:

- 提交规则
- review 规则
- CI / required checks
- release / versioning
- 安全与依赖治理

## 2. 规则生命周期

### 2.1 开发前规则发现

- 非平凡改动开始前，必须整理“适用规则”摘要。
- “适用规则”至少应覆盖：
  - 当前执行入口
  - 架构护栏 / canonical owner
  - 目标模块文档中的职责与不变量
  - CLI / schema / 输出结构 / 文件协议兼容性
  - 必要时补充 ADR、plan 和现有测试基线
- 如果规则缺失，允许写 `TBD`，但必须附确认路径；不允许直接用抽象工程口号替代。

### 2.2 开发中规则遵循

- 实现应优先遵守 canonical owner、既有不变量和协议边界。
- 禁止因为“想更 clean”或“更符合 SOLID”而单独发起改动；必须翻译成仓库内可验证的风险。
- 如果本轮新增规则例外、owner 变化或边界变化，必须同步对应文档。

### 2.3 PR 审查口径

- PR 或自审必须围绕“适用规则”展开，而不是围绕抽象风格好恶。
- 每个非平凡 PR 至少回答：
  - 本次改动受哪些规则约束
  - 是否跨越 canonical owner 或依赖方向
  - 是否引入 breaking change、行为变化或新的规则例外
  - 是否产生重复规则定义、重复配置入口或平行真相源
  - 验证、文档同步和残留风险是什么

## 3. 分支与合并策略

- 默认开发分支:
- 默认发布分支:
- 允许的合并方式:
- 禁止的合并方式:

## 4. Required Checks

- build:
- test:
- lint:
- security:
- docs:

当前未启用项:

- `TBD`

## 5. Review 规则

- 至少需要几位 reviewer:
- CODEOWNERS 是否启用:
- 哪些目录必须 owner review:
- 什么情况下禁止自合并:

## 6. 提交规则

- commit message 格式:
- 是否采用 Conventional Commits:
- 是否允许空 body:
- 禁止的 trailer / 元信息:

## 7. 本地治理防线

- `pre-commit` hook:
- `commit-msg` hook:
- commit template:
- PR template:

## 8. CI 治理防线

- 提交信息校验:
- 协作者标记校验:
- PR 描述校验:
- branch protection / rulesets:

## 9. 版本与发布

- 版本策略:
- prerelease 规则:
- breaking change 处理方式:
- release note owner:

## 10. 安全与依赖治理

- secret 管理策略:
- 依赖升级策略:
- 安全扫描策略:
- 高风险目录:

## 11. 待确认项

- `TBD`
- `TBD`
