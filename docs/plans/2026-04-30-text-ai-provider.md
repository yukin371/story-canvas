# 2026-04-30 Text AI Provider

## 背景

项目原本主要面向 Codex / Claude Code 这类编程宿主使用。真实写作与卷级审查实跑后，宿主内置提示词和既有会话上下文会影响独立编辑判断，尤其容易让同一线程里的自审变成作者自我辩护。

## 目标

1. 引入可选文本 AI provider lane，用于干净上下文的独立编辑审查。
2. 保持核心 CLI、协议、review gate 和测试基线离线可运行。
3. 产出可直接作为 `review volume-self-template --editor-input` / `review volume-self --editor-input` 消费的 editor fragment。

## 非目标

1. 不把章节正文生成接入 provider。
2. 不让 provider 输出自动成为项目真相源。
3. 不引入必需第三方 SDK。
4. 不改变既有 `volume-self` 输入结构。

## 适用规则

- 当前执行入口：`docs/roadmap.md`
- 架构护栏：外部 API 调用归 `providers/`；命令 I/O 归 `commands/`；`services/` 保持纯函数
- ADR：`docs/adr/ADR-002-optional-dependencies-and-providers.md`
- 模块 owner：`src/story_harness_cli/providers/MODULE.md`、`src/story_harness_cli/commands/MODULE.md`、`src/story_harness_cli/services/MODULE.md`
- 兼容性：新增命令和输出字段，不破坏既有 CLI 参数、状态文件或 review schema
- AI friction：AIF-001、AIF-002、AIF-013

## 设计

新增 `review editor-draft`：

```powershell
story-canvas review editor-draft --root <project> --volume-id <volume-id> --dry-run
story-canvas review editor-draft --root <project> --volume-id <volume-id> --output reviews/<volume-id>-editor-pass.json
```

命令职责：

1. 刷新并读取卷级 review packet。
2. 构造 clean-room editor prompt。
3. dry-run 时只输出 provider request，不发网络请求。
4. 真实运行时调用 OpenAI-compatible text provider。
5. 将 provider JSON 输出归一为 `editorPass` + `editorAssessment` fragment。

Provider 边界：

1. 首版使用 stdlib `urllib.request`。
2. 默认走 Responses API `/v1/responses`。
3. 支持 `--base-url` 兼容网关。
4. API key 从 `--api-key` / `TEXT_PROVIDER_API_KEY` / `OPENAI_API_KEY` / `API_KEY` 获取。

## 验证

1. `python -m py_compile` 覆盖新增 provider/service/command。
2. smoke test 覆盖 dry-run 请求结构和 provider 输出 JSON 归一化。
3. 相关 volume self-review 测试保持通过。
