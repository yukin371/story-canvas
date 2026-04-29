# 2026-04-29 Codex Repo Skill Install

## 背景

- 当前写作 skill 的 canonical source 在 `adapters/codex-skill/story-harness-writing/`。
- `~/.codex/skills/story-harness-writing/` 只是用户级部署副本，删除后不会影响仓库 source。
- 本轮需求是把该 skill 作为仓库级 skill 使用，避免只依赖用户目录中的散落副本。

## 适用规则

- 当前执行入口：`docs/roadmap.md`
- 架构护栏：adapter 保持薄，CLI 与协议仍是真相源
- canonical owner：`adapters/codex-skill/story-harness-writing/`
- 不变量：
  - 不新增并行状态系统
  - 不把 repo-local skill 写成第二套手工维护 source
  - 默认用户级安装路径保持兼容

## 方案

1. 保留 `adapters/codex-skill/story-harness-writing/` 为唯一 source of truth。
2. 给 `scripts/install_adapter.py` 增加 `--repo-skill`，把 Codex skill 部署到：
   - `<repo>/.codex/skills/<skill-name>`，或
   - `--workspace` 指定的 `<workspace>/.codex/skills/<skill-name>`
3. 给 `scripts/install_adapters.py` 透传同一能力。
4. 用脚本生成仓库内 `.codex/skills/story-harness-writing/`，把它明确视作 deployed copy。
5. 同步 README / adapter / release 文档，避免 source of truth 混乱。

## 验证

1. `uv run python scripts/install_adapter.py --host codex --repo-skill --dry-run`
2. `uv run python scripts/install_adapter.py --host codex --repo-skill --force`
3. 检查 `.codex/skills/story-harness-writing/SKILL.md` 存在并保留合法 frontmatter

## 风险与回滚

- 风险：仓库内出现 `.codex/skills/...` 副本后，后续若直接手改副本，可能与 adapter source 漂移。
- 缓解：文档明确该目录为部署副本，只通过安装脚本刷新。
- 回滚：删除 `.codex/skills/story-harness-writing/`，并移除 `--repo-skill` 相关脚本变更。
