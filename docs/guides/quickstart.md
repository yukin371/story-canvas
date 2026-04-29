# Quickstart

如果你要先看“完整创作闭环”，直接读 [创作流程指南](./creative-workflow.md)。
如果你要先决定“跑哪个样例工程”，直接读 [样例工程矩阵](./sample-matrix.md)。

## 1. Install

```powershell
uv sync
```

## 2. Initialize a project

```powershell
uv run story-canvas init --root .\demo --title "Fog Harbor" --genre "Mystery"
```

如果你准备直接进入严格写作闭环，初始化时就把项目门禁字段一并写上：

```powershell
uv run story-canvas init `
  --root .\demo `
  --title "Fog Harbor" `
  --genre "Mystery" `
  --primary-genre mystery `
  --target-audience mystery-reader `
  --core-promise "每章推进账本谜团" `
  --pace-contract "中快节奏"
```

`chapter suggest` 默认不会接受“先写再补约束”的流程。
进入细化前，`outline check` 默认要求项目先具备 `primaryGenre`、`targetAudience`、`corePromises`、`paceContract`，章节再具备 `direction`、`beats`、`scenePlans`。
`init` 只会创建空白章节 stub，不会再往正文里塞占位说明；初始化后优先跑 `status --chapter-id <id>` 看 `startGuide`，按提示补第一章结构。
如果你要从零开始直接验证“写完一卷 -> 进入卷级 AI 自审”，初始化时就把首卷一起建出来：

```powershell
uv run story-canvas init `
  --root .\demo `
  --title "Fog Harbor" `
  --genre "Mystery" `
  --primary-genre mystery `
  --target-audience mystery-reader `
  --core-promise "每章推进账本谜团" `
  --pace-contract "中快节奏" `
  --volume-id volume-001 `
  --volume-title "第一卷 雾港吞名案" `
  --volume-theme "从被卷入到主动追查"
```

如果你做的是网站连载或商业长篇，不要只填基础定位，建议把 `commercialPositioning` 也在初始化时写上：

```powershell
uv run story-canvas init `
  --root .\demo `
  --title "夜巡收煞录" `
  --genre "奇幻" `
  --primary-genre fantasy `
  --sub-genre urban-occult `
  --style-tag web-serial `
  --target-audience qidian-reader `
  --core-promise "每章结尾保留追读钩子" `
  --pace-contract "中快节奏" `
  --premise "夜班接尸人继承城隍夜巡牌，处理都市异案并追查失踪父亲真相" `
  --hook-line "接尸抬到空棺的当夜，他被迫上岗做城隍夜巡。" `
  --hook-stack career-entry-hook `
  --hook-stack cliffhanger-end `
  --benchmark-work "都市职业捉诡文" `
  --target-platform qidian `
  --serialization-model "2到3章一个单元异案，持续抬升主线阴谋" `
  --release-cadence "日更两章" `
  --chapter-word-floor 2000 `
  --chapter-word-target 3000
```

`doctor` 会在识别到 `web-serial` / 平台连载项目后，额外检查 `premise`、`hookLine`、`hookStack`、`targetPlatform`、`serializationModel`、`releaseCadence`，并优先采用项目里配置的章节字数目标。

如果你想直接跑一个仓库内已验证样例，而不是先自己写正文，优先使用 `demo-short-story`：

```powershell
uv run story-canvas doctor --root .\projects\demo-short-story
uv run story-canvas chapter analyze --root .\projects\demo-short-story --chapter-id chapter-001
uv run story-canvas review chapter --root .\projects\demo-short-story --chapter-id chapter-001
uv run story-canvas review scene --root .\projects\demo-short-story --chapter-id chapter-001 --scene-index 1
```

如果你要验证“类型 / 子类型 / 风格标签 / 目标读者”是否进入评审链路，改用 `demo-light-novel-short`：

```powershell
uv run story-canvas doctor --root .\projects\demo-light-novel-short
uv run story-canvas chapter analyze --root .\projects\demo-light-novel-short --chapter-id chapter-001
uv run story-canvas review chapter --root .\projects\demo-light-novel-short --chapter-id chapter-001
uv run story-canvas review scene --root .\projects\demo-light-novel-short --chapter-id chapter-001 --scene-index 1
```

如果你要验证“玄幻 + 网文节奏”的定位层和中短篇升级驱动，改用 `demo-xuanhuan-short`：

```powershell
uv run story-canvas doctor --root .\projects\demo-xuanhuan-short
uv run story-canvas chapter analyze --root .\projects\demo-xuanhuan-short --chapter-id chapter-001
uv run story-canvas review chapter --root .\projects\demo-xuanhuan-short --chapter-id chapter-001
uv run story-canvas review scene --root .\projects\demo-xuanhuan-short --chapter-id chapter-001 --scene-index 1
```

这三个样例的定位差异与扩展策略，统一以 [样例工程矩阵](./sample-matrix.md) 为准。

## 3. Replace the first chapter with tagged prose

Prefer `@{实体}` in Chinese prose:

```markdown
# 第一章

@{林舟}拖着受伤的手臂走进仓库，掌心还在流血。
```

## 4. Run the chapter loop

```powershell
uv run story-canvas outline check --root .\demo --chapter-id chapter-001
uv run story-canvas chapter analyze --root .\demo --chapter-id chapter-001
uv run story-canvas chapter suggest --root .\demo --chapter-id chapter-001
uv run story-canvas review apply --root .\demo --chapter-id chapter-001 --all-pending --decision accepted
uv run story-canvas projection apply --root .\demo --chapter-id chapter-001
uv run story-canvas context refresh --root .\demo --chapter-id chapter-001
uv run story-canvas review chapter --root .\demo --chapter-id chapter-001
uv run story-canvas outline scene-detect --root .\demo --chapter-id chapter-001
uv run story-canvas review scene --root .\demo --chapter-id chapter-001 --scene-index 1
uv run story-canvas doctor --root .\demo
```

如果你想先按经典结构把整本书的节拍骨架定下来，而不是直接手写章节方向，可以先跑：

```powershell
uv run story-canvas structure list --root .\demo
uv run story-canvas structure apply --root .\demo --template three-act
uv run story-canvas structure show --root .\demo
uv run story-canvas structure scaffold --root .\demo
uv run story-canvas outline check --root .\demo
uv run story-canvas structure check --root .\demo
```

当前内置模板包含：`three-act`、`five-act`、`hero-journey`、`save-the-cat`。

`structure scaffold` 会把当前模板的 beat 直接落到 `outline.yaml` 的章节 `beats` 和 `direction` 上。
默认会优先使用 `structure map` 的显式映射；没有映射时，会按 beat 位置自动建议章节。
如果章节已经有手工 `direction`，默认保留；需要覆盖时加 `--replace-directions`。
`outline check` 默认会检查“项目定位 / 故事契约 + 章节 direction + beats + scenePlans”是否齐备，再决定是否进入正文细化。
如果当前章还没有正文段落，先在 `chapters/<chapter-id>.md` 里按计划场景写 1 段骨架，再运行 `outline scene-detect` 生成首版 `scenePlans`。
只有在明确接受放宽约束时，才使用 `--allow-missing-project-gate`、`--allow-missing-beats`、`--allow-missing-scene-plans`。

如果你在做网站连载，还建议把字数检查放进每轮闭环：

```powershell
uv run story-canvas stats --root .\demo --min-chapter-words 2000 --target-chapter-words 3000
uv run story-canvas doctor --root .\demo --min-chapter-words 2000 --target-chapter-words 3000
```

If `story-canvas` is not available in your environment yet, use the repository fallback:

```powershell
$env:PYTHONPATH='src'
python -m story_canvas outline check --root .\demo --chapter-id chapter-001
python -m story_canvas chapter analyze --root .\demo --chapter-id chapter-001
python -m story_canvas chapter suggest --root .\demo --chapter-id chapter-001
python -m story_canvas review apply --root .\demo --chapter-id chapter-001 --all-pending --decision accepted
python -m story_canvas projection apply --root .\demo --chapter-id chapter-001
python -m story_canvas context refresh --root .\demo --chapter-id chapter-001
python -m story_canvas review chapter --root .\demo --chapter-id chapter-001
python -m story_canvas outline scene-detect --root .\demo --chapter-id chapter-001
python -m story_canvas review scene --root .\demo --chapter-id chapter-001 --scene-index 1
python -m story_canvas doctor --root .\demo
```

Validated sample fallback:

```powershell
$env:PYTHONPATH='src'
python -m story_canvas doctor --root .\projects\demo-short-story
python -m story_canvas chapter analyze --root .\projects\demo-short-story --chapter-id chapter-001
python -m story_canvas outline check --root .\projects\demo-short-story --chapter-id chapter-001
python -m story_canvas review chapter --root .\projects\demo-short-story --chapter-id chapter-001
python -m story_canvas review scene --root .\projects\demo-short-story --chapter-id chapter-001 --scene-index 1
```

Style-driven sample fallback:

```powershell
$env:PYTHONPATH='src'
python -m story_canvas doctor --root .\projects\demo-light-novel-short
python -m story_canvas chapter analyze --root .\projects\demo-light-novel-short --chapter-id chapter-001
python -m story_canvas review chapter --root .\projects\demo-light-novel-short --chapter-id chapter-001
python -m story_canvas review scene --root .\projects\demo-light-novel-short --chapter-id chapter-001 --scene-index 1
```

Xuanhuan sample fallback:

```powershell
$env:PYTHONPATH='src'
python -m story_canvas doctor --root .\projects\demo-xuanhuan-short
python -m story_canvas chapter analyze --root .\projects\demo-xuanhuan-short --chapter-id chapter-001
python -m story_canvas review chapter --root .\projects\demo-xuanhuan-short --chapter-id chapter-001
python -m story_canvas review scene --root .\projects\demo-xuanhuan-short --chapter-id chapter-001 --scene-index 1
```

## 5. Close The Loop

If `review chapter` or `review scene` gives a weak result, do not stop at the first score.

Standard close-the-loop sequence:

1. Run `review chapter`
2. Run `review scene`
3. Inspect the lowest-scoring dimensions and `priorityActions`
4. For commercial serials, also inspect `commercialAlignment`, `weightedScores.profile.targetPlatform`, and chapter word-count warnings
5. Revise `chapters/*.md` or explicit `scenePlans`
6. Re-run `outline check` if you changed positioning, contract, beats, or `scenePlans`
7. Re-run `chapter analyze`
8. Re-run `review chapter` and `review scene`
9. Only stop when the score is good enough for the current target, or when the remaining risk is explicitly accepted

## 6. Inspect machine-facing state

- `demo/reviews/change-requests.yaml`
- `demo/reviews/story-reviews.yaml`
- `demo/projections/projection.yaml`
- `demo/projections/context-lens.yaml`

## 7. Validate the project shape

```powershell
uv run story-canvas doctor --root .\demo
```

Use `--strict` if you want warnings to fail CI or release checks.
