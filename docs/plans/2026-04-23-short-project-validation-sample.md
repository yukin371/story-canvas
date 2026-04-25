# 短篇验证样例工程落地

> 日期: 2026-04-23
> 状态: 已完成

## 目标模块

- `projects/demo-short-story/*`
- `projects/demo-short-story/README.md`

## 现有 owner

- 项目结构与初始化 owner: `commands/project.py` + `protocol/*`
- 样例工程 owner: 仓库内 `demo-*` 目录

## 影响面

- 新增第二个 demo 工程，用于验证短篇生成质量与功能链路
- 不修改 CLI 接口，不新增依赖

## 计划改动

1. 用现有 CLI 初始化 `demo-short-story`
2. 回填定位层、故事契约、实体卡与 3 章短篇正文
3. 为章节补 volumes / scenePlans / 最小 machine-facing 状态
4. 跑核心命令，生成 review / projection / context 等验证工件
5. 增加项目内 README，说明验证入口

## 验证方式

- `PYTHONPATH=src python -m story_harness_cli doctor --root projects/demo-short-story`
- `PYTHONPATH=src python -m story_harness_cli chapter analyze --root projects/demo-short-story --chapter-id chapter-001`
- `PYTHONPATH=src python -m story_harness_cli chapter suggest --root projects/demo-short-story --chapter-id chapter-001`
- `PYTHONPATH=src python -m story_harness_cli review chapter --root projects/demo-short-story --chapter-id chapter-001`
- `PYTHONPATH=src python -m story_harness_cli review scene --root projects/demo-short-story --chapter-id chapter-001 --scene-index 1`
- `PYTHONPATH=src python -m story_harness_cli export --root projects/demo-short-story --format markdown`

## 需要同步的文档

- `projects/demo-short-story/README.md`
- `docs/roadmap.md`
- `docs/PROJECT_PROFILE.md`

## 架构风险

- 无新增代码 owner，主要风险在样例数据不一致

## 重复实现风险

- 禁止单独写一次性脚本模拟工作流；统一通过现有 CLI 生成样例工件

## 回滚路径

- 删除 `demo-short-story` 与本文档

## 兼容性影响

- 无 breaking change

## 验证结果

- `doctor --root projects/demo-short-story` 通过，结构检查 `errors=0`、`warnings=0`
- `chapter analyze --chapter-id chapter-001` 通过，可识别 `沈禾 / 陆川 / 沈岚 / 陈启明`
- `chapter suggest --chapter-id chapter-001` 通过，本样例当前未生成新增建议，返回 `created=0`
- `review apply --chapter-id chapter-001 --all-pending --decision accepted` 通过，空待处理队列下返回 `updated=0`
- `review chapter --chapter-id chapter-001` 通过，生成章节评分、定位层加权结果与契约对齐判断
- `review scene --chapter-id chapter-001 --scene-index 1` 通过，生成一幕级连续性、逻辑性、伏笔与回收等评分
- `projection apply --chapter-id chapter-001` 通过，本轮无待应用变更，返回 `appliedChangeRequests=0`
- `context refresh --chapter-id chapter-001` 通过，可刷新活跃角色上下文
- `export --format markdown --output projects/demo-short-story/manuscript.md` 通过，成功导出整篇稿件
- `chapter-001 ~ chapter-003` 已全部跑通 `chapter analyze`、`review chapter`、`context refresh`
- 6 个显式场景已全部跑通 `review scene`
- `python -m unittest tests.smoke.test_demo_short_story_sample -v` 通过，样例已接入自动化 smoke test
- `projects/demo-short-story/README.md`、`docs/roadmap.md`、`docs/PROJECT_PROFILE.md` 已同步为当前基线
