## 背景

- 当前仓库已有 `demo-short-story`、`demo-light-novel-short`、`demo-xuanhuan-short` 三个短篇基线。
- 短篇样例已经足够承担命令链路回归和风格权重切换验证，但不足以展示“连载型长篇小说工程”的真实使用方式。
- 现有 `demo-novel` 仍可作为历史长篇样例存在，但结构较杂，不适合作为新的 canonical 商业长篇入口。

## 目标

新增一个面向网站连载的长篇商业样例，名称暂定 `demo-urban-occult-long`，用于同时验证以下能力：

1. 长篇项目初始化后的定位层、故事契约和章节方向维护。
2. “案件单元 + 职业叙事 + 主线阴谋”在 `review chapter` / `review scene` 中的可读性。
3. `doctor`、`chapter analyze`、`review chapter`、`review scene`、`context refresh`、`export` 的长篇样例闭环。
4. 样例矩阵从“短篇回归”扩展到“短篇回归 + 长篇商业样例”。

## 题材选择

默认采用：

- 主类型：`fantasy`
- 子类型：`urban-occult`
- 风格标签：`web-serial`、`folk-occult`、`career-fiction`
- 目标读者：`qidian-reader`、`urban-fantasy-reader`、`folk-occult-reader`

选择理由：

1. 相比继续重复“纯玄幻升级”或“西幻轻小说”，都市民俗志怪更能填补现有样例空白。
2. 民俗、志怪、职业线和强钩子单元案天然适合网站连载的章节末尾留扣。
3. “小案连续 + 大案不偏纲”的结构，更适合验证 Story Harness 的场景评审、连续性、伏笔和主线管理能力。

## 样例范围

- 建立 1 个完整卷级骨架。
- 卷一至少 10 章章节方向，建议 12 章。
- 前 4 章提供完整正文，后续章节至少提供明确 `chapterDirections`、beats 和 `scenePlans`。
- 每章维护显式 `scenePlans`，让 `review scene` 走显式边界而不是启发式切分。

## 差异化定位

- `demo-short-story`：通用短篇回归基线。
- `demo-light-novel-short`：西幻轻小说风格短篇。
- `demo-xuanhuan-short`：玄幻网文短篇。
- `demo-urban-occult-long`：商业化长篇连载样例，强调市场定位、职业叙事、民俗志怪和中长线伏笔。

## 交付物

1. `projects/demo-urban-occult-long/`
2. `projects/demo-urban-occult-long/MODULE.md`
3. `projects/demo-urban-occult-long/README.md`
4. 长篇样例对应 smoke test
5. `docs/guides/sample-matrix.md` 更新
6. `docs/roadmap.md` 更新
7. `docs/PROJECT_PROFILE.md` 更新

## 验证

```powershell
$env:PYTHONPATH='src'
python -m story_harness_cli doctor --root projects/demo-urban-occult-long
python -m story_harness_cli chapter analyze --root projects/demo-urban-occult-long --chapter-id chapter-001
python -m story_harness_cli review chapter --root projects/demo-urban-occult-long --chapter-id chapter-001
python -m story_harness_cli review scene --root projects/demo-urban-occult-long --chapter-id chapter-001 --scene-index 1
python -m story_harness_cli context refresh --root projects/demo-urban-occult-long --chapter-id chapter-001
python -m story_harness_cli export --root projects/demo-urban-occult-long --format markdown --output projects/demo-urban-occult-long/manuscript.md
python -m unittest tests.smoke.test_demo_urban_occult_long_sample -v
```

## 风险

- 风险 1：只补目录和文档，不补足够长的卷级结构，会让它继续退化成“长一点的短篇”。
- 风险 2：如果只写世界观氛围、不写职业流程和单元案，商业化定位会失真。
- 风险 3：如果没有显式 `scenePlans`，长篇样例无法稳定验证一幕级评审链路。
