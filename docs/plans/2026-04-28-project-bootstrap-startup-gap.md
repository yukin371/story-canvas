# 2026-04-28 项目起步闭环缺口修补

## 背景

按 `docs/guides/quickstart.md` 与 `docs/guides/creative-workflow.md` 实测新建项目流程，发现“AI 不知道怎么开始”不是单纯提示词问题，而是当前 CLI 起步链路存在真实摩擦与误导：

1. `init` 后没有直接给出下一步命令链。
2. `status` / `outline check` 只返回抽象 `nextActions`，缺少可执行命令建议。
3. `init` 生成的默认章节占位文案会被后续实体/scene 检测当成正文。
4. `outline scene-detect` 会把初始化占位文案识别成有效 `scenePlans`，导致 `outline check` 假通过。
5. 在假通过前提下，`chapter analyze` / `review chapter` 会继续消费占位稿，形成伪闭环。

## 适用规则

- 当前执行入口：`docs/roadmap.md`
- 架构护栏：CLI 编排归 `commands/`，纯检测逻辑归 `services/`
- 不变量：
  - `services/` 不做文件 I/O
  - 新命令注册规则不变
  - 不引入新的并行真相源
  - `scenePlans` 现阶段仍是带段落边界的显式结构，不能随意改成另一套协议

## 目标

以最小改动修补“新项目起步”风险：

1. 默认章节 stub 不再污染实体/scene 检测。
2. `init` / `status` / `outline check` / workflow 相关输出要能直接提示 AI 下一条命令。
3. `scene-detect` 不再把 bootstrap 占位内容当成真实场景。

## 非目标

- 本轮不重做 `scenePlans` 协议。
- 本轮不新增大型 workflow 子系统。
- 本轮不把卷级闭环与人工审查规则一起改动。

## 验证

1. 新建临时项目后，`status` 能给出可执行下一步建议。
2. 新建临时项目后，`outline scene-detect` 不应从默认 stub 生成 scene。
3. `outline check` 不应因 bootstrap 文案而误判 ready。
4. 相关 smoke tests 补齐并通过。
