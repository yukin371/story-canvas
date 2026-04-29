# Configuration

此文档用于指导 AI 在本仓库中的工作方式。若与更高优先级系统或维护者指令冲突，以更高优先级为准。

## 项目概览

Story Canvas — Agent-native 故事与视觉工作流工具，Python 3.10+，零外部依赖，使用 argparse + JSON-compatible YAML 文件协议，并开始提供早期单页 UI。当前处于早期功能积累阶段。

## 工作原则

1. 修改前先阅读当前执行入口、项目画像、架构护栏和目标模块文档。
2. 不编造事实；未确认项写 `TBD` 并附确认路径。
3. 新增 shared helper / utility / service / adapter 前，必须先搜索现有实现。
4. 非平凡改动前，先输出边界摘要与验证方案。
5. 若任务跨模块或存在风险，先创建 `docs/plans/YYYY-MM-DD-*.md`。
6. 仓库只能维护一个当前执行真相入口，禁止并列维护多个"当前计划"。
7. 修改模块前必须先读该模块文档；没有就先补文档。
8. 完成任务后必须同步文档，并输出验证结果与残留风险。
9. 禁止擅自添加 `Co-Authored-By`、`Pair-Programmed-By`、AI 工具签名或类似协作元信息。
10. 禁止擅自修改协作者、owner、branch protection、ruleset 等仓库设置类配置，除非维护者明确要求。
11. 仓库级规则优先于抽象工程口号；`clean code`、`SOLID` 只能作为辅助观察角度，不能单独构成改动理由。
12. 非平凡改动前必须整理“适用规则”清单，明确本次工作实际受哪些入口、owner、不变量、兼容性和验证约束影响。
13. 提交前或 PR 前必须按“适用规则”回审，不允许只给出泛化风格评价而不落到具体规则。
14. 若任务属于真实实施、流程验证或 agent/workflow/review/tooling 改进，开发前后都必须检查并回写 `docs/tracking/ai-friction-tracker.md`。

## 修改前必读顺序

1. `AGENTS.md`
2. 当前执行入口: `docs/roadmap.md`
3. `docs/PROJECT_PROFILE.md`
4. `docs/ARCHITECTURE_GUARDRAILS.md`
5. 目标模块下的 `MODULE.md`
6. 必要时再读相关 `plan` / `ADR`

## 规则生命周期

### 1. 开发前

- 先整理本次改动的“适用规则”，至少覆盖：
  - 当前执行入口
  - 架构护栏 / canonical owner
  - 目标模块 `MODULE.md` 中的不变量
  - 已知兼容性约束（CLI 参数、输出结构、schema、文件协议）
  - 必要时补充 ADR、plan、测试基线
- 若任务涉及真实流程实跑、agent 协同、workflow/review/export/entity/status 等工具链，还要检查 `docs/tracking/ai-friction-tracker.md` 的 active 条目，并标出本轮适用的痛点编号。
- 如果规则缺失，不得用抽象原则代替，必须写 `TBD` 并给出确认路径。

### 2. 开发中

- 实现必须优先服从已确认的 rule source、owner 和不变量，而不是先写再回头解释。
- 遇到规则例外时，要么在本轮同步文档，要么停下确认；禁止默默引入并行真相源、并行规则定义或 undocumented exception。
- 如果发现“想改是因为不够 clean / 不够 SOLID”，必须先把问题翻译成具体风险：重复实现、边界泄漏、兼容性破坏、测试困难、认知负担过高等。
- 若本轮缓解或暴露了新的 AI 实施痛点，必须同步更新 `docs/tracking/ai-friction-tracker.md`，而不是只写进临时 plan。

### 3. PR 前 / 自审时

- 必须按“适用规则”逐条回审：
  - 有没有越过 canonical owner 或依赖方向
  - 有没有引入 breaking change 或 undocumented behavior change
  - 有没有新增重复规则、平行配置、平行真相源
  - 测试和文档是否与改动同步
- 评审结论必须引用具体规则或风险，不使用“这不够 clean code / 不够 SOLID”作为直接结论。

## 关键项目约定

- **零外部依赖**: 所有代码仅使用 Python stdlib，不引入第三方包
- **JSON-compatible YAML**: 所有 `.yaml` 文件内容必须为合法 JSON（不用 YAML 特有特性）
- **命令注册**: 新命令必须在 `commands/__init__.py` 导出 + `cli.py` 的 `build_parser()` 中注册
- **服务层无副作用**: `services/` 中的函数只接受 state dict 并返回结果 dict，文件 I/O 由 commands 层负责
- **测试模式**: unittest + tempfile fixture，通过 `cli.main()` 直接调用

## 非平凡改动前必须输出

```text
目标模块：
现有 owner：
影响面：
适用规则：
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

## 必须停下并询问的情况

- 当前执行入口不明确
- 需要在两个模块之间新增共享 owner
- 需要引入 breaking change（CLI 参数、输出格式、数据模型变化）
- 需要改动 secrets、权限、安全边界
- 发现仓库已有未解释的大量脏改动
- 现有文档与代码状态严重冲突，无法推断真实状态
- 适用规则之间存在冲突，无法判断哪条应优先
- 需要引入第三方依赖

## 完成后必须输出

```text
已完成改动：
验证结果：
未验证区域：
同步文档：
残留风险：
```
