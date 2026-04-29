# 2026-04-29 Writing Skill Style Rendering

## 1. 背景

- 用户反馈：语料解析进入 writing skill 后仍不够精确，输出容易像机械命令执行。
- 范围：只处理 writing skill / adapter reference / 长期痛点记录，不改 CLI、协议、review 规则或项目正文。
- 约束：adapter 保持薄层；CLI 和协议文件仍是项目事实源；skill 只提供写法解释和执行方法。

## 2. 适用规则

1. 当前执行入口：`docs/roadmap.md`
2. 模块 owner：`adapters/MODULE.md`
3. 架构护栏：adapter 不引入并行状态源，不替代 CLI gate
4. 兼容性：不改 CLI 参数、输出结构、schema 或文件协议
5. 长期痛点：新增 `AIF-013` 记录语料 overlay 过度抽象导致写作机械化

## 3. 设计判断

当前问题不是缺少更多题材 checklist，而是缺少一层转换：

1. 从语料中抽出叙述距离、行文速度、句子质地、对白压力、意象库、禁用语域。
2. 起稿时把这些信号转成 scene action、conflict、consequence、voice、residue。
3. 修稿时把检测器或 review 规则转换成角色动作、物件残留、关系边界和后果。
4. 禁止把 `推进`、`交付`、`钩子`、`闭环` 等作者侧词汇当成正文语言。

## 4. 落地文件

1. `adapters/codex-skill/story-harness-writing/SKILL.md`
2. `adapters/claude-code/story-harness-writing/SKILL.md`
3. `.codex/skills/story-harness-writing/SKILL.md`
4. `adapters/codex-skill/story-harness-writing/references/writing-universal.md`
5. `adapters/claude-code/story-harness-writing/references/writing-universal.md`
6. `.codex/skills/story-harness-writing/references/writing-universal.md`
7. `adapters/codex-skill/story-harness-writing/references/genre-overlays.md`
8. `adapters/claude-code/story-harness-writing/references/genre-overlays.md`
9. `.codex/skills/story-harness-writing/references/genre-overlays.md`
10. `docs/tracking/ai-friction-tracker.md`

## 5. 非目标

1. 不重写所有 overlay 文件。
2. 不宣称现有 overlay 已具备完整文风迁移能力。
3. 不新增新的 workflow gate 或状态文件。
4. 不把外部语料全文搬入 skill。

## 6. 验证

1. skill frontmatter 基础校验。
2. 目标文件 `git diff --check`。
3. 人工回审：确认新增规则是写法方法，不是新的事实源或命令链。

## 7. 工具问题记录

- `quick_validate.py` 当前依赖环境中不存在的 `yaml` 模块，无法作为本轮校验手段。
- 已在 `docs/tracking/ai-friction-tracker.md` 记录为 `AIF-014`。
- 本轮改用 stdlib frontmatter 检查与 `git diff --check` 继续验证。
