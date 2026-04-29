# 样例工程矩阵

> 最后更新: 2026-04-23
> 适用对象: 作者 / 外部 AI / 回归验证维护者

## 1. 目的

用一页统一回答三个问题：

- 当前仓库有哪些 canonical 样例工程
- 每个样例适合验证什么能力
- 什么时候该用哪个样例

## 2. 当前矩阵

| 样例 | 定位 | 适合验证 | 当前状态 |
|------|------|----------|----------|
| `demo-short-story` | 通用短篇回归基线 | `chapter analyze`、`chapter suggest`、`review apply`、`projection apply`、`review chapter`、`review scene`、`export` | 当前有效 |
| `demo-light-novel-short` | 西幻轻小说风格短篇基线 | `positioning.subGenre`、`styleTags`、`targetAudience` 进入 `review chapter` / `review scene` 的输出 | 当前有效 |
| `demo-xuanhuan-short` | 玄幻网文短篇基线 | `xuanhuan + web-serial` 的定位层输出、推进/压制/反压制类短篇节奏 | 当前有效 |
| `demo-urban-occult-long` | 商业化网站连载长篇基线 | 长篇项目结构、卷级方向、`urban-occult + web-serial` 定位层、场景评审与长篇连载钩子 | 当前有效 |

## 3. 如何选择

- 只想确认 CLI 基础闭环能不能跑：先用 `demo-short-story`
- 想确认风格定位会不会进入评审链路：用 `demo-light-novel-short`
- 想验证玄幻网文节奏与升级驱动：用 `demo-xuanhuan-short`
- 想验证“真实网站连载长篇”的建项目方式、卷级骨架和单元案结构：用 `demo-urban-occult-long`
- 想补更多网络小说题材：以这张矩阵为入口，后续新增样例后在这里登记

## 4. 通用短篇基线

路径：`demo-short-story`

特点：

- 更通用，不绑定强风格
- 已作为短篇回归基线写入路线图
- 适合先看章节分析、章节评审、场景评审和导出闭环

推荐命令：

```powershell
$env:PYTHONPATH='src'
python -m story_canvas doctor --root projects/demo-short-story
python -m story_canvas chapter analyze --root projects/demo-short-story --chapter-id chapter-001
python -m story_canvas chapter suggest --root projects/demo-short-story --chapter-id chapter-001
python -m story_canvas review apply --root projects/demo-short-story --chapter-id chapter-001 --all-pending --decision accepted
python -m story_canvas projection apply --root projects/demo-short-story --chapter-id chapter-001
python -m story_canvas context refresh --root projects/demo-short-story --chapter-id chapter-001
python -m story_canvas review chapter --root projects/demo-short-story --chapter-id chapter-001
python -m story_canvas review scene --root projects/demo-short-story --chapter-id chapter-001 --scene-index 1
```

更多细节：`projects/demo-short-story/README.md`

## 5. 风格化短篇基线

路径：`demo-light-novel-short`

特点：

- 验证 `fantasy + western-fantasy + light-novel` 的定位层是否进入评审
- 适合检查 `weightedScores.profile`、`contractAlignment`、风格承诺是否被保留
- 已跑通过完整样例链路和自动化 smoke test

推荐命令：

```powershell
$env:PYTHONPATH='src'
python -m story_canvas doctor --root projects/demo-light-novel-short
python -m story_canvas chapter analyze --root projects/demo-light-novel-short --chapter-id chapter-001
python -m story_canvas review chapter --root projects/demo-light-novel-short --chapter-id chapter-001
python -m story_canvas review scene --root projects/demo-light-novel-short --chapter-id chapter-001 --scene-index 1
python -m story_canvas export --root projects/demo-light-novel-short --format markdown --output projects/demo-light-novel-short/manuscript.md
```

更多细节：`projects/demo-light-novel-short/README.md`

## 6. 玄幻网文基线

路径：`demo-xuanhuan-short`

特点：

- 验证 `fantasy + xuanhuan + web-serial` 的定位层是否进入评审
- 适合检查推进、压制、反压制、小型升级和阶段性跃迁是否被 review 读到
- 已接入独立 smoke test，可作为后续玄幻题材样例的起点

推荐命令：

```powershell
$env:PYTHONPATH='src'
python -m story_canvas doctor --root projects/demo-xuanhuan-short
python -m story_canvas chapter analyze --root projects/demo-xuanhuan-short --chapter-id chapter-001
python -m story_canvas review chapter --root projects/demo-xuanhuan-short --chapter-id chapter-001
python -m story_canvas review scene --root projects/demo-xuanhuan-short --chapter-id chapter-001 --scene-index 1
python -m story_canvas export --root projects/demo-xuanhuan-short --format markdown --output projects/demo-xuanhuan-short/manuscript.md
```

更多细节：`projects/demo-xuanhuan-short/README.md`

## 7. 后续扩展规则

- 新增样例前，先明确它填补的是哪一类空白，而不是重复已有样例
- 新样例落地后，先在这张矩阵登记，再决定是否需要进入 README
- 如果某类样例只是实验性样例，不应直接进入首页入口

## 8. 商业长篇基线

路径：`demo-urban-occult-long`

特点：

- 验证 `fantasy + urban-occult + web-serial + folk-occult + career-fiction` 的定位层是否进入评审
- 展示“卷级骨架 + 前几章正文 + 后续章节 brief”的长篇样例形状
- 适合检查单元案连续、主线钩子、`scenePlans` 显式场景边界和上下文刷新
- 已跑通过 `doctor`、多章 `review chapter`、多场景 `review scene` 和导出链路

推荐命令：

```powershell
$env:PYTHONPATH='src'
python -m story_canvas doctor --root projects/demo-urban-occult-long
python -m story_canvas chapter analyze --root projects/demo-urban-occult-long --chapter-id chapter-001
python -m story_canvas review chapter --root projects/demo-urban-occult-long --chapter-id chapter-001
python -m story_canvas review scene --root projects/demo-urban-occult-long --chapter-id chapter-004 --scene-index 3
python -m story_canvas export --root projects/demo-urban-occult-long --format markdown --output projects/demo-urban-occult-long/manuscript.md
```

更多细节：`projects/demo-urban-occult-long/README.md`
