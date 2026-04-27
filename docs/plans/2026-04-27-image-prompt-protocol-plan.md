# Image Prompt Protocol 实施计划

> 创建日期: 2026-04-27
> 状态: 草稿
> 关联当前入口: `docs/roadmap.md`

## 一、背景

轻量生图工作台已经明确要走“模板优先 + 用户补充提示词 + 轻量多模式”路线。下一步需要把这套产品口径沉淀成协议，否则后续实现很容易把模板、风格词、商业约束散落到 UI 临时状态或命令参数里。

## 二、目标

1. 为 prompt system 建立可持久化、可复用、可回溯的协议
2. 区分项目状态层与 pack 资源层
3. 让 Story Canvas 内嵌态和未来独立在线工具共享底层协议

## 三、非目标

- 不在本轮直接改代码实现
- 不在本轮增加真实远程模板市场
- 不在本轮定义账户和计费协议

## 四、范围

### 4.1 In Scope

- `illustrations.yaml` 的 prompt system 扩展
- `prompts/illustration-packs/*.yaml` 资源协议
- template / modifier / policy / snapshot 结构
- batch / inpaint 任务层字段

### 4.2 Out of Scope

- provider 具体网络字段
- 图像二进制资产协议
- 商业后台权限模型

## 五、前置假设

- 现有 `illustrations.yaml` 继续作为项目级真相源
- 内置 builtin packs 会长期存在
- 项目自定义 pack 与 builtin packs 需要并存

## 六、实施计划

### Checkpoint A: 协议定稿

- [ ] 明确 `promptSystem` 顶层字段
- [ ] 明确 pack/template/modifier/policy 最小结构
- [ ] 明确批量与重绘任务字段

### Checkpoint B: Protocol 层接入

- [ ] 更新 `default_project_state`
- [ ] 明确旧版 `promptPack` 到 `promptSystem` 的兼容映射
- [ ] 明确项目内自定义 pack 的加载入口

### Checkpoint C: Commands / UI 消费

- [ ] `illustration config` 读写默认 pack / template
- [ ] `illustration prompt/generate` 生成 resolved prompt 快照
- [ ] UI 提供模板、modifier、额外提示词、批量和重绘入口

### Checkpoint D: 独立化预留

- [ ] 抽离 `project` 相关 targetRef 之外的通用生成字段
- [ ] 评估 `remote` pack source 的兼容结构
- [ ] 评估普通版 / 商业版 policy 的共享策略

## 七、最低验收标准

- 协议文档已经足够支撑实现阶段
- pack 资源层与项目状态层边界清晰
- 历史快照可复现原则已经落清楚

## 八、一般验收标准

- CLI、UI、未来在线工具都能共用这套协议
- 老项目可渐进迁移，不会被新协议破坏

## 九、验证计划

- 文档一致性：与 `docs/protocol/file-layout.md`、`docs/plans/2026-04-27-lightweight-image-workbench-prd.md` 保持一致
- 实现验证：TBD，待进入编码阶段

## 十、风险与回滚

### 风险

- 资源协议过于复杂会违背“轻量”目标
- 资源协议过于简单会导致商业版和独立化能力不足

### 回滚路径

- 本轮仅为协议文档，可单独回退相关文档
