# 2026-04-27 插画 Prompt 与工作台侧栏调整计划

## 背景

- 当前章节生图 prompt 会直接带入章节正文摘要，导致真实生成时 prompt 过长、耗时过高，也偏离“人物插画优先看角色卡外貌”的产品意图。
- 本地 OpenAI-compatible 网关在复杂 prompt 下返回 `response.output_item.done` 可能超过 180 秒，现有 provider 超时偏低。
- 当前左侧导航仍是宽侧栏 + 内嵌摘要，不符合“VS Code activity bar + 列表面板”的目标。

## 本轮目标

1. 收敛插画 prompt 来源：
   - 角色目标优先使用实体卡外貌 / 身份 / 状态字段
   - 章节目标不再把整段章节内容直接塞进 prompt，而是收敛到更短的场景锚点
2. 提高图片 provider 请求超时，避免真实网关在长耗时图生成下提前超时。
3. 重构工作台左侧为：
   - 窄 activity bar：快速切换审查 / 插画 / 设置
   - 独立列表面板：项目列表、摘要、章节 / 历史等真实列表内容

## 影响面

- `src/story_harness_cli/services/illustration_prompting.py`
- `src/story_harness_cli/providers/image/openai_http.py`
- `scripts/story_canvas_ui_api.py`
- `ui/src/api/storyCanvas.ts`
- `ui/src/App.vue`
- `ui/src/views/WorkbenchView.vue`
- `ui/src/styles.css`

## 验证

- `python -m py_compile scripts/story_canvas_ui_api.py src/story_harness_cli/services/illustration_prompting.py src/story_harness_cli/providers/image/openai_http.py`
- `npm run build` in `ui/`
- 通过本地 `/api/illustration/dry-run` 检查 prompt 收敛结果

## 风险

- 实体卡外貌字段分布可能不统一，需要做兼容式提取。
- 左侧布局重构会影响 review / illustration / settings 三个工作区的整体宽度分配。
