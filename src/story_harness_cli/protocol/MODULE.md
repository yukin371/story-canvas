# Protocol 模块说明

> 最后更新: 2026-04-25
> 状态: 当前有效模块文档

## 1. 模块职责

- 定义项目文件结构约定（哪些文件必须存在、路径规则）
- 加载和保存项目状态（所有 YAML 文件的统一读写）
- 保存前的状态快照校验与根目录级写回互斥
- 提供默认 schema
- 大纲同步（volumes ↔ flat chapters）

## 2. Owns

- `ROOT_FILES` 常量：必须存在的根目录文件列表
- `load_project_state(root)`: 将所有 YAML 文件加载为统一 state dict
- `save_state(root, state)`: 将 state dict 写回各 YAML 文件
- 项目状态指纹：`load_project_state` 记录、`save_state` 校验，防止旧快照覆盖新状态
- `default_project_state()`: 返回所有 key 的空默认值
- `project.yaml` 默认结构：包含 `positioning`、`storyContract` 与 `commercialPositioning`
- `reviews/story-reviews.yaml`: 章节/一幕评审报告状态文件
- `workflow.yaml`: workflow 状态机进度文件（可缺省，缺失时回退 schema 默认值；持久化 `currentStage`、`workflowStatus`、`gateHistory`、`stageResults` 等决策快照）
- `illustrations.yaml`: 插图配置与生成记录文件（可缺省，缺失时回退 schema 默认值）
- `_sync_outline()`: volumes → flat chapters 自动同步

## 3. Must Not Own

- 业务逻辑（分析、投影、一致性等）
- 文件路径之外的项目约定

## 4. 关键入口

- `protocol/__init__.py`: `ensure_project_root`, `load_project_state`, `save_state`
- `protocol/files.py`: `ROOT_FILES`, `chapter_path`, `root_file`
- `protocol/io.py`: `dump_json_compatible_yaml`, `load_json_compatible_yaml`
- `protocol/style_profiles.py`: style profile 的 builtin 默认值、项目级覆盖与自动选择
- `protocol/schema.py`: `default_project_state`
- `protocol/state.py`: `_sync_outline`, re-exports

## 5. 关键依赖

- 依赖 `utils/hashing.py`: 仅 `state.py` 中的指纹生成

## 6. 不变量

- `save_state` 开头始终调用 `_sync_outline`，保证 volumes 和 flat chapters 一致
- `save_state` 写回前必须校验载入时状态指纹，发现外部更新时拒绝覆盖
- `save_state` 写回阶段必须持有项目根目录级别锁，避免多命令同时写同一项目
- 所有 YAML 文件内容必须为合法 JSON
- `load_project_state` 对缺失文件使用 schema 默认值填充
- `load_project_state` 会为旧版 `project.yaml` 回填缺失的定位/契约/商业蓝图字段
- `load_project_state` 会为旧版 `story-reviews.yaml` 回填缺失的 `sceneRubricVersion` / `sceneReviews`
- `load_project_state` 会为缺失的 `workflow.yaml` 回填完整 `workflow_progress` 默认结构
- `load_project_state` 会为缺失的 `illustrations.yaml` 回填完整 `illustrations` 默认结构
- `chapter_path` 的 fallback glob 查找只在 `chapters/` 目录内
- `style-profiles.yaml` 是可选配置文件，缺失时必须回退 builtin profile

## 7. 常见坑

- `_sync_outline` 会覆盖 `outline["chapters"]` 和 `outline["chapterDirections"]`，不要手动维护这两个字段
- 多个会写状态的命令不能依赖“先 load 再晚点 save”而假设项目没变；一旦状态指纹不一致，必须重跑命令
- Windows 下路径需要用 `Path.resolve()` 避免反斜杠问题
- `workflow.yaml` 保存的是“推断结果 + 决策元数据”的组合快照，不能把 gate 是否完成仅理解为人工决策结果
- `illustrations.yaml` 当前保存的是配置、主图路径和资产元数据摘要，不等于图片二进制资产本身；图片文件仍存放在 `assets/illustrations/`

## 8. 测试方式

- 单元测试: `tests/smoke/test_schema.py` 验证 schema 默认值
- 集成测试: 几乎所有测试都通过 `load_project_state` 间接测试

## 9. 文档同步触发条件

- 新增或删除 ROOT_FILES 中的文件
- 新增或删除项目级可选配置文件加载规则（如 `keywords.yaml`、`style-profiles.yaml`）
- 新增或删除 workflow 状态文件（如 `reviews/story-reviews.yaml`）
- `_sync_outline` 逻辑变化
- 状态锁或状态指纹校验逻辑变化
- `default_project_state` 结构变化
- 文件路径约定变化
