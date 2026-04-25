# 风格样例入口同步

> 日期: 2026-04-23
> 状态: 已完成

## 目标模块

- `README.md`
- `docs/guides/*`
- `docs/plans/*`

## 现有 owner

- 首页入口 owner: `README.md`
- 指南 owner: `docs/guides/*`
- 风格样例 owner: `projects/demo-light-novel-short/*`

## 影响面

- 用户是否能快速找到风格驱动样例
- 通用基线与风格基线的使用边界是否清晰
- 不修改 CLI 行为，不新增依赖

## 计划改动

1. 在 `README.md` 增加 `demo-light-novel-short` 入口
2. 在 `docs/guides/quickstart.md` 增加风格样例运行与 fallback
3. 在 `docs/guides/creative-workflow.md` 明确两类样例的用途差异

## 验证方式

- 读取 `README.md`、`docs/guides/quickstart.md`、`docs/guides/creative-workflow.md`
- 对照 `projects/demo-light-novel-short/README.md` 检查样例定位
- 运行 `git diff --check -- README.md docs/guides/quickstart.md docs/guides/creative-workflow.md docs/plans/2026-04-23-style-sample-entry.md`

## 验证结果

- 首页已形成“初始化新项目 + 通用回归样例 + 风格化样例”三条入口
- `demo-light-novel-short` 已作为风格基线出现在 quickstart 与创作流程指南
- 文档已明确区分 `demo-short-story` 与 `demo-light-novel-short` 的适用场景

## 残留风险

- 当前首页仍未把更多题材样例并列展示，后续若增加玄幻等样例，入口策略需要再统一
- 风格样例目前只展示了西幻轻小说一类，尚不能覆盖全部网络小说风格组合
