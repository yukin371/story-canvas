# 2026-04-28 插画结果导出与默认路径分组计划

## 背景

- 当前插画工作台右侧结果区虽然可以回退显示最近历史图，但没有明确的“最近生成结果”导出动作，导出主图或批量变体仍需要手动翻历史或找文件。
- 当前默认资产路径只按 `chapter / entity / temporary` 三类 target type 分流；当同一章节或角色生成多类用途图片（如 `chapter-scene`、`cover-poster`、`character-sheet`）时，目录聚合粒度偏粗，不利于回看与导出。

## 本轮目标

1. 让插画工作台右侧结果区自动聚焦最近可用生成结果，并提供直接导出入口。
2. 增强默认图片落盘路径分组，在 target type 之下按 `useCase` 继续分类。
3. 保持 CLI / 本地 UI API / 协议历史复用同一套落盘与记录逻辑，不引入平行实现。

## 影响面

- `ui/src/views/WorkbenchView.vue`
- `ui/src/components/workbench/IllustrationWorkbenchPane.vue`
- `src/story_harness_cli/commands/illustration.py`
- `docs/protocol/image-prompt-system.md`
- `tests/smoke/test_illustration_command.py`

## 适用规则

- 当前执行入口：`docs/roadmap.md`
- UI 不是新的真相源；只能消费已有协议与本地 API 输出
- 本地 UI API 的 `/api/illustration/generate` 必须继续复用命令层真实逻辑
- `illustrations.yaml` 保存配置与历史，图片二进制仍落在 `assets/illustrations/` 或工作台缓存目录
- 命令层负责文件 I/O，服务层保持无副作用

## 计划改动

1. 在工作台结果区暴露当前预览记录的主图/变体导出链接，并补“最近生成”显式状态。
2. 在工作台状态同步中优先保持当前选中记录；无选中时自动回退到最近历史记录。
3. 调整默认输出路径：
   - `chapter` -> `assets/illustrations/chapters/<chapter-id>/<use-case>/`
   - `entity` -> `assets/illustrations/entities/<entity-id>/<use-case>/`
   - `temporary` -> `tmp/illustrations/staging/<temp-label>/<use-case>/`
4. 同步协议文档中的路径说明，并补 smoke test 覆盖默认分组路径。

## 验证

- `PYTHONPATH=src python -m unittest tests.smoke.test_illustration_command`
- `npm run build` in `ui/`

## 风险

- 路径分组变化只影响新生成资产；旧历史路径不迁移，需要保持旧记录可继续预览。
- 工作台右侧结果区新增导出动作后，需要避免对未绑定项目的工作台缓存路径做错误 root 拼接。

## 回滚路径

- UI 改动可独立回退结果区展示与导出按钮。
- 路径分组逻辑可单独回退到 target type 一级目录。