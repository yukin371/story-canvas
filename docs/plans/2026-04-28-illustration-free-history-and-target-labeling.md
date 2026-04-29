## 背景

- 当前插画工作台左侧“最近结果”只消费当前项目的 `illustrations.generated`，导致自由模式下历史结果虽然实际写进了 workbench sandbox，却无法在界面上回看。
- 历史列表和右侧结果区优先展示 `chapter-023` 这类协议 id，用户很难直接判断它对应哪一章/哪个自由目标，容易误以为目标被错误绑定。

## 本轮目标

1. 让自由模式历史也能进入插画工作台的统一历史列表，并支持切回预览。
2. 让结果区和历史列表优先显示更可读的目标名称，而不是只显示 raw target id。
3. 保持历史真实来源仍是项目协议或 workbench sandbox，不在前端新增平行持久化。

## 影响面

- `scripts/story_canvas_ui_api.py`
- `src/story_harness_cli/commands/illustration.py`
- `src/story_harness_cli/commands/illustration_support.py`
- `ui/src/api/storyCanvas.ts`
- `ui/src/views/workbench/IllustrationWorkbenchView.vue`
- `ui/src/components/workbench/IllustrationWorkbenchPane.vue`
- `ui/MODULE.md`

## 适用规则

- 当前执行入口：`docs/roadmap.md`
- UI 不是新的真相源；只能消费已有协议与本地 API 输出
- 自由模式结果继续只落在 workbench sandbox，不写回真实项目协议
- 本地 UI API 仍是工作台读取/桥接自由模式历史的 canonical 入口
- 改动保持非 breaking，只增补历史视图所需字段与展示逻辑

## 计划改动

1. 在 workbench settings / API 响应里补出 sandbox 最近插画记录。
2. 历史记录装饰阶段补 `targetName`，并在新生成记录里持久化该字段。
3. 前端统一合并“当前项目历史 + 自由模式历史”，并在切换自由历史时自动回到自由模式上下文。
4. 右侧结果摘要与左侧历史列表优先显示 `targetName`，必要时再附带 raw id。

## 验证

- `npm run build` in `ui/`
- 浏览器 MCP：
  - 项目模式能看到项目历史和自由历史
  - 自由模式能看到之前自由生成历史
  - 点击历史后右侧预览能切换
  - 点击结果图能放大

## 风险

- 老的自由模式历史若创建时未持久化目标名称，只能退化显示通用目标名，无法完全还原当时的手填名称。
- 合并历史后，需要避免自由模式图片继续按当前项目 root 去拼资产 URL。

## 回滚路径

- 可单独回退前端合并历史展示。
- 可单独回退 API 中 workspace recentIllustrations 扩展字段。
