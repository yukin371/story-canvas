# review 约束消费增强计划

> 日期: 2026-04-26
> 状态: 进行中
> 范围: `README*` / `commands/review.py` / `services/story_review.py` / `tests/smoke/test_review_*.py`

## 1. 目标

1. 把根 `README.md` 调整为中文主入口
2. 保留英文 README 作为补充入口
3. 增强 `review chapter` / `review scene` 对故事约束的消费，让评审不再只盯正文启发式信号

## 2. 本轮只做什么

### 2.1 文档层

- `README.md` 作为中文主入口
- 新增 `README.en.md` 保存当前英文版说明
- 中文 README 与英文 README 互相跳转

### 2.2 评审层

优先接入以下最小约束切片：

- `project.emotionalContract`
- `worldbook.worldRules`
- `foreshadowing.foreshadows` 的当前章回收窗口
- `entities.state` / `entities.changeLog`

并把结果放到已有 review 输出中，避免新增复杂命令面。

## 3. 非目标

- 不在本轮重写评分 rubric
- 不引入新的 shared service owner
- 不把 review 变成严格证明器
- 不在本轮新增 Web UI 或桌面审查能力

## 4. 计划改动

1. 根 README 改为中文主入口，英文内容迁到 `README.en.md`
2. `build_chapter_review` 增加 story constraint signals / alignment
3. `build_scene_review` 增加情绪契约、伏笔窗口、角色状态变化信号的评审提示
4. 增加/扩展 smoke tests，确保旧字段兼容且新字段可见

## 5. 验证方式

- `python -m unittest tests.smoke.test_review_chapter tests.smoke.test_review_scene`
- 视情况补跑 `tests.smoke.test_demo_*_sample`
- 最后跑 `python -m unittest discover -s tests`

## 6. 风险

- README 双语并行维护可能漂移
- review 过度引入约束可能导致启发式评审变得噪声过多
- 旧样例项目大量缺省字段，需要保持空状态兼容
