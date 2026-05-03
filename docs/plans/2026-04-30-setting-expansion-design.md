# Story Canvas — 设定扩展与大纲细化设计

> Date: 2026-04-30
> Status: Draft
> Scope: 设定扩展命令、题材模板系统、大纲细化工具、设定完善度门禁

---

## 1. 问题陈述

### 1.1 现有流程的痛点

在实际项目初始化过程中，AI生成的设定往往过于简短：

**世界观设定问题**：
- `worldbook.yaml` 中的 `worldRules` 通常只有1-2条简单规则
- 缺少世界细节（地理、势力、历史背景）
- 力量体系描述模糊（如"有修真体系"但没有具体境界划分）

**角色卡问题**：
- `entities.yaml` 只有角色名和基本身份
- 缺少外貌、性格、背景故事
- 缺少角色关系网络
- 主角没有成长弧线设计

**势力设定问题**：
- `factions.yaml` 只有势力名称
- 缺少势力目标、手段、冲突关系
- 缺少势力内部结构

**大纲问题**：
- `outline.yaml` 的 `direction` 通常是一句话
- `beats` 为空或过于简略
- `scenePlans` 缺失
- 缺少从"一句话"到"详细大纲"的渐进扩展机制

### 1.2 根本原因分析

1. **brainstorm 命令过于随机**：
   - `brainstorm character` 生成的内容不与项目定位、故事契约绑定
   - 生成的是孤立角色，没有考虑角色关系网络

2. **缺少题材模板系统**：
   - 没有为不同题材提供设定模板
   - AI需要从零开始推导设定细节

3. **outline gate 只检查存在性**：
   - `outline check` 只检查 `direction`/`beats`/`scenePlans` 是否存在
   - 不检查内容质量和详细程度

4. **缺少"设定完善度"门禁**：
   - workflow 中没有强制要求详细设定的机制
   - 可以跳过设定完善直接进入写作

5. **缺少渐进式扩展机制**：
   - 从"一句话核心承诺"到"详细设定"缺少中间步骤
   - 从"一句话大纲"到"详细细纲"缺少扩展工具

---

## 2. 设计目标

1. **提供设定扩展工具**：从核心承诺自动推导详细设定
2. **建立题材模板系统**：为不同题材提供设定基准
3. **增强 brainstorm**：基于项目定位生成建议
4. **添加大纲细化工具**：从一句话扩展到详细细纲
5. **建立设定完善度门禁**：强制要求关键设定的详细程度

---

## 3. 整体架构

### 3.1 新增工作流阶段

```
init -> story_gate -> setting_expansion -> outline_expansion -> context_ready -> drafting
         ↓              ↓                   ↓
      [检查定位]    [扩展设定]          [细化大纲]
                     ↓                   ↓
                  [模板系统]          [beats/scenes]
```

### 3.2 新增命令组

```bash
# 设定扩展命令
story-canvas setting expand --target worldbook|entities|factions
story-canvas setting check-readiness

# 大纲细化命令
story-canvas outline expand-beats
story-canvas outline expand-scenes

# 增强 brainstorm
story-canvas brainstorm character --context-based
story-canvas brainstorm world --context-based
```

---

## 4. 核心设计

### 4.1 设定扩展命令 (`setting expand`)

#### 功能描述

基于项目的核心承诺和定位，自动推导详细设定。

#### 命令接口

```bash
# 扩展世界观设定
story-canvas setting expand --target worldbook \
  --focus "力量体系|地理|势力关系" \
  --based-on "核心承诺：现代都市修真，隐藏世界与普通世界共存"

# 扩展角色卡
story-canvas setting expand --target entities \
  --entity-id protagonist \
  --focus "外貌|性格|背景|成长弧线" \
  --based-on "主角：夜班接尸人，继承城隍夜巡牌"

# 扩展势力设定
story-canvas setting expand --target factions \
  --faction-id ghost-hunters \
  --focus "目标|手段|内部结构|冲突关系" \
  --based-on "接尸行会：管理生死边界的古老组织"
```

#### 输出示例

**worldbook 扩展**：
```yaml
worldbook:
  worldRules:
    - id: "cultivation-realm"
      category: "power-system"
      summary: "修真境界体系"
      details:
        - "炼气期：感应灵气，淬炼肉身"
        - "筑基期：筑造道基，寿元两百"
        - "金丹期：结成金丹，寿元五百"
        - "元婴期：元婴出窍，寿元千载"
      breakthroughConditions:
        - from: "炼气期"
          to: "筑基期"
          condition: "需要筑基丹辅助，且灵气积累满"
        - from: "筑基期"
          to: "金丹期"
          condition: "需要凝结金丹雏形，且心性过关"

    - id: "modern-hidden-world"
      category: "world-structure"
      summary: "隐藏世界与普通世界共存"
      details:
        - "隐藏世界：修真者、异能者、妖怪等超自然存在的社区"
        - "普通世界：普通人类生活的表面社会"
        - "边界管理：接尸行会负责处理跨越边界的异常"
        - "保密协议：普通人发现异常会被消除记忆"

  locations:
    - id: "hidden-city"
      name: "隐城"
      type: "hidden-settlement"
      description: "位于城市地下的修真者聚居地"
      features:
        - "灵气浓度比地表高3倍"
        - "有专门的灵材交易市场"
        - "设有接尸行会分会"
```

**entities 扩展**：
```yaml
entities:
  - id: "protagonist"
    name: "林舟"
    role: "protagonist"

    # 基础信息（brainstorm 阶段已有）
    seed:
      archetype: "reluctant-hero"
      motivation: "追查失踪父亲真相"
      background: "夜班接尸人，意外继承城隍夜巡牌"

    # 扩展后的详细信息
    profile:
      appearance:
        age: "24岁"
        height: "178cm"
        build: "偏瘦但结实"
        features:
          - "黑发，略微凌乱"
          - "眼睛：深棕色，熬夜时有血丝"
          - "皮肤：偏白，常年夜班导致缺乏日照"
          - "特征：左手手腕有城隍印（继承后出现）"
        clothing:
          - "工作服：黑色冲锋衣，多口袋设计"
          - "配饰：玉质城隍牌（挂在胸前）"

      personality:
        traits:
          - name: "冷静"
            description: "长期处理尸体培养出的职业素养"
            evidence: "面对突发灵异事件时能迅速判断"
          - name: "固执"
            description: "对父亲失踪一事执着"
            evidence: "即使危险也要追查线索"
          - name: "善良"
            description: "虽然外表冷漠，但会帮助无辜者"
            evidence: "多次冒险保护普通人"
        flaws:
          - "过于执着，容易忽视自身安全"
          - "不善表达情感，显得冷漠"

      background:
        - "父亲：林啸天，前任城隍夜巡，五年前失踪"
        - "母亲：早逝"
        - "职业：夜班接尸人（接尸行会底层成员）"
        - "经历：从小被父亲教导处理灵异事件，但父亲从不让他涉足深层秘密"

      growthArc:
        currentStage: "被迫接受"
        nextStage: "主动承担"
        finalStage: "真正传承"
        milestones:
          - stage: "被迫接受"
            description: "被迫上岗，只想完成父亲未竟之事"
            triggers: ["继承城隍牌", "首次夜巡"]
          - stage: "主动承担"
            description: "理解父亲的责任，主动守护城市"
            triggers: ["发现父亲失踪真相", "第一次主动救人"]
          - stage: "真正传承"
            description: "超越父亲，成为新的城隍夜巡传奇"
            triggers: ["击败最终反派", "建立新的秩序"]

      abilities:
        - name: "夜巡之力"
          level: "初期觉醒"
          description: "城隍牌赋予的力量，可以看见灵体、束缚恶鬼"
          progression:
            - stage: "炼气期"
              capabilities: ["看见灵体", "简单束缚术"]
            - stage: "筑基期"
              capabilities: ["灵力外放", "符箓术", "初步御鬼"]
            - stage: "金丹期"
              capabilities: ["城隍法相", "生死边界掌控", "鬼神契约"]

      relationships:
        - target: "father"
          type: "family"
          label: "父子（追寻）"
          description: "父亲失踪，林舟一直在追查真相"
        - target: "mentor"
          type: "mentor"
          label: "师徒（传承）"
          description: "父亲的师父，现任接尸行会会长"
```

#### 技术实现

**新增 service**：
- `services/setting_expander.py`：核心扩展逻辑
- `services/genre_template_resolver.py`：题材模板解析器

**核心算法**：
```python
def expand_worldbook(
    state: Dict[str, Any],
    focus: str,
    based_on: str
) -> Dict[str, Any]:
    """基于核心承诺扩展世界观设定"""

    # 1. 解析题材
    positioning = state["project"]["positioning"]
    primary_genre = positioning.get("primaryGenre")
    sub_genre = positioning.get("subGenre")

    # 2. 加载题材模板
    template = load_genre_template(primary_genre, sub_genre)

    # 3. 基于核心承诺生成设定
    core_promises = state["project"]["storyContract"]["corePromises"]
    world_rules = generate_world_rules(
        template=template,
        core_promises=core_promises,
        focus=focus
    )

    # 4. 生成地理、势力等详细设定
    locations = generate_locations(template, focus)
    factions = generate_factions(template, focus)

    return {
        "worldRules": world_rules,
        "locations": locations,
        "factions": factions
    }
```

### 4.2 题材模板系统

#### 目录结构

```
data/genre-templates/
├── _base.yaml                      # 基础模板（所有题材共享）
├── xuanhuan.yaml                   # 玄幻题材
├── xianxia.yaml                    # 仙侠题材
├── urban-occult.yaml               # 都市异能
├── wuxia.yaml                      # 武侠题材
├── mystery.yaml                    # 悬疑推理
├── romance.yaml                    # 言情题材
└── sci-fi.yaml                     # 科幻题材
```

#### 模板结构示例

```yaml
# data/genre-templates/xuanhuan.yaml
id: "xuanhuan"
name: "玄幻"
description: "以东方幻想为背景，强调力量体系和冒险"

# 世界规则模板
worldRules:
  powerSystem:
    template: "力量体系：{base_level} -> {next_level}，突破需要{condition}"
    examples:
      - "炼气期 -> 筑基期，突破需要筑基丹和灵气积累"
      - "筑基期 -> 金丹期，突破需要凝结金丹雏形"
      - "金丹期 -> 元婴期，突破需要元婴出窍契机"
    requiredFields:
      - "境界名称"
      - "能力描述"
      - "突破条件"
      - "寿元限制"

  worldStructure:
    template: "世界结构：{visible_world} + {hidden_world}"
    examples:
      - "表面世界：普通人类生活；隐藏世界：修真者社区"
      - "凡人界：低武世界；修真界：高武世界"

# 角色成长弧线模板
characterArcs:
  protagonist:
    template: "{archetype}：从{start_state}，通过{method}，达到{end_state}"
    examples:
      - archetype: "废柴流"
        start_state: "天赋极差，被人轻视"
        method: "奇遇 + 努力 + 机缘"
        end_state: "同阶无敌，震惊世人"
      - archetype: "重生流"
        start_state: "带着前世记忆重生"
        method: "利用先知优势 + 弥补遗憾"
        end_state: "改变命运，保护重要的人"
      - archetype: "隐藏流"
        start_state: "表面普通，实则强大"
        method: "扮猪吃虎 + 关键时刻出手"
        end_state: "身份暴露，震慑四方"

# 势力模板
factions:
  template: "{name}：{goal}，{method}，{conflict}"
  examples:
    - name: "正道联盟"
      goal: "维护修真界秩序"
      method: "联合围剿魔道，建立规矩"
      conflict: "与魔道势不两立"
    - name: "魔道宗门"
      goal: "突破正道束缚，追求力量极致"
      method: "不择手段，修炼禁术"
      conflict: "与正道常年对抗"
    - name: "散修联盟"
      goal: "保护散修利益"
      method: "互助合作，共享资源"
      conflict: "被宗门势力排挤"

# 冲突类型模板
conflicts:
  powerStruggle:
    template: "{side1}与{side2}争夺{resource}"
    examples:
      - "正道与魔道争夺灵脉"
      - "宗门之间争夺地盘"
      - "修真者争夺天材地宝"

  secretReveal:
    template: "主角发现{secret}，引发{consequence}"
    examples:
      - "发现父亲失踪真相，被势力追杀"
      - "发现自身身世秘密，陷入身份危机"
      - "发现世界真相，世界观崩塌"
```

### 4.3 增强 brainstorm

#### 改进点

1. **基于项目定位生成**：不再随机生成，而是基于 `project.positioning` 和 `storyContract.corePromises`
2. **生成角色关系图**：不只生成孤立角色，而是生成角色网络
3. **生成角色成长弧线**：不只是静态描述，而是包含成长路径

#### 新命令接口

```bash
# 生成与项目定位匹配的角色建议
story-canvas brainstorm character --context-based \
  --archetype "reluctant-hero" \
  --role "protagonist" \
  --alignment "现代都市修真" \
  --include-relationships

# 输出示例
{
  "suggestions": [
    {
      "name": "林舟",
      "role": "protagonist",
      "archetype": "reluctant-hero",
      "motivation": "追查失踪父亲真相",
      "background": "夜班接尸人，意外继承城隍夜巡牌",
      "growthArc": {
        "currentStage": "被迫接受",
        "nextStage": "主动承担",
        "finalStage": "真正传承"
      },
      "relationships": [
        {
          "target": "父亲",
          "type": "family",
          "label": "父子（追寻）",
          "description": "父亲失踪，林舟一直在追查真相"
        },
        {
          "target": "师父",
          "type": "mentor",
          "label": "师徒（传承）",
          "description": "父亲的师父，引导林舟继承夜巡职责"
        }
      ]
    }
  ]
}
```

### 4.4 大纲细化命令

#### `outline expand-beats`

把一句话 `direction` 扩展为 3-5 个 `beats`。

```bash
story-canvas outline expand-beats --chapter-id chapter-001 \
  --target-beat-count 5
```

**输入**：
```yaml
direction: "林舟夜班时接到特殊任务：护送一具'特殊尸体'，途中遭遇袭击，发现尸体与父亲失踪有关"
```

**输出**：
```yaml
beats:
  - id: "beat-001-1"
    summary: "夜班开始，接到特殊任务"
    details:
      - "林舟在太平间例行检查"
      - "行会会长突然出现，交付特殊任务"
      - "尸体标记为'特级异常'，要求护送到隐城"
    pov: "protagonist"
    keyEntities: ["protagonist", "mentor"]
    status: "planned"

  - id: "beat-001-2"
    summary: "护送途中遭遇第一次袭击"
    details:
      - "运输车经过跨江大桥时被拦截"
      - "袭击者身份不明，使用禁术"
      - "林舟首次使用城隍牌力量反击"
    pov: "protagonist"
    keyEntities: ["protagonist", "unknown-attackers"]
    status: "planned"

  - id: "beat-001-3"
    summary: "发现尸体异常，与父亲产生关联"
    details:
      - "尸体身上有父亲留下的记号"
      - "记号是父子暗号，暗示这是父亲留下的线索"
      - "林舟意识到任务不是护送，是追寻"
    pov: "protagonist"
    keyEntities: ["protagonist", "father", "corpse"]
    status: "planned"

  - id: "beat-001-4"
    summary: "抵达隐城，遭遇更强大的敌人"
    details:
      - "隐城入口处被设伏"
      - "敌人目标明确，就是要这具尸体"
      - "林舟被迫与尸体'绑定'，共同对敌"
    pov: "protagonist"
    keyEntities: ["protagonist", "enemy-faction"]
    status: "planned"

  - id: "beat-001-5"
    summary: "发现尸体真相，悬念收尾"
    details:
      - "尸体'苏醒'，原来不是尸体而是重伤的父亲"
      - "父亲无法直接说话，只能通过意识传递信息"
      - "林舟明白自己已经被卷入巨大阴谋"
    pov: "protagonist"
    keyEntities: ["protagonist", "father"]
    status: "planned"
```

#### `outline expand-scenes`

把每个 `beat` 扩展为具体 `scenes`。

```bash
story-canvas outline expand-scenes --chapter-id chapter-001 \
  --target-scenes-per-beat 2
```

**技术实现**：
```python
def expand_beats_to_scenes(
    beats: List[Dict[str, Any]],
    target_scenes_per_beat: int
) -> List[Dict[str, Any]]:
    """把 beats 扩展为 scenes"""

    scenes = []
    for beat in beats:
        beat_summary = beat["summary"]
        beat_details = beat.get("details", [])

        # 基于 beat 的冲突类型生成 scenes
        conflict_type = detect_conflict_type(beat_summary)

        if conflict_type == "action":
            # 动作场景：铺垫 -> 冲突 -> 高潮 -> 结局
            scene_templates = [
                {"type": "setup", "summary": f"为{beat_summary}做铺垫"},
                {"type": "confrontation", "summary": f"{beat_summary}爆发"},
                {"type": "climax", "summary": f"{beat_summary}达到高潮"},
                {"type": "resolution", "summary": f"{beat_summary}暂时解决"}
            ]
        elif conflict_type == "investigation":
            # 侦查场景：发现线索 -> 分析推理 -> 得出结论
            scene_templates = [
                {"type": "discovery", "summary": f"发现与{beat_summary}相关的线索"},
                {"type": "analysis", "summary": f"分析{beat_summary}的含义"},
                {"type": "conclusion", "summary": f"得出{beat_summary}的结论"}
            ]
        else:
            # 默认场景
            scene_templates = [
                {"type": "beginning", "summary": f"{beat_summary}的开始"},
                {"type": "development", "summary": f"{beat_summary}的发展"},
                {"type": "end", "summary": f"{beat_summary}的结束"}
            ]

        for i, template in enumerate(scene_templates[:target_scenes_per_beat]):
            scene_id = f"scene-{beat['id']}-{i+1}"
            scenes.append({
                "id": scene_id,
                "title": template["summary"],
                "summary": template["summary"],
                "type": template["type"],
                "sourceBeatId": beat["id"],
                "status": "planned"
            })

    return scenes
```

### 4.5 设定完善度门禁

#### 新增 workflow gate

```python
# services/workflow_engine.py
def evaluate_setting_readiness(
    state: Dict[str, Any],
    strictness: str = "standard"  # minimal | standard | strict
) -> Dict[str, Any]:
    """检查设定完善度"""

    worldbook = state.get("worldbook", {})
    entities = state.get("entities", [])
    factions = state.get("factions", [])
    positioning = state.get("project", {}).get("positioning", {})
    story_contract = state.get("project", {}).get("storyContract", {})

    missing = []
    next_actions = []

    # 检查世界规则
    world_rules = worldbook.get("worldRules", [])
    min_world_rules = 3 if strictness == "standard" else 5
    if len(world_rules) < min_world_rules:
        missing.append({
            "code": "insufficient-world-rules",
            "message": f"世界规则不足{min_world_rules}条（当前{len(world_rules)}条）"
        })
        next_actions.append(
            f"运行 `story-canvas setting expand --target worldbook` "
            f"补充世界规则到至少{min_world_rules}条"
        )

    # 检查主角设定
    protagonist = next((e for e in entities if e.get("role") == "protagonist"), None)
    if not protagonist:
        missing.append({
            "code": "missing-protagonist",
            "message": "缺少主角设定"
        })
        next_actions.append(
            "运行 `story-canvas brainstorm character --role protagonist` 生成主角"
        )
    else:
        # 检查主角详细信息
        profile = protagonist.get("profile", {})
        if not profile.get("appearance"):
            missing.append({
                "code": "missing-protagonist-appearance",
                "message": "主角缺少外貌描述"
            })
            next_actions.append(
                "运行 `story-canvas setting expand --target entities --entity-id protagonist --focus appearance`"
            )
        if not profile.get("personality"):
            missing.append({
                "code": "missing-protagonist-personality",
                "message": "主角缺少性格描述"
            })
            next_actions.append(
                "运行 `story-canvas setting expand --target entities --entity-id protagonist --focus personality`"
            )
        if not profile.get("growthArc"):
            missing.append({
                "code": "missing-protagonist-growth-arc",
                "message": "主角缺少成长弧线"
            })
            next_actions.append(
                "运行 `story-canvas setting expand --target entities --entity-id protagonist --focus growth-arc`"
            )

    # 检查势力设定
    if not factions:
        missing.append({
            "code": "missing-factions",
            "message": "缺少势力设定"
        })
        next_actions.append(
            "运行 `story-canvas brainstorm world --focus factions` 生成势力"
        )
    else:
        # 检查势力详细信息
        for faction in factions[:3]:  # 检查前3个势力
            if not faction.get("goal"):
                missing.append({
                    "code": "missing-faction-goal",
                    "message": f"势力 {faction.get('name')} 缺少目标描述"
                })

    # 检查大纲详细程度
    outline = state.get("outline", {})
    chapters = _iter_outline_chapters(outline)
    chapters_without_beats = [
        ch for ch in chapters
        if not ch.get("beats")
    ]
    if chapters_without_beats:
        missing.append({
            "code": "chapters-without-beats",
            "message": f"{len(chapters_without_beats)}个章节缺少 beats"
        })
        next_actions.append(
            f"运行 `story-canvas outline expand-beats --chapter-id <chapter-id>` "
            f"为这些章节补充 beats"
        )

    ready = len(missing) == 0

    return {
        "ready": ready,
        "strictness": strictness,
        "missing": missing,
        "nextActions": next_actions,
        "summary": {
            "worldRulesCount": len(world_rules),
            "entitiesCount": len(entities),
            "factionsCount": len(factions),
            "chaptersWithBeats": len(chapters) - len(chapters_without_beats),
            "totalChapters": len(chapters)
        }
    }
```

---

## 5. 实现优先级

### P0 — 核心扩展能力
1. 题材模板系统（`data/genre-templates/`）
2. `setting expand` 基础命令（worldbook 扩展）
3. `setting check-readiness` 命令

### P1 — 角色扩展
4. `setting expand` entities 扩展
5. 增强 brainstorm character（基于项目定位）

### P2 — 大纲细化
6. `outline expand-beats` 命令
7. `outline expand-scenes` 命令

### P3 — 增强
8. workflow gate 集成
9. 势力扩展（`setting expand` factions）
10. 渐进式扩展UI（未来）

---

## 6. 风险与限制

### 6.1 AI生成质量风险
- **风险**：生成的设定可能质量不稳定
- **缓解**：
  - 提供题材模板作为基准
  - 支持人工review和修改
  - 提供`--dry-run`选项预览生成内容

### 6.2 过度设定风险
- **风险**：生成过多设定，限制创作自由度
- **缓解**：
  - 支持`--focus`参数选择性扩展
  - 提供`--minimal`模式只生成必要设定
  - 允许删除和覆盖生成的设定

### 6.3 题材模板覆盖度
- **风险**：模板可能无法覆盖所有题材细分
- **缓解**：
  - 提供模板继承和组合机制
  - 支持项目级自定义模板
  - 逐步扩充内置模板库

---

## 7. 成功标准

1. **设定完善度**：新项目初始化后，`setting check-readiness` 能通过
2. **大纲详细程度**：章节具备3-5个beats，每个beat具备2-3个scenes
3. **题材适配度**：生成的设定符合题材特点（如玄幻有境界体系）
4. **创作自由度**：生成的设定不限制作者后续创作
5. **工具可用性**：命令接口清晰，输出格式易于理解

---

## 8. 后续扩展

1. **可视化关系图**：生成角色关系图、势力关系图
2. **设定一致性检查**：检查设定之间是否存在矛盾
3. **设定版本管理**：跟踪设定的修改历史
4. **设定推荐引擎**：基于已有设定推荐补充内容
5. **跨项目设定复用**：支持在不同项目间复用设定
