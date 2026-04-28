# 2026-04-28 插画 Prompt 模板自然化与词库收敛计划

> 状态: completed
> 关联入口: `docs/roadmap.md` Track 5

## 1. 背景

- 当前插画 prompt system 已支持 `pack/template/modifier/policy`，但默认模板仍以 `visual direction:` / `user direction:` 这类标签式英语拼接为主。
- `illustration_prompting.py` 的 `subject` 也偏命令式说明句，容易把系统提示感直接带进最终 prompt。
- 角色设定图与章节插图缺少可复用的视觉词库层，用户只能靠 modifier 或额外补充 prompt 手工堆词，导致风格不稳定、AI 感偏重。

## 2. 目标

1. 优化插画与设定图的默认模板，让 resolved prompt 更自然、更接近真人美术 brief。
2. 在 prompt pack 协议内增加可复用词库/短语库，避免把视觉表达继续散落到模板和命令层。
3. 保持旧 pack 与现有 CLI 参数兼容，不新增并行真相源，不引入第三方依赖。

## 3. 适用规则

- 当前执行入口：`docs/roadmap.md` Track 5 生图能力并行推进。
- Canonical owner：
  - prompt pack 协议与 builtin pack 在 `src/story_harness_cli/protocol/prompt_packs.py`
  - prompt 组装在 `src/story_harness_cli/services/illustration_prompting.py`
  - CLI 参数与状态写回在 `src/story_harness_cli/commands/illustration.py`
- 架构不变量：
  - `protocol/` 负责 pack schema、默认值和兼容加载
  - `services/` 只做纯函数式 prompt 解析与组装
  - `.yaml` 仍为 JSON-compatible
- 兼容性约束：
  - 不改 `illustration prompt/generate` 对外参数
  - 旧 pack 缺少新字段时必须继续可用
  - `promptSnapshot/policySnapshot` 结构不能破坏现有消费方

## 4. 计划改动

### 4.1 Protocol

- 为 prompt pack 增加可选 `lexicon` 结构，承载：
  - `subjectPhrases`
  - `detailPhrases`
  - `negativePhrases`
  - 必要的 use case / mode 定向短语
- 更新 builtin packs：
  - 默认包、轻小说包、连载包的角色/场景模板改成更自然的叙述型模板
  - 为角色设定图与章节场景图补一批更贴近插画 brief 的词库片段
- 扩展 pack 规范化和序列化，保证旧 pack 缺字段时安全回退。

### 4.2 Services

- 在 `illustration_prompting.py` 增加词库解析与自然化拼装 helper。
- 角色设定图：
  - 强化外貌锚点、服饰、职业气质、材质与镜头短语
  - 去掉过强的系统命令腔
- 章节场景图：
  - 保留“不直接塞正文”的边界
  - 改成更像美术 brief 的场景、情绪、光影、构图表达
- 保持 `promptSnapshot` 可复现，同时让 `resolvedPrompt` 更自然。

### 4.3 Commands / Tests / Docs

- 只在必要处调整命令层对 pack summary 或 dry-run 输出的兼容字段。
- 补 smoke tests：
  - builtin pack 词库与模板自然化输出
  - project custom pack 新字段归一化
  - 旧 pack 继续兼容
- 同步协议文档和相关 `MODULE.md`。

### 4.4 Export / Customize 闭环

- 提供 `illustration pack-export`，把 builtin/default pack 克隆到 `prompts/illustration-packs/*.yaml`
- 提供 UI API 导出入口，避免前端自己复制系统模板
- 支持导出后直接设为项目默认 pack，形成：
  - 导出 builtin/default pack
  - 本地编辑模板与词库
  - 必要时运行 `illustration pack-migrate`
  - 继续被 `illustration prompt/generate` 消费

## 5. 验证计划

- `PYTHONPATH=src python -m unittest tests.smoke.test_prompt_packs`
- `PYTHONPATH=src python -m unittest tests.smoke.test_illustration_command`
- 如无额外失败，再视情况补 `PYTHONPATH=src python -m unittest discover -s tests`

## 6. 风险与回滚

- 风险：
  - 词库字段设计过重，导致 project pack 编辑复杂化。
  - prompt 过度自然化后，丢失原有可控性或商业模式约束表达。
- 回滚路径：
  - 协议层改动集中在 `prompt_packs.py` 与 `illustration_prompting.py`，可整体回退到旧模板与旧解析逻辑。

## 7. 完成情况

- 已完成：
  - builtin pack 自然化模板与 `lexicon` 收敛
  - legacy template 自动迁移
  - CLI `illustration pack-migrate`
  - UI API `/api/prompt-packs/migrate`
  - CLI `illustration pack-export`
  - UI API `/api/prompt-packs/export`
  - smoke tests 与协议文档同步
