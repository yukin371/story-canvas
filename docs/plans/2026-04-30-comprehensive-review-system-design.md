# Story Canvas 综合审查系统设计

> Date: 2026-04-30
> Status: Design
> Scope: 实体资产自动包裹 + 全面审查AI系统

---

## 1. 核心理念

### 1.1 AI协作模式

**写作Agent（创作AI）职责：**
- 构建完整资产库：设定、角色卡、势力、伏笔等
- 纯文本写作，专注于创作内容
- 根据审查反馈补充资产

**审查AI（编辑AI）职责：**
- 严格的编辑视角，全面检查小说质量
- 发现实体资产缺失，建议Agent补充
- 检查逻辑、爽点、结构、闭环等编辑问题

**系统自动化：**
- 基于Agent构建的资产库自动添加@{}包裹
- 减少手工操作，提升创作效率

### 1.2 完整工作流

```
┌─────────────────────────────────────────────────────┐
│  阶段1: 资产构建（写作Agent）                         │
│  构建设定库、角色卡、势力库、伏笔规划 → 完整实体库      │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  阶段2: 章节写作（写作Agent）                         │
│  纯文本创作，使用实体名称                             │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  阶段3: 自动包裹（系统命令）                          │
│  基于实体库自动添加@{}包裹                            │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  阶段4: 综合审查（审查AI）                            │
│  ✓ 实体检查（发现缺失，建议补充）                      │
│  ✓ 逻辑一致性检查                                    │
│  ✓ 爽点分析                                         │
│  ✓ 结构分析（3幕/5幕、卷级闭环）                       │
│  ✓ 其他编辑问题                                     │
└─────────────────────────────────────────────────────┘
                        ↓
              发现问题？
             ↙           ↘
          是              否
          ↓                ↓
┌─────────────────┐   继续下一章
│ 阶段5: 补充资产   │
│ (写作Agent)     │
│ 根据审查建议     │
│ 补充角色卡       │
│ 补充势力设定     │
│ 修正逻辑问题     │
│ 调整爽点节奏     │
└─────────────────┘
          ↓
      回到阶段2
```

---

## 2. 实体资产自动包裹系统

### 2.1 设计目标

- **基于已知资产库**：不是自动识别新实体，而是为已知实体添加@{}
- **智能匹配**：处理别名、简称、指代等多种情况
- **可配置**：支持不同类型实体的包裹策略
- **可逆操作**：记录包裹历史，支持撤销

### 2.2 实体资产库结构

```yaml
# entities/characters/protagonist.yaml
id: char-protagonist
name: 张三
aliases:
  - 张三
  - 主角
  - 他
kind: character
brief: 主角，夜班接尸人
status: active

# entities/factions/righteous.yaml
id: faction-righteous
name: 正道联盟
aliases:
  - 正道联盟
  - 正道
  - 盟主
kind: faction
brief: 正派势力联合体

# worldbook/locations.yaml
locations:
  - id: loc-city
    name: 幽京城
    aliases:
      - 幽京城
      - 京城
      - 城
    kind: city
```

### 2.3 自动包裹算法

**步骤1：构建实体索引**
```python
def build_entity_index(state: Dict[str, Any]) -> Dict[str, EntityIndex]:
    """构建实体名称索引"""
    index = {
        "canonical_names": {},  # 标准名称 -> 实体
        "aliases": {},          # 别名 -> 实体
        "pronouns": {},         # 代词 -> 上下文实体
    }

    # 遍历所有实体资产
    for entity in load_all_entities(state):
        # 添加标准名称
        index["canonical_names"][entity.name] = entity

        # 添加别名
        for alias in entity.aliases:
            index["aliases"][alias] = entity

        # 添加代词（需要上下文判断）
        if entity.kind == "character":
            index["pronouns"][entity.pronoun] = entity

    return index
```

**步骤2：智能匹配与包裹**
```python
def auto_wrap_entities(
    chapter_text: str,
    entity_index: Dict[str, EntityIndex],
    context: Dict[str, Any]
) -> Tuple[str, List[WrapResult]]:
    """自动包裹实体"""

    # 1. 识别句子边界，避免跨句匹配
    sentences = split_sentences(chapter_text)

    # 2. 为每个句子进行实体匹配
    wrapped_sentences = []
    wrap_results = []

    for sentence in sentences:
        # 获取当前活跃实体（上下文）
        active_entities = get_active_entities(context)

        # 匹配实体名称
        matched = match_entities_in_sentence(
            sentence,
            entity_index,
            active_entities
        )

        # 添加@{}包裹
        wrapped_sentence = apply_wraps(sentence, matched)

        wrapped_sentences.append(wrapped_sentence)
        wrap_results.extend(matched)

    return "\n".join(wrapped_sentences), wrap_results
```

**步骤3：处理特殊情况**
- **避免重复包裹**：检查已经包裹的实体
- **处理嵌套引用**：如"@{张三}的剑"
- **处理指代消歧**：上下文中的"他"指代谁
- **保留特殊格式**：对话、诗词等不处理

### 2.4 命令接口

```bash
# 自动包裹所有已知实体
story-canvas writing auto-wrap --chapter-id chapter-001

# 预览包裹结果（不实际修改）
story-canvas writing auto-wrap --chapter-id chapter-001 --dry-run

# 查看包裹历史
story-canvas writing wrap-history --chapter-id chapter-001

# 撤销上次包裹
story-canvas writing wrap-undo --chapter-id chapter-001
```

---

## 3. 审查AI的实体检查功能

### 3.1 检查内容

**检查1：已知实体规范性**
- 实体库中的实体是否正确使用
- 实体引用是否符合设定
- @{}包裹是否完整
- 实体关系是否符合资产库定义

**检查2：未知实体发现**
- 发现文本中提到但资产库中没有的实体
- 区分"需要补充"和"不需要补充"的情况
- 提供实体分类建议（character/faction/location/item）
- 评估补充优先级

### 3.2 未知实体识别算法

```python
def detect_unknown_entities(
    chapter_text: str,
    entity_index: Dict[str, EntityIndex],
    nlp_engine: Any
) -> List[UnknownEntity]:
    """检测未知实体"""

    unknown_entities = []

    # 1. 分词与命名实体识别
    tokens = nlp_engine.tokenize(chapter_text)
    named_entities = nlp_engine.extract_named_entities(tokens)

    # 2. 过滤已知实体
    for entity in named_entities:
        if not is_known_entity(entity, entity_index):
            # 3. 判断是否需要补充到资产库
            if should_track_as_asset(entity):
                unknown_entities.append({
                    "name": entity.text,
                    "type": predict_entity_type(entity, context),
                    "context": extract_context(entity, chapter_text),
                    "frequency": count_occurrences(entity, chapter_text),
                    "priority": calculate_priority(entity),
                    "suggestion": generate_suggestion(entity)
                })

    return unknown_entities
```

### 3.3 实体类型预测

基于上下文预测实体类型：

```python
def predict_entity_type(entity: NamedEntity, context: str) -> str:
    """预测实体类型"""

    # 角色特征
    character_patterns = [
        "说", "道", "想", "觉得", "看着", "走向",
        "剑", "刀", "武功", "内力"
    ]

    # 势力特征
    faction_patterns = [
        "门派", "盟", "宗", "教", "帮", "阁", "派",
        "弟子", "长老", "掌门"
    ]

    # 地点特征
    location_patterns = [
        "山", "城", "殿", "阁", "室", "谷", "峰",
        "来到", "进入", "离开", "位于"
    ]

    # 物品特征
    item_patterns = [
        "剑", "刀", "丹药", "功法", "秘籍", "符",
        "拿着", "佩戴", "使用", "炼制"
    ]

    # 统计上下文匹配
    character_score = sum(1 for p in character_patterns if p in context)
    faction_score = sum(1 for p in faction_patterns if p in context)
    location_score = sum(1 for p in location_patterns if p in context)
    item_score = sum(1 for p in item_patterns if p in context)

    # 返回得分最高的类型
    scores = {
        "character": character_score,
        "faction": faction_score,
        "location": location_score,
        "item": item_score
    }

    return max(scores, key=scores.get)
```

### 3.4 审查输出格式

```json
{
  "entityReview": {
    "knownEntityCompliance": {
      "score": 15,
      "totalEntities": 8,
      "wrappedEntities": 7,
      "unwrappedEntities": 1,
      "issues": [
        {
          "entityId": "char-protagonist",
          "entityName": "张三",
          "issue": "在第3段未使用@{}包裹",
          "suggestion": "系统自动包裹应处理此问题"
        }
      ]
    },
    "unknownEntityDiscovery": {
      "discoveredCount": 3,
      "entities": [
        {
          "name": "李四的师父",
          "predictedType": "character",
          "context": "在第5章提到，是主角的引路人，传授了基础功法",
          "occurrenceCount": 3,
          "priority": "high",
          "suggestedAction": "补充角色卡",
          "requiredFields": [
            "姓名",
            "身份（门派、职位）",
            "外貌特征",
            "性格特点",
            "与主角关系"
          ]
        },
        {
          "name": "天剑阁",
          "predictedType": "faction",
          "context": "在第8章提到，是正道门派之一，与主角有冲突",
          "occurrenceCount": 2,
          "priority": "medium",
          "suggestedAction": "补充势力设定",
          "requiredFields": [
            "势力目标",
            "现任领袖",
            "主要成员",
            "与其他势力的关系",
            "地理位置"
          ]
        }
      ]
    }
  }
}
```

---

## 4. 审查AI的全面编辑功能

### 4.1 逻辑一致性检查

**检查维度：**

1. **前后文矛盾**
   - 前文说A是好人，后文说A是坏人
   - 前文说道具在甲地，后文突然在乙地
   - 时间线错乱

2. **角色行为一致性**
   - 角色性格前后不符
   - 角色能力前后不一致
   - 角色动机前后矛盾

3. **因果关系合理性**
   - 事件A不能直接导致结果B
   - 缺少必要的中间环节
   - 逻辑跳跃

4. **设定遵循**
   - 违反世界规则
   - 违反能力设定
   - 违伏笔回收规则

**实现算法：**

```python
def check_logical_consistency(
    state: Dict[str, Any],
    chapter_id: str,
    chapter_text: str
) -> LogicalConsistencyReport:
    """检查逻辑一致性"""

    issues = []

    # 1. 加载前面章节的内容
    previous_chapters = load_previous_chapters(state, chapter_id, count=3)

    # 2. 提取当前章节的实体、事件、状态
    current_entities = extract_entities(chapter_text)
    current_events = extract_events(chapter_text)
    current_states = extract_states(chapter_text)

    # 3. 检查矛盾
    for entity in current_entities:
        # 检查实体状态前后是否一致
        previous_state = get_entity_state_from_previous(entity, previous_chapters)
        current_state = get_entity_state_from_current(entity, chapter_text)

        if has_contradiction(previous_state, current_state):
            issues.append({
                "type": "entity-state-contradiction",
                "entity": entity.name,
                "previous": previous_state,
                "current": current_state,
                "location": find_contradiction_location(chapter_text),
                "suggestion": "修正状态描述或补充过渡说明"
            })

    # 4. 检查因果关系
    for event in current_events:
        causes = extract_causes(event, chapter_text)
        effects = extract_effects(event, chapter_text)

        for cause, effect in zip(causes, effects):
            if not is_causal_relationship_valid(cause, effect, world_rules):
                issues.append({
                    "type": "invalid-causality",
                    "cause": cause,
                    "effect": effect,
                    "reason": "缺少必要的中间环节或设定支撑",
                    "suggestion": "补充因果链或调整事件设计"
                })

    # 5. 检查设定遵循
    world_rules = load_world_rules(state)
    for rule in world_rules:
        violations = check_rule_violation(chapter_text, rule)
        if violations:
            issues.append({
                "type": "world-rule-violation",
                "rule": rule.description,
                "violations": violations,
                "suggestion": "调整内容或更新设定"
            })

    return LogicalConsistencyReport(issues=issues)
```

### 4.2 爽点分析功能

**分析维度：**

1. **爽点分布**
   - 识别打脸、装逼、反转等爽点类型
   - 检查爽点密度（是否过疏或过密）
   - 分析爽点强度

2. **期待感设置**
   - 悬念设置
   - 钩子质量
   - 追读动力

3. **情绪节奏**
   - 情绪起伏
   - 高潮与低谷
   - 节奏把控

4. **商业要素检查**
   - 核心承诺兑现
   - 情绪契约履行
   - 禁止内容规避

**爽点识别算法：**

```python
def analyze_satisfaction_points(
    chapter_text: str,
    project_contract: Dict[str, Any]
) -> SatisfactionAnalysis:
    """分析爽点"""

    satisfaction_points = []

    # 1. 打脸识别
    face_slap_patterns = [
        "不是.*吗.*",  # 反问打脸
        "你以为.*",    # 误解纠正
        "其实.*",       # 真相揭露
    ]

    # 2. 装逼识别
    show_off_patterns = [
        "展现实力", "震惊全场", "众人瞩目",
        "出手", "露一手", "展示"
    ]

    # 3. 反转识别
    reversal_patterns = [
        "然而", "没想到", "原来", "竟然",
        "真相", "事实是"
    ]

    # 4. 获得识别
    gain_patterns = [
        "获得", "得到", "突破", "提升",
        "炼制", "学会", "领悟"
    ]

    # 逐段扫描
    paragraphs = split_paragraphs(chapter_text)

    for i, para in enumerate(paragraphs):
        # 识别爽点类型
        point_type = None
        if matches_any(para, face_slap_patterns):
            point_type = "face_slap"
        elif matches_any(para, show_off_patterns):
            point_type = "show_off"
        elif matches_any(para, reversal_patterns):
            point_type = "reversal"
        elif matches_any(para, gain_patterns):
            point_type = "gain"

        if point_type:
            # 计算爽点强度
            strength = calculate_satisfaction_strength(
                para, point_type, project_contract
            )

            satisfaction_points.append({
                "type": point_type,
                "paragraph": i + 1,
                "strength": strength,
                "content": para[:100],
                "emotion_impact": analyze_emotion_impact(para)
            })

    # 分析分布
    distribution = analyze_distribution(satisfaction_points)

    # 生成建议
    suggestions = generate_satisfaction_suggestions(
        satisfaction_points, distribution, project_contract
    )

    return SatisfactionAnalysis(
        points=satisfaction_points,
        distribution=distribution,
        suggestions=suggestions
    )
```

**爽点分析输出：**

```json
{
  "satisfactionAnalysis": {
    "overallScore": 12,
    "pointCount": 5,
    "distribution": {
      "face_slap": 1,
      "show_off": 2,
      "reversal": 1,
      "gain": 1
    },
    "density": "适中",
    "rhythm": "良好",
    "issues": [
      {
        "severity": "moderate",
        "type": "point-density-low",
        "description": "第5-8段爽点密度较低，可能影响阅读节奏",
        "suggestion": "考虑增加主角展示实力的情节，或设置小的反转"
      }
    ],
    "strengths": [
      "第3段打脸爽点设计较好，节奏把握准确"
    ],
    "contractAlignment": {
      "corePromises": ["每章结尾保留追读钩子"],
      "fulfilled": true,
      "hookQuality": "high"
    }
  }
}
```

### 4.3 结构分析功能

**检查维度：**

1. **3幕/5幕结构**
   - 检查是否符合经典结构
   - 分析铺垫、高潮、结局的分布
   - 评估结构完整性

2. **卷级闭环检查**
   - 卷内主线是否完整
   - 伏笔是否回收
   - 是否有明确的阶段性成果

3. **剧情节奏**
   - 快慢节奏分布
   - 高潮设置
   - 过渡是否自然

**3幕结构分析：**

```python
def analyze_three_act_structure(
    volume_outline: Dict[str, Any],
    chapters: List[Dict[str, Any]]
) -> StructureAnalysis:
    """分析3幕结构"""

    # 3幕定义
    # Act 1: 铺垫（Setup） - 25%
    # Act 2: 冲突（Confrontation） - 50%
    # Act 3: 结局（Resolution） - 25%

    total_chapters = len(chapters)
    act1_end = int(total_chapters * 0.25)
    act2_end = int(total_chapters * 0.75)

    # 分析各幕
    act1_chapters = chapters[:act1_end]
    act2_chapters = chapters[act1_end:act2_end]
    act3_chapters = chapters[act2_end:]

    # Act 1 检查
    act1_issues = check_act1_requirements(act1_chapters, volume_outline)

    # Act 2 检查
    act2_issues = check_act2_requirements(act2_chapters, volume_outline)

    # Act 3 检查
    act3_issues = check_act3_requirements(act3_chapters, volume_outline)

    # 检查幕间过渡
    transition_issues = check_act_transitions(
        act1_chapters, act2_chapters, act3_chapters
    )

    return StructureAnalysis(
        acts={
            "act1": {"chapters": act1_chapters, "issues": act1_issues},
            "act2": {"chapters": act2_chapters, "issues": act2_issues},
            "act3": {"chapters": act3_chapters, "issues": act3_issues}
        },
        transitions=transition_issues,
        overall_score=calculate_structure_score(act1_issues, act2_issues, act3_issues)
    )
```

**卷级闭环检查：**

```python
def check_volume_closure(
    volume_outline: Dict[str, Any],
    volume_chapters: List[Dict[str, Any]],
    foreshadowing: Dict[str, Any]
) -> ClosureReport:
    """检查卷级闭环"""

    issues = []

    # 1. 检查主线目标
    volume_goal = volume_outline.get("goal")
    if not volume_goal:
        issues.append({
            "type": "missing-volume-goal",
            "severity": "major",
            "description": "卷缺少明确的主线目标"
        })

    # 2. 检查目标达成
    goal_achieved = check_goal_achievement(volume_goal, volume_chapters)
    if not goal_achieved:
        issues.append({
            "type": "goal-not-achieved",
            "severity": "major",
            "description": f"主线目标'{volume_goal}'未在卷内完成"
        })

    # 3. 检查伏笔回收
    volume_foreshadows = get_foreshadows_in_volume(
        foreshadowing, volume_outline["id"]
    )

    for foreshadow in volume_foreshadows:
        if foreshadow["payoffWindow"]["end"] in volume_outline["id"]:
            # 应该在本卷回收
            if not is_foreshadow_resolved(foreshadow, volume_chapters):
                issues.append({
                    "type": "foreshadow-not-resolved",
                    "severity": "moderate",
                    "description": f"伏笔'{foreshadow['label']}'未在本卷回收"
                })

    # 4. 检查阶段性成果
    milestone_achieved = check_milestone_achievement(
        volume_outline, volume_chapters
    )
    if not milestone_achieved:
        issues.append({
            "type": "no-milestone",
            "severity": "minor",
            "description": "卷缺少明确的阶段性成果"
        })

    # 5. 检查与下一卷的衔接
    next_volume_setup = check_next_volume_setup(
        volume_chapters[-1], volume_outline.get("nextVolumeHint")
    )
    if not next_volume_setup:
        issues.append({
            "type": "no-next-volume-setup",
            "severity": "minor",
            "description": "未为下一卷做铺垫"
        })

    return ClosureReport(
        can_close=len([i for i in issues if i["severity"] == "major"]) == 0,
        issues=issues
    )
```

**结构分析输出：**

```json
{
  "structureAnalysis": {
    "threeActStructure": {
      "act1": {
        "name": "铺垫",
        "chapterRange": "1-5",
        "purpose": "介绍主角、建立目标、引入冲突",
        "score": 14,
        "issues": []
      },
      "act2": {
        "name": "冲突",
        "chapterRange": "6-15",
        "purpose": "发展冲突、升级压力、推进剧情",
        "score": 12,
        "issues": [
          {
            "severity": "moderate",
            "description": "冲突升级不够明显，9-11章节奏较平",
            "suggestion": "增加外部压力或内部矛盾"
          }
        ]
      },
      "act3": {
        "name": "结局",
        "chapterRange": "16-20",
        "purpose": "解决冲突、达成目标、为下一卷铺垫",
        "score": 13,
        "issues": []
      }
    },
    "volumeClosure": {
      "canClose": true,
      "goalAchieved": true,
      "foreshadowsResolved": 3,
      "foreshadowsPending": 1,
      "nextVolumeSetup": "adequate"
    }
  }
}
```

---

## 5. 综合审查输出结构

### 5.1 统一的审查报告

```json
{
  "reviewId": "comprehensive-review-chapter-001",
  "generatedAt": "2026-04-30T10:30:00Z",
  "chapterId": "chapter-001",

  "entityReview": {
    "knownEntityCompliance": {...},
    "unknownEntityDiscovery": {...}
  },

  "logicalConsistency": {
    "overallScore": 13,
    "issues": [
      {
        "severity": "moderate",
        "type": "entity-state-contradiction",
        "description": "角色张三的情绪状态前后不一致",
        "location": "第3段",
        "evidence": ["前文: 张三很冷静", "后文: 张三突然暴怒"],
        "suggestion": "补充情绪转变的过渡描写"
      }
    ]
  },

  "satisfactionAnalysis": {
    "overallScore": 12,
    "pointCount": 4,
    "distribution": {...},
    "issues": [...]
  },

  "structureAnalysis": {
    "threeActStructure": {...},
    "volumeClosure": {...}
  },

  "overallAssessment": {
    "totalScore": 12.5,
    "readyForNext": true,
    "criticalIssues": 0,
    "majorIssues": 2,
    "moderateIssues": 3,
    "minorIssues": 5,

    "summary": "章节整体质量良好，爽点分布合理，结构完整",
    "strengths": [
      "打脸爽点设计精彩",
      "角色刻画生动"
    ],
    "priorities": [
      "补充缺失的角色卡：李四的师父",
      "修正张三情绪状态的矛盾"
    ]
  }
}
```

### 5.2 审查命令接口

```bash
# 全面综合审查
story-canvas review comprehensive --chapter-id chapter-001

# 只审查实体
story-canvas review comprehensive --chapter-id chapter-001 --focus entities

# 只审查逻辑
story-canvas review comprehensive --chapter-id chapter-001 --focus logic

# 只审查爽点
story-canvas review comprehensive --chapter-id chapter-001 --focus satisfaction

# 只审查结构
story-canvas review comprehensive --chapter-id chapter-001 --focus structure

# 指定严格度
story-canvas review comprehensive --chapter-id chapter-001 --strictness commercial
```

---

## 6. 实现优先级

### P0 - 核心功能
1. **实体资产自动包裹** - 基于已知资产库自动添加@{}
2. **实体缺失检查** - 发现未知实体，建议补充

### P1 - 编辑功能
3. **逻辑一致性检查** - 前后文矛盾、行为一致性
4. **爽点分析** - 爽点识别、分布、强度

### P2 - 高级功能
5. **结构分析** - 3幕/5幕结构、卷级闭环

---

## 7. 技术要点

### 7.1 NLP引擎选择
- 考虑使用jieba进行中文分词
- 考虑使用spaCy或HanLP进行命名实体识别
- 或者基于规则的轻量级实现

### 7.2 上下文管理
- 维护当前活跃实体列表
- 追踪实体状态变化
- 处理代词消歧

### 7.3 性能优化
- 实体索引缓存
- 增量审查（只审查变化部分）
- 并行处理独立的检查项

---

**设计完成，等待实现确认**
