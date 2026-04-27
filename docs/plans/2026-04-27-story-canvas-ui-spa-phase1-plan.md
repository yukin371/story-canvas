# Story Canvas UI SPA 收敛计划

> 创建日期: 2026-04-27
> 状态: 进行中
> 关联当前入口: `docs/roadmap.md`

## 一、背景

Early UI 已接入真实项目 summary 与插画 dry-run，但现有视觉语言还没有形成统一规则，生图前置配置也缺少显式入口。为避免继续在不稳定样式基础上叠加功能，本轮先收敛设计，再补齐设置页与配置告警。

## 二、目标

1. 建立统一 UI 设计入口 `ui/design.md`
2. 用 PRD 和计划明确这轮 SPA 收敛方向
3. 完成一轮 App / Chapters / Illustration / Settings 的工作台化收敛

## 三、非目标

- 不接入新的 CLI 动作
- 不在本轮加入正文编辑器

## 四、范围

### 4.1 In Scope

- `ui/design.md`
- `ui/src/App.vue`
- `ui/src/views/*.vue`
- `ui/src/styles.css`
- `scripts/story_canvas_ui_api.py`
- `src/story_harness_cli/commands/illustration.py`
- UI 相关文档同步

### 4.2 Out of Scope

- 新增前端状态持久化

## 五、前置假设

- 允许为工作台补充最小本地设置 API，但不引入新的项目协议真相源
- 单页应用仍是当前合适形态，无需切成多入口

## 六、实施计划

### Checkpoint A

- [x] 明确 UI 视觉规则入口
- [x] 形成 UI PRD
- [x] 形成 dated implementation plan

### Checkpoint B

- [x] 收敛应用壳层，减少品牌文案和装饰性样式
- [x] 重排概览页为更接近 TDesign 工作台的结构
- [x] 调整章节与审查页，延续统一卡片和列表体系

### Checkpoint C

- [x] 调整插画工作台样式和信息层级
- [x] 统一全局圆角、边框、阴影和说明文字策略
- [x] 接入设置页与生图配置缺失告警
- [x] 执行前端 build 验证并记录残留风险

## 七、验收标准

### 最低验收标准

- `ui/design.md`、PRD、plan 已落盘
- UI 仍为单页应用
- 插画工作区在缺 key / provider 时能提前告警
- `npm run build` 通过

### 一般验收标准

- 审查、插画、设置页视觉风格明显统一
- 大圆角和副标题文本明显减少
- 页面看起来接近 TDesign 工作台，而非品牌落地页

## 八、验证计划

- Lint: `vue-tsc --noEmit`
- Test: N/A（当前 UI 未配置独立单测）
- Build: `npm run build`
- Security: 本地 secret 仅允许进入工作台私有配置，不进入项目协议

## 九、风险与回滚

### 风险

- 本地 secret 配置引入后，需要持续保证其不被写入项目协议
- 若样式改动过大，可能牵连审查 / 插画 / 设置三页同时回归

### 回滚路径

- 回退 `ui/`、`scripts/story_canvas_ui_api.py`、`src/story_harness_cli/commands/illustration.py` 与本轮 UI 文档

## 十、文档同步

- `ui/MODULE.md`
- `ui/design.md`
- `docs/plans/2026-04-27-story-canvas-ui-spa-prd.md`
- `docs/plans/2026-04-27-story-canvas-ui-spa-phase1-plan.md`
