## 背景

- 当前项目已支持 `outline`、`structure scaffold`、`scenePlans`、章节评审与一幕评审。
- 但“先定项目定位与故事契约，再拆章节，再细化正文”的流程最初主要靠文档约定，CLI 约束还不够硬。
- 结果是外部 AI 或作者仍可在缺少项目定位、章节方向、beat 或 scene 设计时直接进入细化环节。

## 目标

1. 提供统一的项目级 + 章节级大纲就绪检查。
2. 让 `chapter suggest` 默认拒绝对“未设计完”的章节继续细化。
3. 让 `doctor` 明确报告已有章节但缺少大纲约束的风险。
4. 提供显式的 `outline check` 命令，便于作者与外部 AI 在写作前先跑门禁。

## 计划改动

1. 新增服务层大纲就绪检查逻辑，先判断项目是否具备定位与故事契约，再判断 chapter 是否具备方向和结构拆解。
2. 在 `outline` 命令组下新增 `check` 子命令，输出章节 / 项目级就绪状态，并默认使用严格门禁。
3. 在 `chapter suggest` 中接入该门禁，默认要求目标章节先通过大纲就绪检查。
4. 在 `doctor` 中加入 outline-first 风险提示。
5. 同步 quickstart / workflow 文档，明确“先项目契约 + outline check，再 refine”。

## 验证

```powershell
$env:PYTHONPATH='src'
python -m unittest tests.smoke.test_outline_loop -v
python -m unittest tests.smoke.test_doctor -v
python -m unittest tests.smoke.test_full_creative_loop -v
python -m unittest discover -s tests
python -m story_harness_cli outline check --root projects/demo-urban-occult-long
```

## 风险

- 若规则过严，可能阻塞已有样例中的轻量短篇流程。
- 若只在 `doctor` 警告、不拦 `chapter suggest`，则约束不足。
- 若门禁逻辑在多个命令中重复实现，后续会出现口径漂移。

## 执行进展

- 已新增统一的大纲前置检查 service。
- 已新增项目级 story gate，要求 `primaryGenre`、`targetAudience`、`corePromises`、`paceContract` 齐备。
- 已新增 `outline check` 命令，支持项目级与章节级检查，且默认要求 `direction`、`beats`、`scenePlans` 全部就绪。
- 已让 `chapter suggest` 默认受门禁保护，并提供 `--allow-without-outline` 兼容旧流程。
- 已让 `doctor` 报告“已有正文但缺少前置大纲”的约束风险。
- 已补充 `outline check` 的显式放宽参数，仅用于兼容旧项目或有意放宽的场景。
