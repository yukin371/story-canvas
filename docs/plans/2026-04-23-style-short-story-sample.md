# 风格驱动短篇样例工程落地

> 日期: 2026-04-23
> 状态: 已完成

## 目标模块

- `projects/demo-light-novel-short/*`
- `tests/smoke/test_demo_light_novel_short_sample.py`

## 现有 owner

- 项目结构与初始化 owner: `commands/project.py` + `protocol/*`
- 样例工程 owner: 仓库内 `demo-*` 目录
- 自动化回归 owner: `tests/smoke/*`

## 影响面

- 新增一个强调 `styleTags` 的短篇样例工程
- 不修改 CLI 接口，不新增依赖

## 计划改动

1. 用现有 CLI 初始化 `demo-light-novel-short`
2. 回填西幻轻小说风格的定位层、故事契约、实体卡与 3 章正文
3. 为章节补 `volumes`、`scenePlans` 与最小 machine-facing 状态
4. 增加 README 和 smoke test，固化样例使用方式
5. 跑核心命令，验证这个风格样例能触发类型/风格相关评审输出

## 验证方式

- `PYTHONPATH=src python -m story_harness_cli doctor --root projects/demo-light-novel-short`
- `PYTHONPATH=src python -m story_harness_cli review chapter --root projects/demo-light-novel-short --chapter-id chapter-001`
- `PYTHONPATH=src python -m story_harness_cli review scene --root projects/demo-light-novel-short --chapter-id chapter-001 --scene-index 1`
- `PYTHONPATH=src python -m story_harness_cli export --root projects/demo-light-novel-short --format markdown`
- `PYTHONPATH=src python -m unittest tests.smoke.test_demo_light_novel_short_sample -v`

## 需要同步的文档

- `projects/demo-light-novel-short/README.md`
- `docs/roadmap.md`
- `docs/PROJECT_PROFILE.md`

## 架构风险

- 无新增代码 owner，主要风险在样例数据与预期风格不一致

## 重复实现风险

- 禁止为样例单独写旁路脚本；统一通过现有 CLI 和测试入口验证

## 回滚路径

- 删除 `demo-light-novel-short`、测试文件与本文档

## 兼容性影响

- 无 breaking change

## 验证结果

- `doctor --root projects/demo-light-novel-short` 通过，结构检查 `errors=0`、`warnings=0`
- `chapter analyze --chapter-id chapter-001` 通过，可识别 `艾琳 / 伦恩 / 诺瓦 / 米拉院长`
- `review chapter --chapter-id chapter-001` 通过，`weightedScores.profile` 已输出 `fantasy + western-fantasy + light-novel`
- `review scene --chapter-id chapter-001 --scene-index 1` 通过，成功读取显式 `scenePlans`
- `export --format markdown --output projects/demo-light-novel-short/manuscript.md` 通过
- `python -m unittest tests.smoke.test_demo_light_novel_short_sample -v` 通过，样例已接入自动化 smoke test
