# Provider Foundation Plan

> 日期：2026-04-25
> 状态：In Progress
> 关联：`ADR-002`

## 1. 目标

为 v3 的 optional dependencies / providers 方案先落一层最小基础设施，避免后续 style 和 illustration 各自重复实现依赖加载、provider 错误处理和模块边界。

## 2. 本轮范围

- `pyproject.toml` 增加 optional dependencies
- 新增 `src/story_harness_cli/providers/` 骨架
- `style_detector.py` 接入可选 `rapidfuzz` 增强路径
- 补最小测试覆盖 fallback 与 optional path

## 3. 本轮不做

- 不实现完整 `style` CLI 命令
- 不实现完整 `illustration` CLI 命令
- 不落真实项目级 pack loader
- 不修改现有状态文件协议

## 4. 设计约束

- base install 继续 stdlib-only
- optional dependency 缺失时必须自动回退 builtin
- `providers/` 只负责外部系统和 optional dependency wrapper
- `services/` 只保留纯逻辑和 fallback

## 5. 验证

- `PYTHONPATH=src python -m unittest tests.smoke.test_style_detector`
- `git diff --check -- pyproject.toml src/story_harness_cli/providers src/story_harness_cli/services/style_detector.py tests/smoke/test_style_detector.py docs/plans/2026-04-25-provider-foundation.md`
