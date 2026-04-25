# 首页与指南样例入口对齐

> 日期: 2026-04-23
> 状态: 已完成

## 目标模块

- `README.md`
- `docs/guides/*`
- `docs/plans/*`

## 现有 owner

- 首页入口 owner: `README.md`
- 指南 owner: `docs/guides/*`
- 计划记录 owner: `docs/plans/*`

## 影响面

- 新用户首次体验路径
- 文档中的“新建项目”与“直接跑样例”两条入口
- 不修改 CLI 行为，不新增依赖

## 计划改动

1. 在 `README.md` 中增加 `demo-short-story` 样例入口
2. 保留“初始化新项目”路径，同时补“直接跑已验证样例”路径
3. 在 `docs/guides/quickstart.md` 中同步样例基线入口与 fallback

## 验证方式

- 读取 `README.md` 与 `docs/guides/quickstart.md`
- 对照 `projects/demo-short-story/README.md` 与 `docs/roadmap.md` 确认样例定位
- 运行 `git diff --check -- README.md docs/guides/quickstart.md docs/plans/2026-04-23-sample-entry-alignment.md`

## 验证结果

- `README.md` 已同时提供“初始化新项目”与“运行已验证样例”两条入口
- `demo-short-story` 已作为更通用的短篇回归基线出现在首页与 quickstart
- `docs/guides/quickstart.md` 已补充 `demo-short-story` 的直接运行方式与 fallback

## 残留风险

- `demo-light-novel-short` 仍是风格驱动样例，但当前未在首页作为并列入口展示
- 文档中仍存在 `.\\demo` 作为“新建项目示例名”，需要读者区分“自建项目”和“仓库样例项目”
