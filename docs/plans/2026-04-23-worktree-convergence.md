# 工作区收敛与提交拆分建议

## 背景

- 当前仓库不是单一功能小改，而是多轮连续落地产生的大工作树。
- 代码、协议、样例、文档、adapter skill、测试基线都已经发生变化。
- 全量测试已通过，但提交面仍偏大，不适合直接压成一个 commit。

## 当前判断

### 1. 已验证

- `PYTHONPATH=src python -m unittest discover -s tests` 已通过。
- 商业连载评审、场景评审、样例矩阵、结构化大纲与长短篇样例链路都已进入当前基线。

### 2. 不建议当作噪音直接删除的内容

下面这些虽然多数是未跟踪文件，但在当前仓库语义里更接近“样例工程快照”或“新功能基线”，不建议未经确认直接删掉：

- `projects/demo-short-story/`
- `projects/demo-light-novel-short/`
- `projects/demo-xuanhuan-short/`
- `projects/demo-urban-occult-long/`
- `projects/demo-novel/` 下新增的 `project.yaml` / `outline.yaml` / `chapters/` / `logs/` / `projections/` / `reviews/` / `timeline.yaml`
- `tests/fixtures/minimal_project/structures.yaml`
- `tests/fixtures/minimal_project/threads.yaml`
- `tests/fixtures/minimal_project/reviews/story-reviews.yaml`

原因：

- 它们已被 smoke tests 和文档当作真实样例、回归样本或最小协议基线引用。
- 当前不是单纯运行产物，而是“被仓库工作流依赖的样例状态”。

### 3. 需要单独判断的内容

以下内容更像宿主环境或仓库治理补充，适合单独提交，或在提交前再次确认：

- `.claude/skills/story-harness-writing/`
- `MODULE.md`
- `adapters/MODULE.md`

补充判断：

- `.claude/skills/story-harness-writing/references/protocol.md` 与 `adapters/claude-code/.../protocol.md` 当前内容一致
- 但 `.claude/skills/story-harness-writing/SKILL.md` 与 `adapters/claude-code/.../SKILL.md` 哈希不同，更像安装后的宿主副本，而不是仓库 source of truth

## 建议拆分

### Commit 1: 结构化大纲与写作前门禁

建议包含：

- `src/story_harness_cli/commands/outline.py`
- `src/story_harness_cli/commands/structure.py`
- `src/story_harness_cli/services/outline_guard.py`
- `src/story_harness_cli/services/structure.py`
- `src/story_harness_cli/utils/project_meta.py`
- `src/story_harness_cli/commands/chapter.py`
- `src/story_harness_cli/commands/project.py`
- `src/story_harness_cli/protocol/schema.py`
- `src/story_harness_cli/protocol/state.py`
- `src/story_harness_cli/services/__init__.py`
- `tests/smoke/test_outline_loop.py`
- `tests/smoke/test_full_creative_loop.py`
- `tests/smoke/test_single_chapter_loop.py`
- `tests/smoke/test_schema.py`

主题：

- 先设计结构模板与 outline-first 约束，再允许正文细化。

### Commit 2: 章节/一幕评审与商业连载评分

建议包含：

- `src/story_harness_cli/commands/review.py`
- `src/story_harness_cli/commands/doctor.py`
- `src/story_harness_cli/commands/stats.py`
- `src/story_harness_cli/services/story_review.py`
- `src/story_harness_cli/services/stats.py`
- `tests/smoke/test_review_chapter.py`
- `tests/smoke/test_review_scene.py`
- `tests/smoke/test_doctor.py`
- `tests/smoke/test_stats.py`
- `tests/smoke/test_project_init.py`
- `tests/smoke/test_demo_urban_occult_long_sample.py`

主题：

- 把定位层、商业蓝图、章节字数目标、平台加权和 `commercialAlignment` 接入 review / doctor / stats。

### Commit 3: 样例矩阵与商业化 demo 基线

建议包含：

- `projects/demo-short-story/`
- `projects/demo-light-novel-short/`
- `projects/demo-xuanhuan-short/`
- `projects/demo-urban-occult-long/`
- `tests/smoke/test_demo_short_story_sample.py`
- `tests/smoke/test_demo_light_novel_short_sample.py`
- `tests/smoke/test_demo_xuanhuan_short_sample.py`

主题：

- 用真实样例替代 smoke-only 心智模型，建立短篇回归基线和长篇商业基线。

推荐 commit message：

```text
新增短篇与商业长篇样例回归基线
```

建议提交前最小验证：

```powershell
$env:PYTHONPATH='src'
python -m unittest tests.smoke.test_demo_short_story_sample tests.smoke.test_demo_light_novel_short_sample tests.smoke.test_demo_xuanhuan_short_sample tests.smoke.test_demo_urban_occult_long_sample -v
```

建议纳入本组的样例文件类型：

- `README.md`
- `MODULE.md`（若该样例存在）
- `project.yaml`
- `outline.yaml`
- `chapters/*.md`
- `entities.yaml`
- `branches.yaml`
- `structures.yaml`
- `threads.yaml`
- `timeline.yaml`

可选纳入的状态快照：

- `logs/*.yaml`
- `projections/*.yaml`
- `proposals/*.yaml`
- `reviews/*.yaml`

说明：

- 这些文件更接近“已验证样例状态”，有助于展示完整协议闭环，但并非所有 smoke test 的硬依赖。
- 若你希望样例更像“最小可运行工程”，可以先不提交这类状态快照，后续再单独补一组“样例状态快照”。

不建议默认纳入：

- `demo-*/manuscript.md`

原因：

- 它们更像导出产物，不是样例工程的 canonical source。
- 当前 smoke tests 会自己导出 `manuscript-smoke.md`，不依赖仓库内现存 `manuscript.md`。

`demo-novel` 的处理建议：

- 不要和这四个 canonical demo 放在同一个 commit。
- 它当前没有直接 smoke test 兜底，更像“历史长篇样例扩展”。
- 若要保留，建议单独提交，主题偏“历史样例补齐 scene plan / positioning 状态”，而不是“canonical sample matrix”。

### Commit 4: 文档、README、技能与模块说明同步

建议包含：

- `README.md`
- `docs/PROJECT_PROFILE.md`
- `docs/roadmap.md`
- `docs/protocol/file-layout.md`
- `docs/guides/*.md`
- `docs/plans/2026-04-23-*.md`
- `src/story_harness_cli/commands/MODULE.md`
- `src/story_harness_cli/protocol/MODULE.md`
- `src/story_harness_cli/services/MODULE.md`
- `tests/smoke/MODULE.md`
- `adapters/README.md`
- `adapters/*/story-harness-writing/SKILL.md`
- `adapters/*/story-harness-writing/references/protocol.md`

主题：

- 把“小说工程化 + 商业写作 + 评审闭环 + 外部 AI 使用方式”同步到仓库文档和 skill。

### Commit 5: 历史样例 / 仓库治理 / 宿主补充（可选）

建议单独看：

- `demo-novel`
- `.claude/`
- 根目录 `MODULE.md`
- `adapters/MODULE.md`

主题：

- 属于宿主集成或治理补充，不应和核心功能 commit 混在一起。
- 若 `.claude/` 只是本机安装副本，建议直接排除在本仓库提交之外。

## 当前可提交性判断

- 从“功能正确性”看：已可提交。
- 从“提交清晰度”看：还不适合一把提交，应按上面的 4 到 5 组拆分。
- 如果只能做一次提交，至少也应拆成“代码/测试”和“文档/样例”两组，避免回滚成本过高。

## 建议下一步

1. 先按上述分组人工确认哪些文件确实要进入仓库历史。
2. 再按组分批 `git add`。
3. 每组提交前跑一轮最小相关测试；最后再跑一次全量测试。

## 可直接执行的暂存顺序

### 1) 先暂存核心代码组

```powershell
git add src/story_harness_cli/commands/outline.py
git add src/story_harness_cli/commands/structure.py
git add src/story_harness_cli/services/outline_guard.py
git add src/story_harness_cli/services/structure.py
git add src/story_harness_cli/utils/project_meta.py
git add src/story_harness_cli/commands/chapter.py
git add src/story_harness_cli/commands/project.py
git add src/story_harness_cli/protocol/schema.py
git add src/story_harness_cli/protocol/state.py
git add src/story_harness_cli/services/__init__.py
git add tests/smoke/test_outline_loop.py
git add tests/smoke/test_full_creative_loop.py
git add tests/smoke/test_single_chapter_loop.py
git add tests/smoke/test_schema.py
```

推荐 commit message：

```text
强化 outline-first 门禁并落地结构化大纲骨架
```

建议提交前最小验证：

```powershell
$env:PYTHONPATH='src'
python -m unittest tests.smoke.test_outline_loop tests.smoke.test_full_creative_loop tests.smoke.test_single_chapter_loop tests.smoke.test_schema -v
```

### 2) 再暂存 review / doctor 组

```powershell
git add src/story_harness_cli/commands/review.py
git add src/story_harness_cli/commands/doctor.py
git add src/story_harness_cli/commands/stats.py
git add src/story_harness_cli/services/story_review.py
git add src/story_harness_cli/services/stats.py
git add tests/smoke/test_review_chapter.py
git add tests/smoke/test_review_scene.py
git add tests/smoke/test_doctor.py
git add tests/smoke/test_stats.py
git add tests/smoke/test_project_init.py
git add tests/smoke/test_demo_urban_occult_long_sample.py
```

推荐 commit message：

```text
接入商业连载评审与项目级字数约束
```

建议提交前最小验证：

```powershell
$env:PYTHONPATH='src'
python -m unittest tests.smoke.test_review_chapter tests.smoke.test_review_scene tests.smoke.test_doctor tests.smoke.test_stats tests.smoke.test_project_init tests.smoke.test_demo_urban_occult_long_sample -v
```

### 3) 样例基线单独一组

```powershell
git add demo-short-story
git add demo-light-novel-short
git add demo-xuanhuan-short
git add demo-urban-occult-long
git add tests/smoke/test_demo_short_story_sample.py
git add tests/smoke/test_demo_light_novel_short_sample.py
git add tests/smoke/test_demo_xuanhuan_short_sample.py
```

推荐 commit message：

```text
新增短篇与商业长篇样例回归基线
```

### 4) 文档与 skill 单独一组

```powershell
git add README.md
git add docs/PROJECT_PROFILE.md
git add docs/roadmap.md
git add docs/protocol/file-layout.md
git add docs/guides
git add docs/plans/2026-04-23-*.md
git add src/story_harness_cli/commands/MODULE.md
git add src/story_harness_cli/protocol/MODULE.md
git add src/story_harness_cli/services/MODULE.md
git add tests/smoke/MODULE.md
git add adapters/README.md
git add adapters/codex-skill/story-harness-writing
git add adapters/claude-code/story-harness-writing
```

推荐 commit message：

```text
同步小说工程化工作流文档与外部 AI skill
```

建议提交前最小验证：

```powershell
git diff --check -- README.md adapters/README.md adapters/claude-code/story-harness-writing/SKILL.md adapters/claude-code/story-harness-writing/references/protocol.md adapters/codex-skill/story-harness-writing/SKILL.md adapters/codex-skill/story-harness-writing/references/protocol.md docs/PROJECT_PROFILE.md docs/guides/quickstart.md docs/guides/creative-workflow.md docs/guides/genre-review-rubric.md docs/guides/novel-engineering-init.md docs/guides/sample-matrix.md docs/protocol/file-layout.md docs/roadmap.md src/story_harness_cli/commands/MODULE.md src/story_harness_cli/protocol/MODULE.md src/story_harness_cli/services/MODULE.md tests/smoke/MODULE.md
```

额外说明：

- 这一组更适合做“口径一致性检查”，不一定需要新增代码测试。
- `adapters/codex-skill/...` 与 `adapters/claude-code/...` 不是镜像文件，而是同一工作流在不同宿主上的薄适配。
- `protocol.md` 的差异目前主要体现在宿主名称表述；`SKILL.md` 也存在宿主特定措辞与行为提示差异，因此不要尝试把两者强行合并成同一个文件。

### 5) 只在确认后再考虑的补充组

```powershell
git add MODULE.md
git add adapters/MODULE.md
git add .claude
git add demo-novel
```

## 明确不建议纳入核心提交的内容

- `.claude/`：更像本地安装副本，不是 source of truth
- `demo-*/manuscript.md` / `projects/demo-novel/manuscript.json` / `projects/demo-novel/manuscript.txt`：更偏导出产物，可按是否需要保留示例输出单独决定

如果你要的是“干净历史”，优先只提交 `project.yaml` / `outline.yaml` / `chapters/` / `reviews/` / `projections/` / `logs/` / `timeline.yaml` 这些真正被样例和测试依赖的状态文件，导出成品留到第二轮再决定。
