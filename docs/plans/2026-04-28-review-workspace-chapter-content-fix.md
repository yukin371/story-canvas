# 审查工作区章节正文修正计划

> 创建日期: 2026-04-28
> 状态: 进行中
> 关联当前入口: `docs/roadmap.md`

## 一、问题

当前 UI 章节记录把 review summary 直接塞进 `summary` 字段，审查主区又把它当正文渲染，导致用户看到的是修复建议而不是章节内容。

## 二、目标

1. 让章节正文以独立字段进入本地 UI API
2. 让 `summary` 回到“正文预览”语义
3. 让审查工作区正文优先渲染，审查摘要作为附属信息展示

## 三、实施范围

- `scripts/story_canvas_ui_api.py`
- `ui/src/api/storyCanvas.ts`
- `ui/src/views/WorkbenchView.vue`
- `ui/src/views/ChaptersView.vue`

## 四、验证

- `python -m py_compile scripts/story_canvas_ui_api.py`
- `npm run build`
