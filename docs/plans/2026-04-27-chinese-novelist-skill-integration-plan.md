# Chinese Novelist Skill 融入计划

> 日期: 2026-04-27
> 状态: 草稿
> 关联当前入口: `docs/roadmap.md`
> 范围: `adapters/`、适配器安装脚本、相关文档

## 1. 背景

外部仓库 `E:\Github\chinese-novelist-skill` 提供了一套更偏“中文小说怎么写”的 skill：

- 三层递进式问答
- 规划 -> 写作 -> 自动校验流程
- 章节钩子、长篇写法、去 AI 味等写作提示

当前仓库已有的 `adapters/codex-skill/story-harness-writing` / `adapters/claude-code/story-harness-writing` 更偏：

- 如何调用 `story-harness` CLI
- 哪些协议文件重要
- 章节分析 / review / projection / context 的命令链

两者并不完全兼容：

- 外部 skill 假设自己管理项目目录和 JSON 状态
- 当前仓库要求以 `story-harness` CLI 和协议文件为真相源
- 当前仓库还要求 `skill` 保持“薄”，不要与真实 CLI 能力口径冲突

因此不能直接复制，需要做“写法指导 + CLI 工具路由”的融合。

## 2. 目标

1. 把外部 `chinese-novelist-skill` 的高价值写作指导融入当前项目。
2. 保持现有 adapter 的薄边界：skill 负责告诉 AI 怎么写、怎么用工具；执行仍走 CLI。
3. 不让 skill 和仓库实际 workflow / 协议真相源发生分叉。
4. 让项目形成“外部 agent + CLI 工具 + skills”的闭包。

## 3. 非目标

- 不把外部 skill 的整套目录原样照搬进仓库。
- 不保留与当前仓库冲突的 JSON 项目状态和独立项目管理方式。
- 不在本轮引入第二套并行 canonical workflow。
- 不要求一次完成所有宿主的深度定制。

## 4. 设计结论

### 4.1 保留现有 skill 名称与入口

建议继续以：

- `adapters/codex-skill/story-harness-writing`
- `adapters/claude-code/story-harness-writing`

作为主适配 skill 源。

原因：

- 安装脚本已默认围绕 `story-harness-writing`
- 宿主侧已有入口，不必多维护一个并行 skill 名称
- 更符合“仓库 skill 是 CLI 的薄适配层”这一不变量

### 4.2 融合方式

把外部 skill 拆成两部分融入：

1. **保留的部分**
   - 中文小说写法规则
   - 阶段化写作流程
   - 钩子、对白、章节展开等写作参考
2. **替换的部分**
   - 外部 skill 自己的项目目录约定
   - 独立 JSON 协调状态
   - 与仓库 CLI 冲突的阶段命令

### 4.3 最终形态

现有 `story-harness-writing` skill 变成：

- 既告诉 AI “怎么写”
- 也告诉 AI “该用哪些 `story-harness` 命令”
- 并明确哪些动作必须依赖 repo-native CLI，而不是直接改协议文件

## 5. 需要落地的改动

### 5.1 adapters/codex-skill/story-harness-writing

- 重写或增强 `SKILL.md`
  - 增加中文小说写作阶段说明
  - 增加“要怎么写 / 不要怎么写”规则
  - 增加与当前仓库兼容的工作流
- 新增或扩充 `references/`
  - `flows/`
  - `guides/`

### 5.2 adapters/claude-code/story-harness-writing

- 保持与 codex 版本基本同构
- 根据宿主语气做轻微调整

### 5.3 adapters/README.md

- 说明 skill 已从“纯工具路由”升级为“写法指导 + CLI 路由”的闭包适配
- 说明仍以 CLI 为执行真相源

### 5.4 安装脚本

原则上可不改 skill 名称与默认参数。

仅当目录结构变化影响安装时，才修改：

- `scripts/install_adapter.py`
- `scripts/install_adapters.py`

## 6. 兼容性约束

融合后的 skill 必须明确：

1. 章节正文可自由编辑
2. `yaml` 协议文件优先通过 CLI 命令维护
3. 不再沿用外部 skill 的独立 JSON 状态协调方式
4. 写作流程必须服从当前仓库的：
   - `project.yaml`
   - `outline`
   - `entities`
   - `foreshadowing`
   - `workflow`
   - `review / projection / context`

## 7. 推荐信息架构

### SKILL.md 负责

- 何时使用 skill
- 总体写作原则
- 总体 workflow
- 核心命令路由
- 停止条件

### references/flows/* 负责

- 分阶段写作流程
- 与当前 CLI 对齐的阶段动作

### references/guides/* 负责

- 章节写法
- 人物写法
- 钩子写法
- 去 AI 味
- 结构模板

## 8. 验收标准

- skill 安装后仍使用同一入口名称
- skill 明确告诉 AI：
  - 怎么写中文小说
  - 怎么使用 `story-harness` CLI
  - 哪些事不要直接改 YAML
- skill 文案与仓库真实 workflow 不冲突
- codex / claude 两份适配都保持同构，不出现两套流程口径

## 9. 当前建议执行顺序

1. 先增强 codex skill
2. 再同步 claude skill
3. 再同步 adapters README
4. 最后检查安装脚本是否需要补充说明
