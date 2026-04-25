# Style Repair 与 Illustration MVP 实施计划

> 日期: 2026-04-25
> 状态: 实施中
> 关联: `docs/v3-plan.md`, `docs/plans/2026-04-25-prd-style-and-illustration-alignment.md`

## 1. 目标

落地两条最小可用闭环：

1. `style repair`
   - 基于已有 `style check` / `styleAnalysis` 结果输出结构化修复建议
   - 支持 `prompt` 与 `change-requests` 两种输出格式
2. `illustration` MVP
   - 支持 `prompt` / `generate --dry-run` / `list` / `config`
   - 同时覆盖 `text-to-image` 与 `image-to-image`
   - 先不把真实网络调用和文件下载做成默认测试前提

## 2. 范围

### 2.1 需要改动

- `src/story_harness_cli/commands/style.py`
- `src/story_harness_cli/services/style_detector.py`
- `src/story_harness_cli/commands/illustration.py`
- `src/story_harness_cli/services/illustration_prompting.py`
- `src/story_harness_cli/protocol/schema.py`
- `src/story_harness_cli/protocol/files.py`
- `src/story_harness_cli/protocol/state.py`
- `src/story_harness_cli/protocol/__init__.py`
- `src/story_harness_cli/commands/__init__.py`
- `src/story_harness_cli/cli.py`
- `src/story_harness_cli/services/__init__.py`
- `tests/smoke/test_style_command.py`
- `tests/smoke/test_illustration_command.py`

### 2.2 本轮不做

- adapter 自动把 `style constraints` 注入 draft prompt
- `illustration` 与 workflow gate 的自动串接

## 3. 设计口径

### 3.1 style repair

- 复用已有 `styleAnalysis.patternResults` 与 `constraints`
- `--format prompt`
  - 输出可直接贴给模型的修复提示
- `--format change-requests`
  - 输出与 `reviews/change-requests.yaml` 兼容的建议草案，但默认只打印，不自动落盘

### 3.2 illustration MVP

- `illustrations.yaml` 维护：
  - adapter 配置
  - prompt pack 配置
  - 生成记录
- `illustration prompt`
  - 生成 chapter / entity 的 prompt request
- `illustration generate --dry-run`
  - 输出 provider request 和预计写入的 metadata，不调用网络
- `illustration generate`
  - 已打通 OpenAI `gpt-image-2` 的文生图 JSON 请求与图生图 multipart 请求
  - 真实生成成功后会把返回图批量写入 `assets/illustrations/`
  - 同时把 provider request / result、主图路径和 `artifacts[]` 资产元数据写入 `illustrations.yaml`
- `illustration list`
  - 输出生成记录时补充资产存在性、数量和主图标记，便于检查落盘状态
- `illustration config`
  - 支持设置 adapter / model / size / quality

## 4. 验证

- `PYTHONPATH=src python -m unittest tests.smoke.test_style_command tests.smoke.test_illustration_command`
- 之后补跑 `uv run python -m unittest discover -s tests`
