# Story Canvas — 渐进式设定扩展与全流程AI审查架构设计

> Date: 2026-04-30
> Status: Draft
> Scope: 渐进式设定扩展、实体引用自动化、多层级AI审查系统、架构方向预防

---

## 1. 问题陈述

### 1.1 当前架构的核心缺陷

通过深入分析现有代码和设计文档，发现以下关键问题：

**问题1：设定是一次性生成的，不是渐进式扩展的**
- `init` 时AI生成的设定往往过于简短
- 缺少从"一句话核心承诺"到"详细世界设定"的中间步骤
- 无法在写作过程中逐步丰富设定

**问题2：@{}实体引用完全依赖AI手动填写**
- 虽然有`entity mention-adopt`、`entity mention-tag-apply`等命令
- 但这些命令需要手动执行，AI写作时缺少"自动检测+一键应用"的便捷流程
- 没有在写作过程中实时提示"应该添加@{}"的机制

**问题3：角色关系管理是静态的**
- 虽然有`relationProjections`，但需要手动更新
- 缺少自动识别角色关系变化的机制
- 无法追踪"从敌对→合作→背叛"的复杂关系演变

**问题4：AI审查只在章节级别**
- 现有`review chapter`、`review scene`主要关注写作质量
- 缺少对设定完善度、角色行为逻辑一致性、大纲合理性、剧情走向连贯性的审查
- 如果开始的架构方向有问题，后续很难通过章节审查发现

**问题5：伏笔约束不够强**
- 虽然有`foreshadowing.yaml`和`foreshadow check`
- 但缺少"强制要求每章必须埋钩子"的约束
- 没有检查"埋了但没回收"或"回收了但没埋"的机制

### 1.2 根本原因分析

1. **工作流设计缺陷**：
   - `init -> story_gate -> context_ready -> drafting` 流程跳过了设定完善阶段
   - 缺少"设定扩展"和"架构审查"这两个关键门禁

2. **命令设计问题**：
   - 实体引用相关命令过于底层，需要组合多个命令才能完成简单任务
   - 缺少"写作时实时建议"的机制

3. **审查层级不完整**：
   - 只有"章节级"和"场景级"审查
   - 缺少"设定级"、"大纲级"、"剧情走向级"审查

4. **状态管理不足**：
   - 角色关系、伏笔状态缺少自动化追踪
   - 依赖人工维护，容易遗漏

---

## 2. 设计目标

1. **渐进式设定扩展**：从一句话核心承诺逐步推导到详细设定
2. **实体引用自动化**：写作时自动检测缺失的@{}并提供一键应用
3. **角色关系动态追踪**：自动识别并记录角色关系变化
4. **多层级AI审查**：从设定到章节的全流程质量保证
5. **架构方向预防**：在写作前就发现架构问题
6. **伏笔强制约束**：确保每章都有钩子，且埋了就要回收

---

## 3. 整体架构

### 3.1 新的工作流阶段

```
init -> story_gate -> setting_expansion -> architecture_review -> outline_expansion -> context_ready -> drafting -> writing_assist -> review
         ↓              ↓                   ↓                    ↓                    ↓              ↓              ↓
      [检查定位]    [扩展设定]          [架构审查]           [细化大纲]           [上下文]       [写作辅助]     [全层审查]
                     ↓                   ↓                    ↓                                   ↓
                  [模板系统]         [多层级审查]         [beats/scenes]                     [实时建议]
                                                                                                   ↓
                                                                                            [@{}自动检测]
```

### 3.2 新增命令组

```bash
# 设定扩展命令
story-canvas setting expand --target worldbook|entities|factions
story-canvas setting check-readiness

# 架构审查命令
story-canvas architecture review --scope setting|outline|characters|plot

# 写作辅助命令
story-canvas writing assist --chapter-id chapter-001
story-canvas writing mention-check --auto-suggest
story-canvas writing relation-track --auto-detect

# 多层级审查命令
story-canvas review setting --strictness standard
story-canvas review outline --check-consistency
story-canvas review plot --check-foreshadowing
```

---

## 4. 核心设计

### 4.1 渐进式设定扩展

#### 问题分析

当前`init`命令生成的设定过于简短：
- `worldbook.worldRules` 通常只有1-2条简单规则
- `entities` 只有角色名和基本身份
- 缺少从"核心承诺"到"详细设定"的中间步骤

#### 解决方案

**新增`setting expand`命令**：

```bash
# 基于核心承诺扩展世界观
story-canvas setting expand --target worldbook \
  --focus "力量体系|地理|势力关系" \
  --depth "minimal|standard|detailed" \
  --based-on "核心承诺：现代都市修真，隐藏世界与普通世界共存"

# 基于核心承诺扩展角色卡
story-canvas setting expand --target entities \
  --entity-id protagonist \
  --focus "外貌|性格|背景|成长弧线|关系网络" \
  --depth "standard"

# 渐进式扩展（推荐）
story-canvas setting expand --target worldbook \
  --mode progressive \
  --step 1  # 第一步：生成基础世界规则（3-5条）
```

**核心设计原则**：
1. **渐进式**：从最小可用设定开始，逐步丰富
2. **基于核心承诺**：所有扩展都基于`storyContract.corePromises`
3. **题材感知**：利用题材模板生成符合类型特点的设定
4. **可回滚**：每次扩展生成新版本，允许回退

**技术实现**：

```python
# services/setting_expander.py

def expand_setting(
    state: Dict[str, Any],
    target: str,  # "worldbook" | "entities" | "factions"
    focus: str,
    depth: str = "standard",
    based_on: str = "",
    mode: str = "one-shot"
) -> Dict[str, Any]:
    """渐进式扩展设定"""

    if mode == "progressive":
        return _progressive_expand(state, target, focus, depth)
    else:
        return _one_shot_expand(state, target, focus, depth, based_on)

def _progressive_expand(
    state: Dict[str, Any],
    target: str,
    focus: str,
    depth: str
) -> Dict[str, Any]:
    """渐进式扩展：分步骤生成"""

    positioning = state["project"]["positioning"]
    core_promises = state["project"]["storyContract"]["corePromises"]

    # 加载题材模板
    template = load_genre_template(
        positioning.get("primaryGenre"),
        positioning.get("subGenre")
    )

    # 生成扩展步骤
    steps = _generate_expansion_steps(template, target, focus, depth)

    return {
        "mode": "progressive",
        "totalSteps": len(steps),
        "currentStep": 1,
        "steps": steps,
        "currentExpansion": _execute_step(steps[0], state, template)
    }

def _generate_expansion_steps(
    template: Dict[str, Any],
    target: str,
    focus: str,
    depth: str
) -> List[Dict[str, Any]]:
    """生成扩展步骤"""

    if target == "worldbook":
        if "力量体系" in focus:
            return [
                {
                    "step": 1,
                    "title": "生成基础境界体系",
                    "description": "生成3-5个基础境界和突破条件",
                    "output": "worldRules",
                    "count": 3
                },
                {
                    "step": 2,
                    "title": "完善突破细节",
                    "description": "为每个境界添加详细突破方法和代价",
                    "output": "worldRules",
                    "count": 5
                },
                {
                    "step": 3,
                    "title": "生成世界结构",
                    "description": "生成隐藏世界和普通世界的共存规则",
                    "output": "premiseFacts",
                    "count": 3
                }
            ]
        elif "势力关系" in focus:
            return [
                {
                    "step": 1,
                    "title": "生成核心势力",
                    "description": "生成3-5个主要势力及其目标",
                    "output": "factions",
                    "count": 3
                },
                {
                    "step": 2,
                    "title": "明确势力关系",
                    "description": "定义势力间的对立、合作、竞争关系",
                    "output": "factions",
                    "count": 5
                }
            ]

    # 其他情况...
```

**使用示例**：

```bash
# 第一步：生成基础世界规则
story-canvas setting expand --target worldbook --focus "力量体系" --mode progressive --step 1

# 输出示例：
{
  "mode": "progressive",
  "totalSteps": 3,
  "currentStep": 1,
  "steps": [...],
  "currentExpansion": {
    "worldRules": [
      {
        "id": "rule-cultivation-base",
        "label": "基础境界",
        "rule": "炼气 -> 筑基 -> 金丹 -> 元婴",
        "details": ["每个境界需要明确的突破条件和代价"]
      }
    ]
  }
}

# 第二步：完善突破细节
story-canvas setting expand --target worldbook --focus "力量体系" --mode progressive --step 2
```

### 4.2 实体引用自动化

#### 问题分析

虽然有`entity mention-adopt`等命令，但存在以下问题：
1. 需要手动运行命令，无法在写作时实时提示
2. 命令组合复杂，需要`mention-plan` -> `mention-apply`等多步操作
3. 缺少"一键应用所有建议"的便捷功能

#### 解决方案

**新增`writing assist`命令**：

```bash
# 写作辅助：实时检测并建议
story-canvas writing assist --chapter-id chapter-001

# 专门检查缺失的@{}
story-canvas writing mention-check --chapter-id chapter-001 --auto-suggest

# 一键应用所有建议
story-canvas writing mention-check --chapter-id chapter-001 --auto-apply
```

**核心设计**：

```python
# services/writing_assistant.py

def build_writing_assistance(
    state: Dict[str, Any],
    chapter_id: str,
    assistance_type: str = "full"  # "full" | "mention-only" | "relation-only"
) -> Dict[str, Any]:
    """生成写作辅助建议"""

    chapter_file = chapter_path(root, chapter_id)
    chapter_text = chapter_file.read_text(encoding="utf-8")

    assistance = {
        "chapterId": chapter_id,
        "timestamp": now_iso(),
        "mentionSuggestions": [],
        "relationSuggestions": [],
        "foreshadowSuggestions": [],
        "consistencyWarnings": []
    }

    if assistance_type in ["full", "mention-only"]:
        # 检测缺失的@{}
        mention_suggestions = _detect_missing_mentions(state, chapter_text)
        assistance["mentionSuggestions"] = mention_suggestions

    if assistance_type in ["full", "relation-only"]:
        # 检测角色关系变化
        relation_suggestions = _detect_relation_changes(state, chapter_text, chapter_id)
        assistance["relationSuggestions"] = relation_suggestions

    return assistance

def _detect_missing_mentions(
    state: Dict[str, Any],
    chapter_text: str
) -> List[Dict[str, Any]]:
    """检测缺失的@{}包裹"""

    catalog = build_reference_catalog(state)
    quote_ranges = _quote_ranges(chapter_text)

    # 找出所有未包裹的已知实体
    known_unwrapped = []
    for item in catalog:
        names = [name for name in item.get("names", []) if isinstance(name, str) and name]
        plain_count, quoted_count = _collect_unwrapped_mentions(
            chapter_text, names, quote_ranges
        )

        if plain_count > 0:
            known_unwrapped.append({
                "entityId": item.get("id"),
                "name": item.get("canonicalName"),
                "kind": item.get("kind"),
                "plainCount": plain_count,
                "suggestedTag": f"@{{{item.get('canonicalName')}}}",
                "priority": "high" if plain_count > 3 else "medium",
                "autoActionable": True  # 可以自动应用
            })

    return known_unwrapped

def _detect_relation_changes(
    state: Dict[str, Any],
    chapter_text: str,
    chapter_id: str
) -> List[Dict[str, Any]]:
    """检测角色关系变化"""

    entities = state.get("entities", {}).get("entities", [])
    relation_projections = state.get("projection", {}).get("relationProjections", [])

    # 分析章节中出现的角色对
    character_pairs = _extract_character_pairs(chapter_text, entities)

    suggestions = []
    for pair in character_pairs:
        from_id = pair["from"]
        to_id = pair["to"]

        # 查找现有关系
        existing_relation = _find_existing_relation(
            relation_projections, from_id, to_id
        )

        # 分析当前章节的关系表现
        current_relation = _analyze_current_relation(
            chapter_text, pair, entities
        )

        # 检测关系变化
        if existing_relation:
            if _relation_changed(existing_relation, current_relation):
                suggestions.append({
                    "type": "relation-change",
                    "fromId": from_id,
                    "toId": to_id,
                    "fromName": _get_entity_name(entities, from_id),
                    "toName": _get_entity_name(entities, to_id),
                    "previousLabel": existing_relation.get("label"),
                    "currentLabel": current_relation["label"],
                    "evidence": current_relation["evidence"],
                    "suggestedAction": "update-relation",
                    "autoActionable": True
                })
        else:
            # 新发现的关系
            suggestions.append({
                "type": "new-relation",
                "fromId": from_id,
                "toId": to_id,
                "fromName": _get_entity_name(entities, from_id),
                "toName": _get_entity_name(entities, to_id),
                "suggestedLabel": current_relation["label"],
                "evidence": current_relation["evidence"],
                "suggestedAction": "add-relation",
                "autoActionable": True
            })

    return suggestions
```

**CLI集成**：

```python
# commands/writing.py

def command_writing_assist(args) -> int:
    """写作辅助命令"""

    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project(root)

    chapter_id = args.chapter_id or state["project"].get("activeChapterId")
    if not chapter_id:
        raise SystemExit("缺少 chapter id")

    assistance = build_writing_assistance(
        state, chapter_id,
        assistance_type=args.assistance_type or "full"
    )

    # 输出JSON格式，供AI agent消费
    print(json.dumps(assistance, ensure_ascii=False, indent=2))

    # 如果是交互模式，可以提供更友好的输出
    if args.interactive:
        _print_interactive_assistance(assistance)

    return 0

def command_writing_mention_check(args) -> int:
    """检查缺失的@{}"""

    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project(root)

    chapter_id = args.chapter_id or state["project"].get("activeChapterId")

    assistance = build_writing_assistance(
        state, chapter_id,
        assistance_type="mention-only"
    )

    mention_suggestions = assistance.get("mentionSuggestions", [])

    if not mention_suggestions:
        print("未发现缺失的实体引用")
        return 0

    # 如果指定了--auto-apply，自动应用所有建议
    if args.auto_apply:
        return _auto_apply_mention_suggestions(
            root, state, chapter_id, mention_suggestions
        )

    # 否则输出建议
    print(json.dumps({
        "chapterId": chapter_id,
        "suggestionCount": len(mention_suggestions),
        "suggestions": mention_suggestions
    }, ensure_ascii=False, indent=2))

    return 0

def _auto_apply_mention_suggestions(
    root: Path,
    state: Dict[str, Any],
    chapter_id: str,
    suggestions: List[Dict[str, Any]]
) -> int:
    """自动应用所有@{}建议"""

    chapter_file = chapter_path(root, chapter_id)
    chapter_text = chapter_file.read_text(encoding="utf-8")

    # 收集所有可自动应用的建议
    actionable = [s for s in suggestions if s.get("autoActionable")]

    if not actionable:
        print("没有可自动应用的建议")
        return 0

    # 应用建议
    catalog = build_reference_catalog(state)
    replacements = svc_collect_tag_replacements(chapter_text, catalog)

    updated_text = _apply_tag_replacements(chapter_text, replacements)

    if updated_text != chapter_text:
        chapter_file.write_text(updated_text, encoding="utf-8")

        print(f"已应用 {len(replacements)} 条建议")
        print(f"修改前：{len([s for s in suggestions])} 个缺失引用")
        print(f"修改后：{len(replacements)} 个引用已包裹")

        return 0
    else:
        print("未应用任何建议（可能已手动修复）")
        return 1
```

### 4.3 角色关系动态追踪

#### 问题分析

现有`relationProjections`需要手动维护，存在以下问题：
1. 关系变化容易被遗忘
2. 无法追溯关系演变历史
3. 缺少自动检测关系变化的机制

#### 解决方案

**新增`writing relation-track`命令**：

```bash
# 自动检测并追踪角色关系变化
story-canvas writing relation-track --chapter-id chapter-001 --auto-detect

# 查看关系演变历史
story-canvas writing relation-history --entity-id protagonist
```

**核心设计**：

```python
# services/relation_tracker.py

def track_relation_changes(
    state: Dict[str, Any],
    chapter_id: str,
    auto_detect: bool = True
) -> Dict[str, Any]:
    """追踪角色关系变化"""

    entities = state.get("entities", {}).get("entities", [])
    relation_projections = state.get("projection", {}).get("relationProjections", [])

    chapter_file = chapter_path(root, chapter_id)
    chapter_text = chapter_file.read_text(encoding="utf-8")

    # 自动检测关系变化
    if auto_detect:
        detected_changes = _detect_relation_changes(
            entities, relation_projections, chapter_text, chapter_id
        )
    else:
        detected_changes = []

    # 生成关系追踪报告
    return {
        "chapterId": chapter_id,
        "detectedChanges": detected_changes,
        "relationHistory": _build_relation_history(relation_projections),
        "suggestions": _generate_relation_suggestions(detected_changes)
    }

def _detect_relation_changes(
    entities: List[Dict[str, Any]],
    relation_projections: List[Dict[str, Any]],
    chapter_text: str,
    chapter_id: str
) -> List[Dict[str, Any]]:
    """自动检测关系变化"""

    # 提取章节中出现的角色对
    character_pairs = _extract_character_pairs_from_text(
        chapter_text, entities
    )

    changes = []
    for pair in character_pairs:
        from_id = pair["from"]
        to_id = pair["to"]

        # 查找现有关系
        existing = _find_relation(relation_projections, from_id, to_id)

        # 分析当前章节的关系表现
        current_analysis = _analyze_relation_in_chapter(
            chapter_text, pair, entities
        )

        if existing:
            # 检查关系是否变化
            if _is_relation_changed(existing, current_analysis):
                changes.append({
                    "type": "relation-change",
                    "fromId": from_id,
                    "toId": to_id,
                    "fromName": _get_entity_name(entities, from_id),
                    "toName": _get_entity_name(entities, to_id),
                    "previousLabel": existing.get("label"),
                    "currentLabel": current_analysis["label"],
                    "changeType": _classify_relation_change(
                        existing.get("label"),
                        current_analysis["label"]
                    ),
                    "evidence": current_analysis["evidence"],
                    "confidence": current_analysis["confidence"]
                })
        else:
            # 新发现的关系
            if current_analysis["confidence"] > 0.7:
                changes.append({
                    "type": "new-relation",
                    "fromId": from_id,
                    "toId": to_id,
                    "fromName": _get_entity_name(entities, from_id),
                    "toName": _get_entity_name(entities, to_id),
                    "suggestedLabel": current_analysis["label"],
                    "evidence": current_analysis["evidence"],
                    "confidence": current_analysis["confidence"]
                })

    return changes

def _classify_relation_change(
    previous_label: str,
    current_label: str
) -> str:
    """分类关系变化类型"""

    # 定义关系变化类型
    if previous_label == current_label:
        return "no-change"

    # 敌对关系变化
    if "敌" in previous_label or "对" in previous_label:
        if "友" in current_label or "盟" in current_label:
            return "enemy-to-friend"
        elif "合" in current_label:
            return "enemy-to-cooperation"

    # 友好关系变化
    if "友" in previous_label or "盟" in previous_label:
        if "敌" in current_label or "对" in current_label:
            return "friend-to-enemy"
        elif "背叛" in current_label:
            return "friend-to-betrayal"

    # 其他变化
    return "other-change"
```

### 4.4 多层级AI审查系统

#### 问题分析

现有审查系统的问题：
1. 只有`review chapter`和`review scene`两个级别
2. 缺少对设定完善度、大纲合理性、剧情走向连贯性的审查
3. 如果开始架构有问题，章节审查无法发现

#### 解决方案

**建立4层审查体系**：

```
Level 1: 设定级审查 (review setting)
   ↓ 检查：设定完善度、设定一致性、设定与核心承诺的契合度

Level 2: 大纲级审查 (review outline)
   ↓ 检查：大纲合理性、大纲与设定的一致性、剧情走向连贯性

Level 3: 章节级审查 (review chapter) [已有]
   ↓ 检查：章节质量、风格、设定遵循、伏笔回收

Level 4: 场景级审查 (review scene) [已有]
   ↓ 检查：场景质量、逻辑、对话、伏笔细节
```

**Level 1: 设定级审查**

```bash
story-canvas review setting --strictness minimal|standard|strict
```

```python
# services/setting_review.py

def review_setting(
    state: Dict[str, Any],
    strictness: str = "standard"
) -> Dict[str, Any]:
    """审查设定完善度"""

    worldbook = state.get("worldbook", {})
    entities = state.get("entities", {}).get("entities", [])
    positioning = state.get("project", {}).get("positioning", {})
    story_contract = state.get("project", {}).get("storyContract", {})
    story_template = state.get("project", {}).get("storyTemplate", {})

    issues = []
    scores = {}

    # 1. 检查世界规则完善度
    world_rules = worldbook.get("worldRules", [])
    world_rules_score = _check_world_rules_completeness(
        world_rules, story_template, strictness
    )
    scores["worldRules"] = world_rules_score

    if world_rules_score["score"] < 10:
        issues.append({
            "level": "error" if strictness == "strict" else "warning",
            "category": "setting-completeness",
            "message": f"世界规则不足{world_rules_score['required']}条（当前{world_rules_score['actual']}条）",
            "suggestion": f"运行 `story-canvas setting expand --target worldbook --focus worldRules` 补充世界规则"
        })

    # 2. 检查设定与核心承诺的一致性
    consistency_score = _check_setting_promise_consistency(
        worldbook, entities, story_contract
    )
    scores["promiseConsistency"] = consistency_score

    if consistency_score["score"] < 12:
        issues.append({
            "level": "warning",
            "category": "setting-consistency",
            "message": "设定与核心承诺存在偏差",
            "details": consistency_score["mismatches"],
            "suggestion": "检查设定是否真正支撑了核心承诺"
        })

    # 3. 检查角色设定完善度
    character_score = _check_character_completeness(
        entities, story_template, strictness
    )
    scores["characters"] = character_score

    # 4. 检查势力设定完善度
    factions = worldbook.get("factions", [])
    faction_score = _check_faction_completeness(
        factions, story_template, strictness
    )
    scores["factions"] = faction_score

    # 计算总分
    total_score = sum(s["score"] for s in scores.values()) / len(scores)

    return {
        "overallScore": total_score,
        "strictness": strictness,
        "scores": scores,
        "issues": issues,
        "ready": total_score >= 12 and len([i for i in issues if i["level"] == "error"]) == 0
    }

def _check_world_rules_completeness(
    world_rules: List[Dict[str, Any]],
    story_template: Dict[str, Any],
    strictness: str
) -> Dict[str, Any]:
    """检查世界规则完善度"""

    module_policy = story_template.get("modulePolicy", {})
    required = module_policy.get("worldRules") == "required"

    if not required:
        return {"score": 15, "required": 0, "actual": len(world_rules)}

    required_count = 3 if strictness == "standard" else 5
    actual_count = len(world_rules)

    # 检查规则质量
    quality_score = 0
    for rule in world_rules:
        if rule.get("rule") and len(rule.get("rule", "")) > 20:
            quality_score += 3
        elif rule.get("rule"):
            quality_score += 1

    # 计算分数
    if actual_count >= required_count:
        count_score = 15
    elif actual_count >= required_count * 0.7:
        count_score = 10
    else:
        count_score = 5

    final_score = min(15, count_score + quality_score / 2)

    return {
        "score": final_score,
        "required": required_count,
        "actual": actual_count,
        "quality": quality_score
    }
```

**Level 2: 大纲级审查**

```bash
story-canvas review outline --check-consistency --check-foreshadowing
```

```python
# services/outline_review.py

def review_outline(
    state: Dict[str, Any],
    check_consistency: bool = True,
    check_foreshadowing: bool = True
) -> Dict[str, Any]:
    """审查大纲合理性和一致性"""

    outline = state.get("outline", {})
    worldbook = state.get("worldbook", {})
    entities = state.get("entities", {}).get("entities", [])
    foreshadowing = state.get("foreshadowing", {})

    issues = []
    scores = {}

    # 1. 检查大纲与设定的一致性
    if check_consistency:
        consistency_score = _check_outline_setting_consistency(
            outline, worldbook, entities
        )
        scores["settingConsistency"] = consistency_score

        if consistency_score["score"] < 12:
            issues.extend(consistency_score["issues"])

    # 2. 检查大纲与伏笔的一致性
    if check_foreshadowing:
        foreshadow_score = _check_outline_foreshadow_consistency(
            outline, foreshadowing
        )
        scores["foreshadowConsistency"] = foreshadow_score

        if foreshadow_score["score"] < 12:
            issues.extend(foreshadow_score["issues"])

    # 3. 检查剧情走向连贯性
    coherence_score = _check_plot_coherence(outline)
    scores["plotCoherence"] = coherence_score

    # 4. 检查角色弧线合理性
    arc_score = _check_character_arcs(outline, entities)
    scores["characterArcs"] = arc_score

    # 计算总分
    total_score = sum(s["score"] for s in scores.values()) / len(scores)

    return {
        "overallScore": total_score,
        "scores": scores,
        "issues": issues,
        "ready": total_score >= 12 and len([i for i in issues if i["level"] == "error"]) == 0
    }

def _check_plot_coherence(outline: Dict[str, Any]) -> Dict[str, Any]:
    """检查剧情走向连贯性"""

    volumes = outline.get("volumes", [])
    all_chapters = []
    for vol in volumes:
        all_chapters.extend(vol.get("chapters", []))

    issues = []

    # 检查章节之间的衔接
    for i in range(len(all_chapters) - 1):
        current = all_chapters[i]
        next_ch = all_chapters[i + 1]

        current_direction = current.get("direction", "")
        next_direction = next_ch.get("direction", "")

        # 检查是否有明确的承接关系
        if not _has_clear_continuation(current_direction, next_direction):
            issues.append({
                "level": "warning",
                "category": "plot-coherence",
                "fromChapter": current.get("id"),
                "toChapter": next_ch.get("id"),
                "message": f"章节 {current.get('id')} 到 {next_ch.get('id')} 的承接关系不够明确",
                "suggestion": "补充章节间的承接点或钩子"
            })

    # 计算分数
    total_chapters = len(all_chapters)
    coherence_ratio = 1 - len(issues) / max(total_chapters, 1)
    score = int(coherence_ratio * 15)

    return {
        "score": score,
        "totalChapters": total_chapters,
        "continuityIssues": len(issues),
        "issues": issues
    }
```

**Level 3/4: 章节/场景级审查** [已有，增强]

```python
# 增强 story_review.py，添加更多设定检查

def build_chapter_review(
    state: Dict[str, Any],
    chapter_id: str,
    chapter_text: str,
    analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """增强的章节审查，增加设定遵循检查"""

    # ... 现有逻辑 ...

    # 新增：检查设定遵循
    setting_compliance = _check_setting_compliance(
        state, chapter_text, chapter_id
    )
    dimension_map["settingCompliance"] = setting_compliance

    # 新增：检查角色行为逻辑一致性
    character_logic = _check_character_logic_consistency(
        state, chapter_text, chapter_id
    )
    dimension_map["characterLogic"] = character_logic

    # ... 现有逻辑 ...

    return dimension_map

def _check_setting_compliance(
    state: Dict[str, Any],
    chapter_text: str,
    chapter_id: str
) -> Dict[str, Any]:
    """检查设定遵循"""

    worldbook = state.get("worldbook", {})
    world_rules = worldbook.get("worldRules", [])

    violations = []
    for rule in world_rules:
        rule_text = rule.get("rule", "")
        # 检查正文是否违反了规则
        if _violates_rule(chapter_text, rule_text):
            violations.append({
                "ruleId": rule.get("id"),
                "rule": rule_text,
                "evidence": _find_violation_evidence(chapter_text, rule_text)
            })

    if violations:
        return {
            "score": 8,
            "comment": "本章存在设定违反",
            "violations": violations,
            "suggestion": "检查是否需要修改正文或更新设定"
        }
    else:
        return {
            "score": 15,
            "comment": "本章遵循了设定"
        }

def _check_character_logic_consistency(
    state: Dict[str, Any],
    chapter_text: str,
    chapter_id: str
) -> Dict[str, Any]:
    """检查角色行为逻辑一致性"""

    entities = state.get("entities", {}).get("entities", [])

    # 提取章节中出现的角色及其行为
    character_behaviors = _extract_character_behaviors(chapter_text, entities)

    logic_issues = []
    for behavior in character_behaviors:
        entity_id = behavior["entityId"]
        entity = _find_entity(entities, entity_id)

        if not entity:
            continue

        # 检查行为是否符合角色设定
        personality = entity.get("seed", {}).get("personality", "")
        motivation = entity.get("seed", {}).get("motivation", "")

        if not _behavior_matches_character(behavior, personality, motivation):
            logic_issues.append({
                "entityId": entity_id,
                "entityName": entity.get("name"),
                "behavior": behavior["description"],
                "personality": personality,
                "motivation": motivation,
                "issue": "行为与角色设定不一致"
            })

    if logic_issues:
        return {
            "score": 9,
            "comment": "部分角色行为逻辑存在问题",
            "issues": logic_issues
        }
    else:
        return {
            "score": 15,
            "comment": "角色行为逻辑一致"
        }
```

### 4.5 架构方向预防

#### 问题分析

如果开始架构有问题，后续很难修正：
1. 设定不支撑核心承诺
2. 大纲无法实现故事目标
3. 角色弧线不合理

#### 解决方案

**新增`architecture review`命令**：

```bash
# 在开始写作前进行架构审查
story-canvas architecture review --scope setting|outline|characters|plot
```

```python
# services/architecture_review.py

def review_architecture(
    state: Dict[str, Any],
    scope: str = "full"  # "setting" | "outline" | "characters" | "plot" | "full"
) -> Dict[str, Any]:
    """架构级审查，预防方向性问题"""

    positioning = state.get("project", {}).get("positioning", {})
    story_contract = state.get("project", {}).get("storyContract", {})
    story_template = state.get("project", {}).get("storyTemplate", {})
    worldbook = state.get("worldbook", {})
    entities = state.get("entities", {}).get("entities", [])
    outline = state.get("outline", {})

    issues = []
    risks = []

    # 1. 设定架构审查
    if scope in ["setting", "full"]:
        setting_review = _review_setting_architecture(
            worldbook, story_contract, story_template
        )
        issues.extend(setting_review["issues"])
        risks.extend(setting_review["risks"])

    # 2. 大纲架构审查
    if scope in ["outline", "full"]:
        outline_review = _review_outline_architecture(
            outline, story_contract, worldbook
        )
        issues.extend(outline_review["issues"])
        risks.extend(outline_review["risks"])

    # 3. 角色架构审查
    if scope in ["characters", "full"]:
        character_review = _review_character_architecture(
            entities, story_contract, outline
        )
        issues.extend(character_review["issues"])
        risks.extend(character_review["risks"])

    # 4. 剧情架构审查
    if scope in ["plot", "full"]:
        plot_review = _review_plot_architecture(
            outline, story_contract, foreshadowing
        )
        issues.extend(plot_review["issues"])
        risks.extend(plot_review["risks"])

    # 评估架构风险等级
    risk_level = _assess_risk_level(issues, risks)

    return {
        "riskLevel": risk_level,
        "scope": scope,
        "issues": issues,
        "risks": risks,
        "recommendations": _generate_recommendations(issues, risks),
        "readyToWrite": risk_level != "high"
    }

def _review_setting_architecture(
    worldbook: Dict[str, Any],
    story_contract: Dict[str, Any],
    story_template: Dict[str, Any]
) -> Dict[str, Any]:
    """审查设定架构"""

    issues = []
    risks = []

    # 检查设定是否支撑核心承诺
    core_promises = story_contract.get("corePromises", [])
    world_rules = worldbook.get("worldRules", [])

    for promise in core_promises:
        supported = False
        for rule in world_rules:
            if _rule_supports_promise(rule, promise):
                supported = True
                break

        if not supported:
            issues.append({
                "level": "error",
                "category": "setting-promise-alignment",
                "message": f"设定不支撑核心承诺: {promise}",
                "suggestion": f"添加与承诺相关的世界规则"
            })

    # 检查设定是否自洽
    consistency_issues = _check_setting_consistency(worldbook)
    issues.extend(consistency_issues)

    # 检查设定是否过于复杂
    complexity_risk = _assess_setting_complexity(worldbook)
    if complexity_risk > 0.7:
        risks.append({
            "level": "warning",
            "category": "setting-complexity",
            "message": "设定过于复杂，可能增加维护难度",
            "suggestion": "考虑简化部分设定或延迟引入"
        })

    return {"issues": issues, "risks": risks}

def _review_outline_architecture(
    outline: Dict[str, Any],
    story_contract: Dict[str, Any],
    worldbook: Dict[str, Any]
) -> Dict[str, Any]:
    """审查大纲架构"""

    issues = []
    risks = []

    # 检查大纲是否能实现核心承诺
    core_promises = story_contract.get("corePromises", [])
    volumes = outline.get("volumes", [])

    if not volumes:
        issues.append({
            "level": "error",
            "category": "outline-missing",
            "message": "缺少卷结构",
            "suggestion": "创建至少一个卷的结构"
        })

    # 检查每卷是否能支撑承诺的一部分
    for vol in volumes:
        vol_theme = vol.get("theme", "")
        if not vol_theme:
            risks.append({
                "level": "warning",
                "category": "volume-theme-missing",
                "volumeId": vol.get("id"),
                "message": "卷缺少明确主题",
                "suggestion": "为每卷定义明确的主题和目标"
            })

    # 检查章节数量是否合理
    total_chapters = sum(len(vol.get("chapters", [])) for vol in volumes)
    if total_chapters < 10:
        risks.append({
            "level": "info",
            "category": "chapter-count-low",
            "message": f"总章数较少（{total_chapters}章）",
            "suggestion": "确认是否能充分展开故事"
        })

    return {"issues": issues, "risks": risks}

def _review_character_architecture(
    entities: List[Dict[str, Any]],
    story_contract: Dict[str, Any],
    outline: Dict[str, Any]
) -> Dict[str, Any]:
    """审查角色架构"""

    issues = []
    risks = []

    # 检查是否有明确的主角
    protagonists = [e for e in entities if e.get("role") == "protagonist"]
    if not protagonists:
        issues.append({
            "level": "error",
            "category": "protagonist-missing",
            "message": "缺少明确的主角",
            "suggestion": "定义至少一个主角角色"
        })

    # 检查主角是否有明确的成长弧线
    for prot in protagonists:
        arc = prot.get("arc", {})
        if not arc or not arc.get("theme"):
            risks.append({
                "level": "warning",
                "category": "protagonist-arc-missing",
                "entityId": prot.get("id"),
                "entityName": prot.get("name"),
                "message": "主角缺少明确的成长弧线",
                "suggestion": "定义主角的角色弧线主题"
            })

    # 检查是否有足够的冲突关系
    relations = _count_relationship_types(entities)
    if relations.get("conflict", 0) < 2:
        risks.append({
            "level": "warning",
            "category": "conflict-insufficient",
            "message": "冲突关系较少，可能缺乏戏剧张力",
            "suggestion": "增加角色间的冲突关系"
        })

    return {"issues": issues, "risks": risks}

def _review_plot_architecture(
    outline: Dict[str, Any],
    story_contract: Dict[str, Any],
    foreshadowing: Dict[str, Any]
) -> Dict[str, Any]:
    """审查剧情架构"""

    issues = []
    risks = []

    # 检查是否有明确的伏笔计划
    foreshadows = foreshadowing.get("foreshadows", [])
    if len(foreshadows) < 3:
        risks.append({
            "level": "warning",
            "category": "foreshadow-insufficient",
            "message": f"伏笔数量较少（{len(foreshadows)}条）",
            "suggestion": "增加长期伏笔以支撑主线"
        })

    # 检查伏笔是否有明确的回收计划
    unresolved_without_schedule = [
        f for f in foreshadows
        if f.get("status") != "resolved" and not f.get("payoffPlan", {}).get("window")
    ]
    if len(unresolved_without_schedule) > len(foreshadows) * 0.5:
        issues.append({
            "level": "warning",
            "category": "foreshadow-unscheduled",
            "message": f"{len(unresolved_without_schedule)}条伏笔缺少回收计划",
            "suggestion": "为伏笔添加明确的回收窗口"
        })

    return {"issues": issues, "risks": risks}
```

### 4.6 伏笔强制约束

#### 问题分析

现有伏笔系统的问题：
1. 没有强制要求"每章必须埋钩子"
2. 没有检查"回收了但没埋"的情况
3. 伏笔债务累积不被重视

#### 解决方案

**在workflow中添加伏笔约束门禁**：

```python
# services/workflow_engine.py

def evaluate_foreshadow_gate(
    state: Dict[str, Any],
    chapter_id: str,
    strictness: str = "standard"
) -> Dict[str, Any]:
    """评估伏笔约束门禁"""

    foreshadowing = state.get("foreshadowing", {})
    foreshadows = foreshadowing.get("foreshadows", [])
    outline = state.get("outline", {})

    # 找到当前章节
    chapter = _find_chapter(outline, chapter_id)
    if not chapter:
        return {"ready": False, "reason": "chapter-not-found"}

    # 检查1：本章是否埋了新钩子
    planted_in_chapter = [
        f for f in foreshadows
        for plant in f.get("plantPoints", [])
        if plant.get("chapterId") == chapter_id
    ]

    min_plant_count = 1 if strictness == "standard" else 2
    if len(planted_in_chapter) < min_plant_count:
        return {
            "ready": False,
            "reason": "insufficient-foreshadows",
            "message": f"本章只埋了{len(planted_in_chapter)}个钩子（要求至少{min_plant_count}个）",
            "suggestion": "在本章增加埋钩点",
            "plantedCount": len(planted_in_chapter),
            "requiredCount": min_plant_count
        }

    # 检查2：是否有到期的伏笔需要回收
    due_foreshadows = [
        f for f in foreshadows
        if f.get("status") != "resolved" and _is_due_in_chapter(f, chapter_id)
    ]

    if due_foreshadows:
        # 检查是否有回收信号
        # （需要在review时检查，这里只做提醒）
        pass

    # 检查3：伏笔债务是否过多
    overdue_foreshadows = [
        f for f in foreshadows
        if f.get("status") != "resolved" and _is_overdue(f, chapter_id)
    ]

    max_overdue = 3 if strictness == "standard" else 5
    if len(overdue_foreshadows) > max_overdue:
        return {
            "ready": False,
            "reason": "foreshadow-debt",
            "message": f"伏笔债务过多（{len(overdue_foreshadows)}条逾期未回收）",
            "suggestion": "先回收部分逾期伏笔，或调整回收计划",
            "overdueCount": len(overdue_foreshadows),
            "maxAllowed": max_overdue
        }

    return {"ready": True}
```

---

## 5. 实现优先级

### P0 — 核心架构审查
1. `architecture review` 命令（setting/outline/characters/plot）
2. `review setting` 命令
3. `review outline` 命令
4. workflow gate 集成

### P1 — 写作辅助
5. `writing assist` 命令
6. `writing mention-check --auto-suggest` 命令
7. `writing mention-check --auto-apply` 命令

### P2 — 关系追踪
8. `writing relation-track --auto-detect` 命令
9. 关系演变历史查询

### P3 — 增强
10. 渐进式设定扩展（`setting expand --mode progressive`）
11. 伏笔强制约束集成到workflow
12. 多层级审查的UI可视化

---

## 6. 成功标准

1. **架构预防**：能在写作前发现80%的架构问题
2. **设定完善**：新项目通过`setting check-readiness`
3. **引用自动化**：写作时自动检测并建议@{}，减少90%手动操作
4. **关系追踪**：自动识别角色关系变化，准确率>70%
5. **多层审查**：4层审查体系全部可用，且结果能被workflow消费
6. **伏笔约束**：每章都有钩子，伏笔债务得到控制

---

## 7. 风险与限制

### 7.1 AI生成质量风险
- **风险**：自动检测和建议可能存在误报
- **缓解**：所有自动建议都需人工确认，提供confidence分数

### 7.2 过度结构化风险
- **风险**：多层审查可能让创作变得过于工程化
- **缓解**：
  - 提供minimal/standard/strict三种严格度
  - 允许通过`review-rules.yaml`豁免特定检查

### 7.3 性能风险
- **风险**：多层审查可能耗时较长
- **缓解**：
  - 支持增量审查（只审查变化部分）
  - 支持并行审查（独立层级可并行）

---

## 8. 后续扩展

1. **可视化关系图**：实时显示角色关系网络
2. **智能建议系统**：基于历史数据提供更精准的建议
3. **跨项目验证**：检查跨项目的设定一致性（针对系列作品）
4. **AI训练数据**：使用审查结果训练更好的质量模型
