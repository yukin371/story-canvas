# 2026-05-03 项目收口与实验命令稳定化设计

## 背景

当前路线图的 `v1.0` 收口目标强调协议稳定、workflow 闭环可验证、样例矩阵可回归。仓库当前已有一批实验命令进入 `commands/__init__.py` 与 `cli.py` 主注册链，虽然 `story_canvas --help`、`compileall` 和全量 unittest 当前通过，但仍存在几个会误导真实使用的断点：

- `setting` 命令已经注册，但 `setting template --list` 因 `genre_templates.yaml` 不是 JSON-compatible YAML 而返回空模板列表。
- `setting assess/expand/validate` 没有 `--root`，会默认读取当前工作目录，不符合现有 CLI 项目根约定。
- `services/setting_expansion.py` 直接读取模板文件，越过 service 无副作用边界。
- `writing.py` 存在重复函数定义，且 `entity-only` / `mention-only` 辅助类型口径不一致。
- `docs/plans/2026-04-30-implementation-archive.md` 把功能标为已完成但测试列为待测试，并含 AI 工具署名，和仓库规则冲突。

本轮先收口“已进入主 CLI 的实验能力不能误导使用者”这一层，不扩展新大能力。

## 目标模块

- `src/story_harness_cli/commands/`
- `src/story_harness_cli/services/`
- `src/story_harness_cli/data/`
- `tests/smoke/`
- `docs/`

## 现有 owner

- `commands/`: argparse、root 参数、项目状态读取/写入、章节文件 I/O、JSON 输出。
- `services/`: 纯业务逻辑，只接受 state / 已解析输入并返回 dict，不读取文件。
- `data/`: 内置创作数据表；若使用 `.yaml` 后缀，内容必须仍为合法 JSON。
- `docs/tracking/ai-friction-tracker.md`: 长期 AI 实施痛点入口。

## 影响面

- `story-canvas setting template|assess|expand|validate|check`
- `story-canvas writing assist|mention-check|relation-track`
- CLI 主注册链的导入稳定性
- README / plan 对“已完成”的陈述可信度

## 适用规则

- 当前执行入口：`docs/roadmap.md`，优先服务 `v1.0` 的 workflow 闭环、样例回归和文档口径收敛。
- 架构护栏：`commands/` 负责 I/O 与注册；`services/` 不读写文件；禁止在多个模块并行维护同一共享能力。
- 文件协议：所有 `.yaml` 文件必须为合法 JSON。
- 兼容性：新增命令已暴露在主 CLI，修复应优先保持命令名不变；新增 `--root` 属于补齐现有 CLI 约定。
- AIF：本轮直接关联 `AIF-017`；同时避免扩大 `AIF-014` 的第三方依赖风险。`AIF-015` / `AIF-016` 本轮只列为后续优先项。

## 计划改动

1. 将 `src/story_harness_cli/data/genre_templates.yaml` 迁入 builtin Python 数据表 `src/story_harness_cli/data/genre_templates.py`，移除非 JSON-compatible YAML 文件。
2. 服务层只消费传入或 builtin 的模板 dict，不再读取文件。
3. 给 `setting assess/expand/validate/check` 增加 `--root`，并用 `load_state(root)` / `save_state(state, root)`。
4. 将 `setting expand` 收敛为稳定的 prompt / draft 入口；不再调用不存在的 `services.ai_provider`。
5. 清理 `commands/writing.py` 重复函数定义，统一 `entity-only` 为 `mention-only` 的兼容别名，输出结构化 JSON。
6. 增加聚焦 smoke tests 覆盖上述命令。
7. 同步模块文档，清理明显冲突的文档口径和 AI 署名。

## 验证方式

- `PYTHONPATH=src python -m story_canvas setting template --list`
- `PYTHONPATH=src python -m story_canvas setting assess --root <fixture> --format json`
- `PYTHONPATH=src python -m story_canvas writing assist --help`
- `PYTHONPATH=src python -m unittest tests.smoke.test_setting_command tests.smoke.test_writing_command`
- `python -m compileall -q src`
- `PYTHONPATH=src python -m unittest discover -s tests`

## 非目标

- 本轮不正式实现新的 provider-backed 设定扩展生成。
- 本轮不处理 `stats/doctor` 字数目标分叉和 `scene-detect --replace` 降粒度问题，只保留为后续 P0/P1。
- 本轮不引入第三方依赖或向量数据库。

## 回滚路径

- 若实验命令仍不稳定，可从 `commands/__init__.py` 与 `cli.py` 暂时移除 `setting` / `writing` / `review-comprehensive` 注册，保留文件但不暴露到主 CLI。
- builtin `genre_templates.py` 可直接通过 git diff 回退，不涉及项目状态迁移。
