# Story Canvas 架构护栏

> 最后更新: 2026-04-27
> 定位: 仓库级长期边界约束
> 当前阶段依据: `docs/roadmap.md`

> 命名说明: 对外产品名与主入口已收敛到 `Story Canvas` / `story-canvas` / `story_canvas`；`story-harness` 与 `story_harness_cli` 仅作为兼容别名保留，当前内部实现 owner 仍在 `src/story_harness_cli/`

## 1. 目的

本文件只回答三件事:

1. 关键层次怎么分
2. 共享能力归谁 owner
3. 哪些重复实现和依赖方向是禁止的

## 2. 当前层次划分

### 2.1 入口层

- 对外入口: `src/story_canvas/`
- 内部入口 owner: `src/story_harness_cli/cli.py`, `src/story_harness_cli/main.py`

职责:

- 维持 `story-canvas` / `python -m story_canvas` 的公共入口
- argparse 解析与子命令注册
- 路由到 command 函数
- stdout/stderr 编码处理

不应承担:

- 业务逻辑
- 文件 I/O（委托 protocol 层）
- 对 `src/story_harness_cli/` 之外的实现分叉

### 2.2 命令层

- `src/story_harness_cli/commands/`

职责:

- 解析 args，调用 protocol 加载状态
- 调用 service 执行业务逻辑
- 保存状态，输出 JSON 结果
- 文件 I/O（读写 YAML、章节文件）

不应承担:

- 纯计算逻辑（委托 service 层）
- 状态管理的隐式规则（委托 protocol 层）

### 2.3 服务层

- `src/story_harness_cli/services/`

职责:

- 纯业务逻辑：分析、投影、一致性校验、统计、灵感生成
- 接受 state dict，返回结果 dict
- 无副作用

不应承担:

- 文件 I/O
- argparse 参数处理
- JSON 输出格式化

### 2.4 协议层

- `src/story_harness_cli/protocol/`

职责:

- 定义文件路径约定（ROOT_FILES）
- 加载/保存项目状态（load_project_state / save_state）
- Schema 默认值（default_project_state）
- 大纲同步（_sync_outline）

不应承担:

- 业务逻辑判断

### 2.5 工具与数据层

- `src/story_harness_cli/utils/`, `src/story_harness_cli/data/`

职责:

- 文本处理工具（段落拆分、标签提取、关键词匹配）
- 哈希与时间工具
- 创作数据表（角色原型、世界元素、姓名库）

不应承担:

- 业务逻辑
- 状态管理

### 2.6 Provider 层

- `src/story_harness_cli/providers/`

职责:

- 封装外部 API、SDK 和 optional dependency
- 返回标准化 provider 结果，供 commands / services 使用
- 隔离鉴权、网络调用和 provider 特定错误

不应承担:

- 项目状态持久化
- CLI 参数解析
- 核心业务规则判定

## 3. Canonical Owners

| 关注点 | Canonical owner | 说明 |
|------|------|------|
| 文件路径约定 | `protocol/files.py` | ROOT_FILES, chapter_path, root_file |
| 状态加载/保存 | `protocol/__init__.py` | load_project_state, save_state |
| Schema 默认值 | `protocol/schema.py` | default_project_state |
| 章节分析 | `services/analyzer.py` | 实体识别、状态检测、关系检测 |
| 投影管理 | `services/projection_engine.py` | upsert_by_key, apply_projection |
| 一致性校验 | `services/consistency_engine.py` | hard/soft checks |
| 规则元数据定义 | `services/rule_registry.py` | builtin rule registry / canonical rule metadata |
| 规则 judgement 组装 | `services/rule_semantics.py` | build_rule_judgement, scope refs |
| 文本处理 | `utils/text.py` | strip_entity_tags, extract_tag_mentions 等 |
| 外部 provider 接入 | `providers/` | API/SDK 封装、optional dependency 包装 |
| 命令注册 | `commands/__init__.py` + `cli.py` | 所有子命令注册入口 |

## 4. 允许的依赖方向

1. `commands/` → `protocol/`, `services/`, `utils/`
2. `commands/` → `providers/`
3. `services/` → `utils/`（仅文本工具和数据表）
4. `protocol/` → `utils/`（仅 hashing）
5. `providers/` → `utils/`, `data/`（仅 provider 辅助工具和 builtin pack）
6. `cli.py` → `commands/__init__.py`
7. `main.py` → `cli.py`

## 5. 明确禁止事项

- 禁止 `services/` 直接读写文件（文件 I/O 由 commands 层负责）
- 禁止 `protocol/` 包含业务逻辑
- 禁止在 `commands/` 之外注册 CLI 子命令
- 禁止两个模块并行维护相同共享能力
- 禁止把第三方依赖设为 base install 的必需项
- 禁止在 `services/` 和 `protocol/` 中直接调用外部 API 或耦合特定 provider SDK
- 禁止缺失 optional dependency 时让核心 CLI 闭环直接失败
- 禁止使用 YAML 特有特性（所有 `.yaml` 必须为合法 JSON）

## 5.1 依赖策略

- 仓库采用 `base + extras + packs` 模式:
  - `base`: stdlib-only，必须覆盖核心 CLI 与离线测试
  - `extras`: 可选第三方依赖，只能增强，不能变成硬前置
  - `packs`: 词表、字典、prompt、review profile 等可替换资源包，缺失时必须回退 builtin 最小集
- 具体口径见 `docs/adr/ADR-002-optional-dependencies-and-providers.md`

## 6. 非平凡改动前必须回答的问题

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
```

## 7. 文档同步触发条件

- 模块职责变化
- 共享能力 owner 变化
- 目录边界变化
- 注册方式变化（新命令/新 service）
- 依赖方向变化
