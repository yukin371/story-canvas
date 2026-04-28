# 2026-04-28 插画模板矩阵扩展计划

> 状态: completed
> 关联入口: `docs/roadmap.md` Track 5

## 1. 背景

- 当前插画 prompt system 已具备 `pack/template/modifier/policy/lexicon` 基础能力，但模板用途仍集中在 `character`、`chapter-scene`、`promo` 三类。
- 这足够覆盖“普通插图”，但还不够支撑小说项目级图片体系：封面、人物设定、对决、追逃、搞笑、道具、生物、漫画等需求还没有稳定的 use-case owner。
- 如果继续依赖“一个万能海报模板 + 用户自由补 prompt”，会回到松散 prompt 工程，无法形成题材包 × 用途模板 × 修饰器的矩阵。

## 2. 目标

1. 在不引入平行真相源的前提下，把 `prompt pack` 从少数用途扩成第一批真实可用的图片模板矩阵。
2. 让 `entity / chapter / temporary` 三种目标都能显式选择更细的用途模板，而不是只有 freeform 图能切 use-case。
3. 保持 pack、service、CLI 的兼容边界：旧 pack 和旧命令默认行为不破。

## 3. 适用规则

- 当前执行入口：`docs/roadmap.md` Track 5 生图能力并行推进。
- Canonical owner：
  - use-case / builtin templates / lexicon / fallback 归 `src/story_harness_cli/protocol/prompt_packs.py`
  - prompt 组装与 subject 语义细化归 `src/story_harness_cli/services/illustration_prompting.py`
  - `--use-case` 暴露与参数编排归 `src/story_harness_cli/commands/illustration.py`
- 架构不变量：
  - `protocol/` 仍是模板矩阵真相源
  - `services/` 仍保持纯函数
  - `.yaml` 继续是 JSON-compatible
- 兼容性约束：
  - 旧 `character` / `chapter-scene` / `promo` 继续可用
  - 没有对应专用模板的 use-case 必须安全回退到同类模板，而不是退成 pack 第一条模板
  - `promptSnapshot/policySnapshot` 结构不破坏既有消费者

## 4. 计划改动

### 4.1 第一批 use-case 矩阵

- `cover-poster`
- `character-sheet`
- `ensemble-key-visual`
- `duel-scene`
- `chase-escape`
- `comic-relief`
- `prop-relic`
- `creature-sheet`
- `manga-panel`
- `manga-page`

### 4.2 Protocol

- 扩 builtin packs 的用途模板矩阵：
  - `default` 提供完整第一批模板
  - `light-novel` 补轻小说/漫画向模板
  - `web-serial` 补封面、群像、对决、追逃等强钩子模板
- 新增 use-case fallback 逻辑，避免 pack 没有专用模板时退错模板。
- 扩默认 `promptTemplate` / `subjectPhrases` / `detailPhrases` 映射，保证新 use-case 至少有稳定默认行为。

### 4.3 Services

- `build_entity_illustration_payload` / `build_chapter_illustration_payload` 接受更细的 `use_case`。
- 按 use-case 细化 subject 说明：
  - `character-sheet` 偏设定图/立绘
  - `duel-scene` / `chase-escape` 偏动作关系
  - `comic-relief` 偏夸张节奏
  - `manga-panel` / `manga-page` 偏黑白分镜与叙事阅读方向

### 4.4 Commands / Tests / Docs

- 扩 `illustration prompt/generate` 的 `--use-case` choices。
- 允许 chapter/entity 目标显式带更细的 use-case，而不再只对 `temp-label` 生效。
- 补 smoke tests，覆盖：
  - 新 use-case 模板解析
  - use-case fallback
  - chapter/entity 显式 use-case 覆盖
- 同步 `MODULE.md` 与协议文档。

## 5. 验证计划

- `python -m py_compile src/story_harness_cli/protocol/prompt_packs.py src/story_harness_cli/services/illustration_prompting.py src/story_harness_cli/commands/illustration.py`
- `PYTHONPATH=src python -m unittest tests.smoke.test_prompt_packs`
- `PYTHONPATH=src python -m unittest tests.smoke.test_illustration_command`
- 如无额外失败，再补 `PYTHONPATH=src python -m unittest discover -s tests`

## 6. 风险与回滚

- 风险：
  - use-case 数量上来后，如果没有 fallback，用户会频繁踩到“选了模板但 pack 不支持”的空洞。
  - 如果 chapter/entity 继续强绑旧 use-case，矩阵会停留在协议层而不是可用能力。
- 回滚路径：
  - 协议与 service 改动集中在 `prompt_packs.py` 与 `illustration_prompting.py`
  - 命令层主要是 `--use-case` 暴露，必要时可单独回退

## 7. 完成情况

- 已扩第一批 use-case 矩阵到 builtin packs、service prompt 组装与 CLI `--use-case` 暴露。
- 已为 `chapter / entity / temporary` 三类目标统一 use-case 入口，并补 chapter/entity 的 subject / guardrail 细化。
- 已补 same-family fallback，避免 pack 缺少专用模板时误退到第一条模板。
- 已补 `cover-concept` / `product` 的 legacy 默认模板兼容，保证旧 use-case 不会退成通用默认句式。
- 已同步 smoke tests 与协议/模块文档。

## 8. 验证结果

- `python -m py_compile src\story_harness_cli\protocol\prompt_packs.py src\story_harness_cli\services\illustration_prompting.py src\story_harness_cli\commands\illustration.py` 通过
- `PYTHONPATH=src python -m unittest tests.smoke.test_prompt_packs` 通过（8 tests）
- `PYTHONPATH=src python -m unittest tests.smoke.test_illustration_command` 通过（26 tests）
- `PYTHONPATH=src python -m unittest discover -s tests` 通过（384 tests）
