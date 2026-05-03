# 综合审查系统使用指南

> Date: 2026-04-30
> 功能: 实体资产自动包裹 + 全面审查AI系统

---

## 核心理念

### AI协作模式

**写作Agent职责：**
1. **构建资产库**：设定、角色卡、势力、伏笔等完整资产
2. **纯文本写作**：专注于创作，不需要手动添加@{}
3. **补充资产**：根据审查反馈补充缺失的实体资产

**审查AI职责：**
1. **实体检查**：发现未知实体，建议Agent补充
2. **逻辑审查**：检查前后文矛盾、行为一致性、因果关系
3. **爽点分析**：识别爽点类型、分布、强度
4. **结构分析**：检查3幕/5幕、卷级闭环、剧情节奏

**系统自动化：**
1. **自动包裹**：基于Agent构建的资产库自动添加@{}
2. **减少手工**：最大化自动化，减少重复劳动

---

## 完整工作流

### 阶段1: 资产构建（写作Agent）

Agent先构建完整的实体资产库：

```yaml
# entities/characters/protagonist.yaml
id: char-protagonist
name: 张三
kind: character
aliases:
  - 张三
  - 主角
brief: 夜班接尸人，继承了城隍夜巡牌
status: active

# entities/factions/heavenly-sword.yaml
id: faction-heavenly-sword
name: 天剑阁
kind: faction
aliases:
  - 天剑阁
  - 天剑
brief: 正道门派，以剑修闻名
```

### 阶段2: 章节写作（写作Agent）

Agent纯文本写作，不需要添加@{}：

```markdown
# chapters/chapter-001.md

张三走在幽京城的街道上，突然感到一股寒意。他停下脚步，环顾四周，发现有个黑衣人在跟踪他。

"你是谁？"张三问道。

黑衣人没有回答，反而加快了脚步。张三心中警觉，握紧了手中的接尸符。
```

### 阶段3: 自动包裹（系统命令）

```bash
# 自动为已知实体添加@{}包裹
story-canvas writing auto-wrap --chapter-id chapter-001
```

输出：

```
=== 自动包裹报告 ===
章节: chapter-001
共包裹 4 处实体引用

character: 3 处
  - 张三 (匹配为: 张三)
  - 张三 (匹配为: 张三)
  - 主角 (匹配为: 张三)

location: 1 处
  - 幽京城 (匹配为: 幽京城)
```

结果文本：

```markdown
@{张三}走在@{幽京城}的街道上，突然感到一股寒意。@{张三}停下脚步，环顾四周，发现有个黑衣人在跟踪他。

"你是谁？"@{张三}问道。

黑衣人没有回答，反而加快了脚步。@{张三}心中警觉，握紧了手中的接尸符。
```

### 阶段4: 综合审查（审查AI）

```bash
# 全面综合审查
story-canvas review-comprehensive --root ./my-novel --chapter-id chapter-001
```

输出示例：

```
=== 综合审查报告 ===

章节: chapter-001
审查时间: 2026-04-30T10:30:00Z
审查范围: entities, logic, satisfaction, structure

=== 总体评估 ===
总分: 12.5/15
可继续下一章: 是
⚠️  重要问题: 2 个

=== 分项评分 ===
  实体完整性: 10/15
    发现3个未知实体
  逻辑一致性: 13/15
    无明显矛盾
  爽点设计: 12/15
    共3个爽点
  结构完整性: 15/15
    结构完整

=== 实体审查 ===

已知实体: 5 个
已包裹: 5 个

发现未知实体: 3 个

未知实体详情:
  名称: 李四的师父
  预测类型: character
  出现次数: 3
  优先级: high
  建议: 补充character资产
  上下文: 在第5章提到，是主角的引路人，传授了基础功法...
  必需字段: 姓名, 身份, 外貌特征, 性格特点, 背景故事

  名称: 天剑阁
  预测类型: faction
  出现次数: 2
  优先级: medium
  建议: 补充faction资产
  上下文: 在第8章提到，是正道门派之一，与主角有冲突...
  必需字段: 势力名称, 势力目标, 现任领袖, 主要成员, 与其他势力的关系

=== 改进建议 ===

【P0-紧急】补充高优先级实体：
  - 李四的师父: 补充character资产
  - 天剑阁: 补充faction资产

【P1-重要】修正重要问题：
  - 第3段情绪状态前后不一致

=== 总体摘要 ===

章节质量良好，发现3个需要补充的实体，建议补充后继续下一章
```

### 阶段5: 补充资产（写作Agent）

Agent根据审查建议补充资产：

```yaml
# entities/characters/mentor.yaml
id: char-mentor
name: 李玄道
kind: character
aliases:
  - 李玄道
  - 师父
  - 李四的师父
brief: 天剑阁执事长老，主角的引路人，传授基础接尸功法
```

```yaml
# entities/factions/heavenly-sword.yaml
id: faction-heavenly-sword
name: 天剑阁
kind: faction
aliases:
  - 天剑阁
  - 天剑
brief: 正道门派，以剑修闻名，与魔道势不两立
goal: 维护正道秩序，消灭魔道
leader: 李玄道（执事长老）
members: [张三（外门弟子）]
```

### 阶段6: 重新包裹

```bash
# 重新执行自动包裹（现在包含了新实体）
story-canvas writing auto-wrap --chapter-id chapter-001
```

---

## 命令参考

### 自动包裹命令

```bash
# 自动包裹所有已知实体
story-canvas writing auto-wrap --root ./my-novel --chapter-id chapter-001

# 预览包裹结果（不实际修改）
story-canvas writing auto-wrap --root ./my-novel --chapter-id chapter-001 --dry-run
```

### 综合审查命令

```bash
# 全面审查（所有区域）
story-canvas review-comprehensive --root ./my-novel --chapter-id chapter-001

# 只审查实体
story-canvas review-comprehensive --root ./my-novel --chapter-id chapter-001 --focus entities

# 只审查逻辑
story-canvas review-comprehensive --root ./my-novel --chapter-id chapter-001 --focus logic

# 只审查爽点
story-canvas review-comprehensive --root ./my-novel --chapter-id chapter-001 --focus satisfaction

# 只审查结构
story-canvas review-comprehensive --root ./my-novel --chapter-id chapter-001 --focus structure

# 商业严格模式
story-canvas review-comprehensive --root ./my-novel --chapter-id chapter-001 --strictness commercial

# JSON格式输出（便于脚本处理）
story-canvas review-comprehensive --root ./my-novel --chapter-id chapter-001 --format json
```

---

## 实体补充建议示例

### 审查AI发现的未知实体

```json
{
  "name": "李四的师父",
  "predictedType": "character",
  "context": "在第5章提到，是主角的引路人，传授了基础功法，似乎与天剑阁有关",
  "occurrenceCount": 3,
  "priority": "high",
  "suggestedAction": "补充character资产",
  "requiredFields": [
    "姓名（不能只用"李四的师父"这种指代）",
    "身份（门派、职位）",
    "外貌特征",
    "性格特点",
    "背景故事",
    "与主角关系"
  ]
}
```

### Agent如何补充

**方法1: 创建角色卡**

```bash
story-canvas entity create \
  --name "李玄道" \
  --kind character \
  --brief "天剑阁执事长老，主角的引路人" \
  --aliases "李玄道,师父,执事长老"
```

**方法2: 编辑YAML文件**

编辑 `entities/characters/mentor.yaml`:

```yaml
id: char-mentor
name: 李玄道
kind: character
aliases:
  - 李玄道
  - 师父
  - 执事长老
brief: 天剑阁执事长老，主角的引路人，传授基础接尸功法
personality:
  - 正直
  - 严厉
  - 关心主角
background: |
  曾是主角父亲李四的挚友，在李四失踪后承担起引路人的责任。
  发现主角的接尸天赋后，决定传授他基础的接尸功法。
```

---

## 审查AI的全面编辑功能

### 1. 实体检查

**检查内容：**
- 已知实体是否正确使用
- 发现文本中的未知实体
- 提供补充建议

**输出示例：**
```
发现未知实体: 3 个
  - 李四的师父 (character, high priority)
  - 天剑阁 (faction, medium priority)
  - 接尸符 (item, low priority - 可能已在设定库中)
```

### 2. 逻辑一致性检查

**检查内容：**
- 前后文矛盾
- 角色行为一致性
- 因果关系合理性
- 设定遵循

**输出示例：**
```
评分: 13/15
问题: 1 个警告
  ⚠️ 第3段情绪状态前后不一致
     建议: 补充情绪转变的过渡描写
```

### 3. 爽点分析

**爽点类型：**
- `face_slap`: 打脸（误解纠正、真相揭露）
- `show_off`: 装逼（展现实力、震惊全场）
- `reversal`: 反转（意外转折）
- `gain`: 获得（获得功法、物品、突破）

**分析维度：**
- 爽点数量和分布
- 爽点强度
- 商业契约履行
- 结尾钩子质量

**输出示例：**
```
评分: 12/15
爽点数量: 3 个
分布: {face_slap: 1, show_off: 1, gain: 1}
密度: 适中
商业契约履行: ✓
结尾钩子质量: high

改进建议:
  爽点密度较低，建议增加主角展示实力或剧情反转的情节
```

### 4. 结构分析

**检查内容：**
- 3幕/5幕结构
- 卷级闭环
- 剧情节奏

**输出示例：**
```
评分: 15/15

3幕结构:
  第一幕（铺垫）: 1-5
  第二幕（冲突）: 6-15
  第三幕（结局）: 16-20

卷级闭环: ✓ 可以结束
剧情节奏: balanced
```

---

## 最佳实践

### 1. 资产构建优先级

**必需资产（P0）：**
- 主角完整角色卡
- 主要反派角色卡
- 核心势力设定
- 世界基础规则

**重要资产（P1）：**
- 配角角色卡
- 次要势力设定
- 主要地点设定

**可选资产（P2）：**
- 次要角色
- 次要地点
- 特殊物品

### 2. 写作流程建议

```bash
# 写作前准备
story-canvas setting assess      # 检查设定完备性
story-canvas setting expand       # 扩展设定（如需要）

# 写作阶段
# Agent写作纯文本...

# 写作后处理
story-canvas writing auto-wrap   # 自动包裹
story-canvas review-comprehensive # 综合审查

# 根据审查结果
# Agent补充资产 → 重新auto-wrap → 下一章
```

### 3. 审查驱动的资产完善

**循环流程：**
1. 写作 → 审查 → 发现缺失实体
2. 补充实体 → 重新审查 → 通过
3. 继续写作

**好处：**
- 确保资产库与内容同步
- 避免后期设定矛盾
- 发现遗漏的重要角色/势力

---

## 常见问题

### Q1: 自动包裹会误判吗？

**A:** 可能会有以下情况：
- 同名不同实体（如"两个张三"）
- 代词歧义（"他"指代谁）
- 专有名词误判（如"明天"被当作实体名）

**解决方案：**
- 使用唯一的标准名称
- 预览模式（--dry-run）检查结果
- 手动编辑修正误判

### Q2: 审查AI的实体类型预测准确吗？

**A:** 准确率约70-80%，建议：
- 高优先级实体重点检查
- 中低优先级实体可选补充
- 结合上下文判断

### Q3: 需要补充所有发现的实体吗？

**A:** 不需要。只补充：
- 出现3次以上的实体
- 主剧情相关的实体
- 影响设定的实体

忽略：
- 一次性背景角色
- 纯装饰性描述
- 已知实体别名

### Q4: 如何处理同名实体？

**A:** 建议：
- 使用不同的标准名称
- 添加别名区分
- 在资产库中明确说明

---

## 总结

这个系统的核心价值：

1. **Agent主导**：资产构建和写作都是Agent负责
2. **自动高效**：系统自动处理技术细节
3. **审查增值**：发现真正的问题，促进资产完善
4. **严格编辑**：全面的编辑视角，不仅是格式检查

正确的流程：
- Agent构建资产 → Agent写作 → 系统自动包裹 → 审查AI发现问题 → Agent补充资产 → 继续创作
