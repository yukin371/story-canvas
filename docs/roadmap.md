# 当前路线图

> 最后更新: 2026-04-24
> 状态: 当前唯一执行入口

## 1. 当前版本目标

- v0.2: 修复已知缺陷 + 补齐空壳功能 + 工程质量提升 — **全部完成**

## 2. Active Tracks

### Track P0: 修复 entity enricher 实体归属

- 目标: 同段落多实体时，外貌/能力属性错配给后出现的实体
- 当前状态: **已完成** — 按句子粒度归属标签
- 下一步: 无

### Track P1: 补齐空壳功能

- 目标: timeline 管理、causality 追踪、search 跨章节搜索
- 当前状态: **已完成** — timeline、search、causality 全部落地
- 下一步: 无

### Track P2: 工程质量

- 目标: CI/CD (GitHub Actions)、lint (ruff)、entity 注册自动化
- 当前状态: **已完成** — CI workflow、ruff 配置、entity 自动注册均已落地
- 下一步: 无

### Track P3: 体验优化

- 目标: 导出格式扩展、relationship graph、beat 追踪、配置化关键词表
- 当前状态: **已完成** — 四项全部落地
- 下一步: 无

## 3. 当前阻塞

- SSL 问题导致 `pip install -e .` 失败（镜像证书）:
  - 影响: 无法通过 `story-harness` 命令直接运行
  - 解除路径: 使用 `PYTHONPATH=src python -m story_harness_cli` 替代

## 4. 待验证项

- 长篇小说项目端到端验证
- adapters/ 目录的实际使用情况
- 更多商业化长篇题材样例

## 5. 最近进展

- 修复 entity enricher 跨实体属性错配（P0）
- 新增 timeline add/list/check 命令（P1）
- 新增 search 跨章节搜索命令（P1）
- 新增 causality 追踪命令（P1）
- GitHub Actions CI workflow (test/lint/commit-governance)（P2）
- ruff lint/format 配置（P2）
- chapter analyze 自动注册 inferred entities（P2）
- export --format json/markdown/txt 多格式导出（P3）
- entity graph --format mermaid/dot 关系图导出（P3）
- outline beat-add/beat-complete/beat-list 细纲追踪（P3）
- keywords.yaml 配置化关键词表（P3）
- review chapter 章节回顾评分与改稿建议
- 新增按类型组织的小说评审标准表文档
- project.yaml 新增 positioning / storyContract 初始化支持
- project.yaml 新增 commercialPositioning 商业连载蓝图支持
- doctor / review chapter 已接入定位层与故事契约基础检查
- doctor 已接入商业连载蓝图检查与项目级章节字数目标
- review chapter 已接入商业平台加权与章节级 commercial alignment 输出
- review scene 已接入一幕级 commercial alignment 输出
- 章节 review 相关 smoke test 已补齐
- review scene 已支持按段落范围评一幕的连续性、逻辑、伏笔与场景功能
- outline scene-add / scene-list 已支持显式维护章节场景边界，review scene 会优先读取 scenePlans
- outline scene-update / scene-remove 已补齐，scenePlans 已具备最小可维护闭环
- outline scene-detect 已支持把启发式候选场景落成显式 scenePlans，便于后续维护
- review scene 已接入一幕级 contract alignment 输出
- 新增 `demo-short-story` 短篇验证工程，已跑通章节分析、章节/一幕评审、上下文刷新与导出链路
- 新增 `demo-light-novel-short` 风格驱动短篇样例，已验证 `fantasy + western-fantasy + light-novel` 的定位层输出
- 新增 `demo-xuanhuan-short` 玄幻网文短篇样例，已验证 `fantasy + xuanhuan + web-serial` 的定位层输出
- 新增 `demo-urban-occult-long` 商业化网站连载长篇样例，已验证长篇项目结构、卷级骨架、章节评审与一幕评审链路
- `demo-urban-occult-long` 已完成卷一 `chapter-012`，并跑通 analyze / review / context / doctor / export 闭环
- `projects/demo-urban-occult-long/chapter-001` 到 `chapter-008` 已回补到商业最低字数线，其中 `chapter-002` 到 `chapter-012` 里已有 11 章达到建议字数线，卷一前半短章缺口已清零

## 6. 下一步

- v0.2 发布准备
- 基于 `demo-short-story` 固化短篇回归基线，基于 `demo-urban-occult-long` 固化已收口的商业长篇卷一基线，并评估是否继续卷二写作或精修 `chapter-001`
- 继续补更多网文题材样例，形成“短篇回归 + 长篇商业样例”矩阵
- 收集使用反馈，规划 v0.3
