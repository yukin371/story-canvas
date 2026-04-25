# Commands 模块说明

> 最后更新: 2026-04-25
> 状态: 当前有效模块文档

## 1. 模块职责

- 定义所有 CLI 子命令的参数解析和处理逻辑
- 每个命令一个文件，通过 `register_xxx_commands(subparsers)` 注册
- 命令函数 `command_xxx_action(args) -> int` 负责串联 protocol → service → output

## 2. Owns

- argparse 子命令注册（`__init__.py` 导出 + `cli.py` 注册）
- 命令参数定义（--root, --chapter-id, --output 等）
- JSON 输出格式化（`print(json.dumps(...))`）
- 文件 I/O 时机控制（何时 save_state）
- workflow 命令编排（如 `review apply`、`review chapter`、`review scene` 的不同评审路径，以及 `review scene --list-scenes` 的场景枚举）
- `projection apply` 的 command-side 编排：加载 analysis、读取章节正文并补跑设定一致性抽取，把非冲突高置信新设定交给 service 入账
- `outline scene-add` / `outline scene-list` / `outline scene-detect` / `outline scene-update` / `outline scene-remove` 这类轻量结构维护命令
- `outline check` 这类“写作前门禁”命令，以及 `chapter suggest` 的 outline-first workflow gate
  默认门禁口径为 `project.positioning` / `project.storyContract` + chapter `direction` + `beats` + `scenePlans`
- 项目初始化参数装配（如 `init` 写入 positioning / storyContract / emotionalContract / storyTemplate / commercialPositioning，并落盘 `worldbook` / `foreshadowing` 默认文件）
- `context refresh` 的 command-side 编排：加载 analysis 日志，刷新并持久化包含情绪契约、题材模板、世界约束、线索和伏笔切片的写作上下文
- doctor 类命令中的项目元数据校验编排
- doctor 现在还负责校验可选项目配置如 `style-profiles.yaml` 的基本结构，以及 `storyTemplate` 驱动的 `worldbook` / 伏笔账本 / 角色状态追踪基础约束
- doctor 现在还会扫描全项目章节中的 `@{实体}` 包裹引用，并检查是否已在 `entities/worldbook` 中建档
- doctor 现在还会校验 `illustrations.yaml` 中的主图/多图资产引用、缺失文件和孤儿资产
- `style check` / `style constraints` / `style report` / `style repair` 这组风格治理命令，以及 optional scorer 的 command-side 装配
- `style check` / `style constraints` / `style report` / `style repair` 这组风格治理命令，以及 `style-profiles.yaml` 中 pattern / 术语词典 / 白名单 / 题材语域词表的 command-side 装配；未显式传 `--profile` 时会按项目定位自动选 profile
- `style check` / `consistency check` / `review chapter` / `review scene` 现已开始对外暴露统一规则 judgement 结果，作为后续统一规则引擎协议的 Phase 1 兼容输出
- `illustration prompt` / `illustration generate` / `illustration list` / `illustration config` 这组插图命令，负责编排 prompt 构造、文生图/图生图 provider 请求与 `illustrations.yaml` 配置读写
- `workflow status` / `workflow run` / `workflow advance` / `workflow reset` / `workflow export` 这组 workflow 状态机入口，负责把 protocol + service 的推断结果、gate 决策和快照导出编排到 `workflow.yaml`
- `doctor` 与 `workflow` 现也开始对外暴露统一规则语义：`doctor.judgements`、workflow gate 下的 `ruleJudgements/gateDecision`，用于把结构校验和流程门禁逐步收口到同一规则协议

## 3. Must Not Own

- 纯计算逻辑（委托 services/）
- 状态管理规则（委托 protocol/）
- 文本处理算法（委托 utils/）

## 4. 关键入口

- `commands/__init__.py`: 所有 `register_*_commands` 的导出汇总
- `cli.py`: `build_parser()` 构建完整 argparse 树
- 每个子模块: `register_xxx_commands` + `command_xxx_*` 函数

## 5. 关键依赖

- 依赖 `protocol/`: `ensure_project_root`, `load_project_state`, `save_state`
- 依赖 `services/`: 各业务逻辑服务
- 依赖 `utils/`: `now_iso`, `stable_hash`, 文本工具

## 6. 不变量

- 每个命令函数必须 `return 0` 表示成功
- 致命错误必须 `raise SystemExit("中文消息")`
- 输出统一使用 `print(json.dumps(result, ensure_ascii=False, indent=2))`
- 在兼容旧字段的前提下，新增输出字段应优先挂在统一语义层（如 `judgements`、`ruleJudgements`），而不是继续为每个命令单独发明平行结构
- 新命令必须在 `__init__.py` 和 `cli.py` 双重注册

## 7. 常见坑

- 忘记在 `cli.py` 的 `build_parser()` 中调用 `register_xxx_commands(subparsers)` 会导致命令不可见
- `argparse` 的 `dest` 参数和 `--entity-id` 的 kebab-case 需要显式 `dest="entity_id"`
- `review scene` 的段落范围是 1-based 且基于“去掉标题后的正文段落”计数，和 markdown 原始行号不是一回事
- `review scene --scene-index` 在没有 `scenePlans` 时会回退到启发式候选场景
- 一旦章节里存在显式 `scenePlans`，`review scene --scene-index` 会优先使用显式边界，而不是启发式切分
- `outline scene-update` 更新段落范围时，必须同时提供 `--start-paragraph` 和 `--end-paragraph`
- `outline scene-detect` 默认不会覆盖已有 `scenePlans`，需要显式传入 `--replace`
- `chapter suggest` 默认要求目标章节先通过 `outline check`，旧项目如需跳过必须显式传 `--allow-without-outline`
- `outline check` 默认是严格模式；只有显式传入 `--allow-missing-project-gate`、`--allow-missing-beats`、`--allow-missing-scene-plans` 才会放宽
- `workflow advance` 只能对当前 gate 执行；如果要回到更早 gate，必须先 `workflow run --resume-from <stage>` 或 `workflow reset --from-gate <stage>`
- `workflow status` 会把持久化的 `workflow.yaml` 与当前推断结果合并展示，因此 `currentStage` 可能早于 `inferredCurrentStage`
- `illustration generate --dry-run` 不会写 `illustrations.yaml`；只有真实生成成功后才会落记录
- `illustration generate --mode image-to-image` 至少需要一张 `--input-image`
- `illustration generate --mode image-to-image --mask <path>` 会把 mask 一并上传给 provider，mask 仅作用于第一张输入图
- `illustration generate` 真实执行时会把返回图批量写入 `assets/illustrations/`；`filePath` 仍指向主图，额外结果写入 `artifacts[]`
- `illustration list` 会补充资产存在性、数量、主图标记，以及 chapter/entity/input-image/mask 的引用状态
- `doctor` 会基于 `illustrations.yaml` 检查缺失资产、主图路径不一致、失效 target/input/mask 引用和 `assets/illustrations/` 下的孤儿文件

## 8. 测试方式

- 单元测试: 各 `tests/smoke/test_xxx_command.py`
- 调用方式: `from story_harness_cli.cli import main; main(["command", "subcommand", ...])`
- 输出捕获: `contextlib.redirect_stdout(StringIO())`

## 9. 文档同步触发条件

- 新增/删除命令
- 命令参数变化（breaking change）
- 输出格式变化
- workflow 文件读写路径变化
- 注册方式变化
