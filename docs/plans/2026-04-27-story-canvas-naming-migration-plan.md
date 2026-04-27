# Story Canvas 命名迁移计划

> 创建日期: 2026-04-27
> 状态: 进行中
> 关联当前入口: `docs/roadmap.md`

## 一、背景

产品名已经收敛为 `Story Canvas`，并且仓库已不再只是单纯 CLI。当前仍保留 `story-harness` CLI 命令和 `story_harness_cli` 包名，会持续向外暴露过时心智，和现有 UI、生图工作台、未来在线工具方向不一致。

## 二、目标

1. 把主产品名、主 CLI 命令和主 Python 包入口统一迁移到 `Story Canvas` / `story-canvas` / `story_canvas`
2. 保留旧入口作为兼容壳，避免一次性打断现有调用链
3. 让当前执行入口、README 和项目画像口径一致

## 三、非目标

- 不在本轮强制搬迁全部内部源码目录
- 不在本轮清洗所有历史计划文档、适配器说明和样例文本
- 不在本轮移除 `story-harness` / `story_harness_cli` 兼容入口

## 四、范围

### 4.1 In Scope

- `pyproject.toml` 的主脚本入口
- 新主包 `src/story_canvas/`
- README / 项目画像 / 路线图 / UI README 的主命名口径
- 保留兼容入口的策略说明

### 4.2 Out of Scope

- 历史文档全量替换
- 宿主 adapter 的完整改名
- 仓库物理目录重命名

## 五、实施策略

### Phase A

- 新增 `story_canvas` 主包与 `python -m story_canvas`
- 新增 `story-canvas` 主 CLI
- 保留 `story-harness` 作为兼容命令

### Phase B

- 把 README、路线图、项目画像改成以 `story-canvas` / `story_canvas` 为主
- 明确旧入口为 compatibility alias

### Phase C

- 后续再决定是否把内部源码目录从 `story_harness_cli` 整体搬到 `story_canvas`
- 若执行该阶段，需要单独处理导入路径、测试和 adapter 迁移

## 六、验收标准

- `pip install -e .` 后可使用 `story-canvas`
- `python -m story_canvas --help` 可用
- 旧入口 `story-harness` 和 `python -m story_harness_cli` 仍可用
- 当前主文档不再把项目描述成“仍以 story-harness CLI 为主入口”

## 七、风险

- 双入口并存期间，文档与用户口径容易混用
- 若过早搬迁内部源码目录，会卷入过多导入与测试改动

## 八、回滚路径

- 若新主包方案不稳定，可先回滚到旧入口，同时保留本计划文档
