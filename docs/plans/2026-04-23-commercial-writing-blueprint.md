# 商业写作蓝图落地

## 背景

- 当前项目已经有 `positioning` / `storyContract`，但商业连载写作仍主要停留在样例级说明。
- 商业长篇需要的不只是“能跑通测试”，还要有真实可执行的市场定位、连载节奏、章节字数和钩子约束。
- 现有 `demo-urban-occult-long` 已隐含一部分 `commercialPositioning` 数据，但它还没有变成正式协议字段。

## 目标

1. 把商业写作蓝图收编到 `project.yaml` 正式 schema。
2. 让 `init` 可以一次性写入商业连载所需的真实字段。
3. 让 `doctor` 能识别并检查商业连载项目的节奏、钩子和字数目标。
4. 同步初始化指南、快速上手和样例工程文档，避免项目继续被误导为“只有 smoke fixture”。

## 范围

- 新增 `project.commercialPositioning` 协议字段。
- 扩展 `init` 参数，支持连载商业蓝图写入。
- 扩展 `doctor`，让商业项目默认检查更新节奏和章节字数目标。
- 更新商业长篇样例 `demo-urban-occult-long`。
- 同步相关文档。

## 验证

```powershell
$env:PYTHONPATH='src'
python -m unittest tests.smoke.test_project_init -v
python -m unittest tests.smoke.test_doctor -v
python -m unittest tests.smoke.test_demo_urban_occult_long_sample -v
python -m unittest discover -s tests
python -m story_harness_cli doctor --root projects/demo-urban-occult-long
```

