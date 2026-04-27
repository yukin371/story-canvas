# AI Repo Bootstrap Playbook

> 版本: v2
> 目标: 让 AI 在一个全新或存量仓库中，建立可持续的工程治理骨架，而不是直接开始堆实现
> 适用范围: Web / 桌面 / 后端 / CLI / 库 / 脚本 / monorepo / 平台仓库
> 推荐用法: 与 `docs/templates/` 模板套件配合使用，先实例化骨架，再进入具体功能开发

## 1. 使命

你的第一目标不是“理解一点代码然后开改”，而是先把仓库建立成一个可持续协作的系统:

1. 建立项目画像
2. 建立 AI 工作规则
3. 建立唯一当前执行入口
4. 建立架构边界和 canonical owner
5. 建立关键模块上下文
6. 建立工程治理门禁
7. 建立设计文档、决策文档与历史归档的生命周期

如果这些骨架缺失，AI 与人工协作会持续在以下问题上漂移:

- 当前入口到底是哪份文档
- 哪个模块才是共享能力 owner
- 什么才算最低验证通过
- 哪些是历史资料，哪些还是当前依据
- 哪些改动必须经过 review、兼容性判断与安全检查

## 2. 不可谈判的强制原则

### 2.1 不编造

- 不确定的事实一律写 `TBD`
- 每个 `TBD` 后必须附确认路径
- 不要把猜测、经验判断或行业通用做法写成该仓库既成事实

### 2.2 先复用后新增

在新增任何 shared helper / utility / service / adapter / workflow 前，必须先搜索现有实现。

如果已有实现存在:

- 优先扩展
- 无法复用时必须说明原因
- 明确新能力的 canonical owner

### 2.3 唯一当前入口

仓库必须只有一个“当前执行真相”入口。

可选形态:

- `docs/roadmap.md`
- `docs/plans/current-execution-control.md`

二选一即可，但禁止并行维护多个“当前计划 / 当前进度 / 执行中计划”文档竞争当前入口。

### 2.4 边界先于实现

在开始非平凡改动前，必须先明确:

- 目标模块
- canonical owner
- 影响面
- 验证方案
- 文档同步范围
- 风险与回滚路径

### 2.5 文档只写高价值信息

文档只记录工具不容易稳定推导的信息:

- 业务意图
- 模块职责
- 依赖边界
- 禁止事项
- 不变量
- 权衡与例外
- 生命周期规则

不要抄源码目录树、函数列表和显而易见的结构。

### 2.6 验证先于完成

任务不算完成，直到:

- 代码或文档已落地
- 验证已执行或阻塞已明确
- 文档已同步
- 没有引入新的重复 owner
- 没有引入新的架构漂移

### 2.7 默认安全

在未确认前:

- 不把 secrets、tokens、keys 写入仓库
- 不降低权限边界
- 不默认新增协作者标记、Co-Authored-By 或类似协作元信息
- 不把安全扫描、review 或 required checks 当成可省略项

## 3. 首次接手仓库时必须交付的产物

### 3.1 核心必交付

1. `docs/PROJECT_PROFILE.md`
2. 根目录 `AGENTS.md`
3. 一个且仅一个当前执行入口:
   - `docs/roadmap.md`
   - 或 `docs/plans/current-execution-control.md`
4. `docs/ARCHITECTURE_GUARDRAILS.md`
5. 1 到 3 个关键模块文档:
   - `MODULE.md`
   - 或模块下 `ARCHITECTURE.md`
6. `docs/plans/YYYY-MM-DD-*.md`
7. `docs/adr/ADR-*.md` 或等价 ADR 命名体系

### 3.2 推荐补交付

8. `docs/ENGINEERING_GOVERNANCE.md`
9. `docs/DOCUMENT_LIFECYCLE.md`
10. `docs/releases/RELEASE_CHECKLIST.md`
11. Git hooks / commit policy / CI governance 资产

## 4. 严格执行顺序

不要一上来批量生成所有文档。严格按下面顺序推进。

### Phase 1. 建立项目画像

产物:

- `docs/PROJECT_PROFILE.md`

事实来源至少覆盖:

1. `README`
2. 依赖声明文件
3. CI / workflow
4. 入口代码
5. 构建、测试、运行脚本
6. 发布相关文件

必须确认:

- 项目类型
- 技术栈
- 运行入口
- 验证命令
- 仓库拓扑
- canonical owner 候选
- 已知高风险区域
- 现有治理资产

输出要求:

- 只写高置信度事实
- 未确认项写 `TBD`
- 不凭经验补齐未知命令

### Phase 2. 建立 AI 工作规则

产物:

- 根目录 `AGENTS.md`

至少写入:

- 修改前必读文件顺序
- 先复用后新增
- 大改前必须输出边界摘要
- 完成后必须输出验证与文档同步结果
- 哪些情况下必须停下并询问
- 不得擅自添加协作者标记与协作元信息

### Phase 3. 建立唯一当前工作面

产物:

- `docs/roadmap.md`
  或
- `docs/plans/current-execution-control.md`

只保留:

- 当前版本目标
- 当前 active tracks
- 当前阻塞
- 待验证项
- 下一步

不要把它写成历史流水账。

### Phase 4. 建立架构边界

产物:

- `docs/ARCHITECTURE_GUARDRAILS.md`

必须明确:

- 模块或层次划分
- 允许的依赖方向
- forbidden imports / forbidden ownership
- 跨切关注点的 canonical owner

典型跨切关注点包括:

- logging
- config
- auth
- persistence
- HTTP / API client
- shared utilities
- UI primitives
- error mapping
- file / path helpers
- feature flags
- release/version metadata

### Phase 5. 建立关键模块上下文

产物:

- 关键目录下的 `MODULE.md` 或等价模块文档

只为关键模块生成，不要铺满全仓库。

优先级:

1. 入口模块
2. 共享能力模块
3. 容易重复造轮子的模块
4. 多人或多代理频繁改动的模块

### Phase 6. 建立工程治理门禁

产物:

- `docs/ENGINEERING_GOVERNANCE.md`
- `docs/DOCUMENT_LIFECYCLE.md`
- `docs/releases/RELEASE_CHECKLIST.md`
- Git hooks / commit policy / CI governance 资产
- `.github/pull_request_template.md`

必须覆盖:

- build / test / lint / security 最低门禁
- PR review / branch protection / CODEOWNERS / required checks
- commit 规则与拦截钩子
- PR 描述中的适用规则、验证结果与残留风险
- release / versioning / breaking change 流程
- 历史文档归档与当前入口切换规则

### Phase 7. 建立任务与决策生命周期

产物:

- `docs/plans/YYYY-MM-DD-*.md`
- `docs/adr/ADR-*.md`

规则:

- 临时方案和实施设计进入 `plans`
- 长期边界决策进入 `ADR`
- 一个 plan 完成后必须归档、收敛为 ADR，或同步到当前入口 / 模块文档后结束

## 5. 最低工程治理要求

### 5.1 验证门禁

每个仓库至少应定义:

1. build
2. test
3. lint
4. security scan

如果暂时无法全部启用:

- 用 `TBD` 说明
- 写出启用路径
- 明确当前最低阻断门槛

### 5.2 PR 与分支治理

至少应明确:

- 默认开发分支
- 合并目标分支
- required checks
- review 要求
- CODEOWNERS 策略
- branch protection 或 rulesets 是否存在
- PR 模板是否要求填写 `Applicable Rules`、`Validation`、`Risks`

### 5.3 提交治理

至少应明确:

- commit message 规则
- 是否采用 Conventional Commits
- 是否允许 squash merge / merge commit / rebase merge
- 禁止 `Co-Authored-By`、`Pair-Programmed-By`、AI 工具签名等协作元信息的规则
- 本地 hook 与 CI 双重防线
- 是否有开发中规则触点提醒

### 5.4 兼容性与破坏性变更

以下变更必须单独说明:

- public API 变化
- CLI 参数或输出变化
- 协议变化
- 数据模型变化
- 配置项变化
- 文件路径或产物路径变化

必须回答:

- 是否 breaking change
- 迁移路径是什么
- 哪些文档和 release note 要同步

### 5.5 安全基线

至少应定义:

- secret 管理边界
- 依赖更新策略
- 权限边界
- 安全扫描策略
- 高风险目录或能力 owner

## 6. AI 自适配规则

### 6.1 Web / 前端项目

重点补:

- 页面入口
- 状态管理 owner
- API client owner
- UI primitives owner
- E2E / 浏览器验证流程

### 6.2 桌面项目

重点补:

- 前后端边界
- IPC / command owner
- 本地数据路径
- 多窗口 / 多进程入口
- 打包与平台特有验证方式

### 6.3 后端服务

重点补:

- API 入口
- service / repository 边界
- 数据库访问 owner
- 配置与鉴权 owner
- 集成测试和部署验证

### 6.4 CLI / 脚本仓库

重点补:

- 命令入口
- 参数解析 owner
- 输出格式约束
- 环境依赖
- 幂等性与安全边界

### 6.5 库 / SDK

重点补:

- public API surface
- compatibility promises
- examples / smoke tests
- versioning strategy
- forbidden internal leakage

### 6.6 Monorepo / 平台仓库

重点补:

- workspace / package / service 边界
- 根治理和子项目治理的继承关系
- shared package owner
- 统一 CI 与分项目 CI 的边界
- 统一发布与分模块发布策略

## 7. 防止 AI 破坏架构的强制问题

在新增任何共享能力之前，必须回答:

1. 我搜索了哪些现有实现？
2. 为什么现有实现不能复用？
3. 新能力的 canonical owner 是谁？
4. 这会不会让两个模块同时拥有相同职责？
5. 哪些文档必须同步？
6. 是否需要 ADR 才能安全落地？

任何一个问题答不清，就先不要新增。

## 8. 文档防腐化规则

### 8.1 项目画像

只在这些变化时更新:

- 技术栈变化
- 构建 / 测试命令变化
- 部署方式变化
- 核心拓扑变化

### 8.2 当前执行入口

只保留 active 内容。

- 已完成历史不要无限累积
- 历史详情转移到 plan / ADR / report / archive

### 8.3 模块文档

只记录:

- 职责
- owner 能力
- 不变量
- 依赖规则
- 常见坑
- 文档同步触发条件

### 8.4 plans

只记录临时设计和实施方案。

- 完成后必须收敛
- 不允许长期堆积成“设计坟场”

### 8.5 ADR

只记录长期有效的决策。

- 普通实现步骤、临时 workaround 不应写成 ADR

### 8.6 issue / report / archive

必须明确这些文档是:

- 当前执行依据
- 背景材料
- 历史材料
- 兼容入口 stub

不要让历史文档伪装成当前入口。

## 9. 每次非平凡改动前必须输出的摘要

```text
目标模块：
现有 owner：
影响面：
计划改动：
验证方式：
需要同步的文档：
```

高风险改动再补:

```text
架构风险：
重复实现风险：
回滚路径：
兼容性影响：
```

## 10. 每次完成后必须输出的摘要

```text
已完成改动：
验证结果：
未验证区域：
同步文档：
残留风险：
```

## 11. 初始化完成标准

### 11.1 仓库 bootstrap 完成

- `PROJECT_PROFILE.md` 已建立
- `AGENTS.md` 已建立
- 唯一当前执行入口已建立
- `ARCHITECTURE_GUARDRAILS.md` 已建立
- 至少 1 到 3 个关键模块有模块文档
- `plans` 与 `ADR` 入口已建立
- 工程治理门禁已定义
- 文档生命周期规则已定义

### 11.2 单次任务完成

- 改动已实施
- 验证已完成或阻塞已说明
- 文档已同步
- 未引入新的重复 owner
- 未引入新的未解释 breaking change

## 12. 与模板套件组合使用

若仓库存在模板目录，优先按以下文件实例化:

- `docs/templates/PROJECT_PROFILE.template.md`
- `docs/templates/AGENTS.template.md`
- `docs/templates/roadmap.template.md`
- `docs/templates/current-execution-control.template.md`
- `docs/templates/ARCHITECTURE_GUARDRAILS.template.md`
- `docs/templates/MODULE.template.md`
- `docs/templates/plan.template.md`
- `docs/templates/ADR.template.md`
- `docs/templates/ENGINEERING_GOVERNANCE.template.md`
- `docs/templates/DOCUMENT_LIFECYCLE.template.md`
- `docs/templates/RELEASE_CHECKLIST.template.md`
- `docs/templates/COMMIT_POLICY.template.md`
- `docs/templates/pull_request_template.template.md`
- `docs/templates/git-hooks/commit-msg.template.sh`
- `docs/templates/git-hooks/pre-commit.template.sh`
- `docs/templates/workflows/governance.template.yml`
- `docs/templates/scripts/check_commit_message.template.sh`
- `docs/templates/scripts/check_commit_messages_range.template.sh`
- `docs/templates/scripts/check_pull_request_template.template.py`
- `docs/templates/scripts/check_rule_touchpoints.template.py`

若模板不存在，再按本文档结构创建最小版本。

## 13. 推荐参考

- GitHub CODEOWNERS: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
- GitHub Rulesets: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets
- GitHub Required Status Checks: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- Go Test: https://go.dev/doc/tutorial/add-a-test
- Go Fuzzing: https://go.dev/doc/security/fuzz/
- Go Module Release Workflow: https://go.dev/doc/modules/release-workflow
- Semantic Versioning: https://semver.org/
- Conventional Commits: https://www.conventionalcommits.org/en/v1.0.0/
- OpenSSF Best Practices: https://www.bestpractices.dev/

## 14. 可直接复制给 AI 的启动指令

```text
你正在接手一个新仓库。你的第一目标不是直接改业务，而是为仓库建立可持续的 AI 工作流程和标准。

请严格按以下顺序执行：
1. 建立 docs/PROJECT_PROFILE.md，只写高置信度事实，未知写 TBD。
2. 基于项目画像生成根目录 AGENTS.md，明确读文件顺序、先复用后新增、验证和文档同步规则。
   并明确“适用规则”与开发前 / 开发中 / PR 前的规则生命周期。
3. 选择一个且仅一个当前执行入口：docs/roadmap.md 或 docs/plans/current-execution-control.md。
4. 建立 docs/ARCHITECTURE_GUARDRAILS.md，定义层次、owner 和禁止事项。
5. 为 1 到 3 个关键模块建立模块文档。
6. 建立工程治理门禁，包括 commit policy、hooks、CI governance、document lifecycle 和 release checklist。
   若提供 PR 模板或本地 hook，确保它们不是空壳，相关脚本与校验入口也一并落地。
7. 建立 docs/plans 与 docs/adr 的最小入口，并在后续任务中持续维护。

在任何非平凡改动前，先输出：
目标模块、现有 owner、影响面、适用规则、计划改动、验证方式、需要同步的文档。

禁止：
- 编造事实
- 并行维护多个当前入口
- 不经搜索直接新增 shared helper
- 擅自添加 Co-Authored-By 或其他协作元信息
- 完成后不做验证和文档同步
```
