# Style Profile Doctor Validation Plan

> 日期：2026-04-25
> 状态：In Progress

## 1. 目标

为 `style-profiles.yaml` 增加最小 `doctor` 校验，避免项目自定义 style profile 时出现：

- 文件格式不可解析
- profile 结构错误但命令运行时才暴露
- 阈值或 regex 列表类型错误

## 2. 本轮范围

- `doctor` 检查 `style-profiles.yaml` 的可解析性
- 校验 `profiles`、`patternThresholds`、`extraPatterns` 的基本结构
- 输出当前项目自动选中的 style profile
- 补 smoke test

## 3. 本轮不做

- 不为 style profile 增加正式 schema 文件
- 不增加 project.yaml 显式 style profile 字段
- 不校验 regex 本身的语义质量

## 4. 验证

- `PYTHONPATH=src python -m unittest tests.smoke.test_doctor tests.smoke.test_style_profiles`
