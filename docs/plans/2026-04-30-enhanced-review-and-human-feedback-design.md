# Story Canvas — 审查AI增强与人工审查集成设计

> Date: 2026-04-30
> Status: Draft
> Scope: 审查AI能力增强、Provider复用、人工审查WebUI集成

---

## 1. 背景与问题

### 1.1 现有审查系统的限制

通过深入分析现有代码，发现以下问题：

**问题1：审查只给评分，不给具体建议**
- 现有`review chapter`/`review scene`输出大量评分
- 但缺少"哪里有问题"、"怎么改"的具体指导
- 用户需要自己从评分中推断问题，效率低下

**问题2：依赖外部Agent工具的审查能力**
- 现有流程依赖Claude Code、Codex等外部Agent工具
- 这些工具自带的提示词可能污染审查标准
- 无法保证审查标准的一致性

**问题3：人工审查体验割裂**
- 人工审查需要在不同工具间切换
- Agent工具中审查，然后在网页中查看评分
- 缺少统一的审查界面

### 1.2 设计目标

1. **审查AI能力增强**：从评分转向具体的、可操作的建议
2. **Provider复用**：复用现有text provider infrastructure做审查
3. **人工审查集成**：为webui添加统一的人工审查界面

---

## 2. 审查AI能力增强

### 2.1 现有审查输出的问题

**现有输出示例**：
```json
{
  "scores": {
    "推进": 12,
    "压力": 8,
    "冲突": 10,
    "逻辑": 14,
    "伏笔与回收": 11
  },
  "contractAlignment": {
    "matched": ["情绪推进明显"],
    "risks": ["伏笔回收信号偏弱"]
  }
}
```

**问题**：
- 用户需要自己理解"压力8分"是什么意思
- "伏笔回收信号偏弱"没有告诉用户哪里弱、怎么改
- 缺少具体的修改建议

### 2.2 新的审查输出格式

**设计原则**：
1. **问题导向**：明确指出"哪里有问题"
2. **建议导向**：给出"怎么改"的具体建议
3. **证据导向**：提供"为什么有问题"的证据

**新的输出格式**：
```json
{
  "overallAssessment": {
    "grade": "B",
    "summary": "本章在推进和逻辑方面表现良好，但伏笔回收和角色刻画需要加强",
    "readyForNext": true
  },
  "issues": [
    {
      "id": "issue-001",
      "severity": "medium",
      "category": "伏笔回收",
      "location": "第3-5段",
      "description": "本章有2条伏笔进入回收窗口，但兑现信号偏弱",
      "evidence": [
        "伏笔'归墟体是封印活钥匙'应在本章有进展",
        "第3段只提到了归墟体的存在，没有推进相关线索"
      ],
      "suggestions": [
        {
          "priority": "high",
          "action": "add-foreshadow-progress",
          "description": "在第3段增加主角对归墟体的思考或探索",
          "example": "林舟按住胸口的城隍牌，能感觉到它与体内归墟体的共鸣越来越强。这意味着...（接下文）"
        },
        {
          "priority": "medium",
          "action": "strengthen-payoff-signal",
          "description": "在第5段增加一个明确的线索推进",
          "example": "他在归墟体的共鸣中看到了一闪而过的画面：父亲留下的符号..."
        }
      ]
    },
    {
      "id": "issue-002",
      "severity": "low",
      "category": "角色刻画",
      "location": "第7段",
      "description": "主角情绪反应不够充分",
      "evidence": [
        "主角得知重要信息，但情绪描写过于平淡",
        "与emotionalContract中要求的'压迫下反制'不符"
      ],
      "suggestions": [
        {
          "priority": "medium",
          "action": "deepen-emotional-response",
          "description": "增加主角的内心冲突和身体反应",
          "example": "林舟的手指微微颤抖，不是因为恐惧，而是因为...（补充情绪反应）"
        }
      ]
    }
  ],
  "strengths": [
    {
      "category": "推进",
      "description": "本章主线推进明显，节奏紧凑",
      "evidence": ["第1-2段快速进入冲突", "第6-8段完成阶段性目标"]
    },
    {
      "category": "逻辑",
      "description": "场景转换自然，逻辑链条清晰",
      "evidence": ["从接尸到遇袭的转场合理", "动作序列符合逻辑"]
    }
  ]
}
```

### 2.3 审查AI能力实现

**核心设计**：

```python
# services/enhanced_review.py

def build_enhanced_chapter_review(
    state: Dict[str, Any],
    chapter_id: str,
    chapter_text: str,
    analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """增强的章节审查，提供具体建议"""

    # 1. 基础评分（保留现有逻辑）
    dimension_map = build_chapter_review(
        state, chapter_id, chapter_text, analysis
    )

    # 2. 基于评分生成问题诊断
    issues = _generate_issue_diagnoses(
        state, chapter_id, chapter_text, dimension_map
    )

    # 3. 为每个问题生成具体建议
    for issue in issues:
        suggestions = _generate_suggestions_for_issue(
            state, chapter_id, chapter_text, issue
        )
        issue["suggestions"] = suggestions

    # 4. 识别优点
    strengths = _identify_strengths(dimension_map)

    # 5. 生成总体评估
    overall = _generate_overall_assessment(
        issues, strengths, dimension_map
    )

    return {
        "overallAssessment": overall,
        "issues": issues,
        "strengths": strengths,
        "dimensionScores": dimension_map  # 保留评分供参考
    }

def _generate_issue_diagnoses(
    state: Dict[str, Any],
    chapter_id: str,
    chapter_text: str,
    dimension_map: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """基于评分生成问题诊断"""

    issues = []
    issue_id = 0

    # 检查每个维度
    for dimension_name, dimension_result in dimension_map.items():
        score = dimension_result.get("score", 0)

        # 低分维度生成问题诊断
        if score < 12:
            issue = {
                "id": f"issue-{issue_id:03d}",
                "severity": "high" if score < 10 else "medium",
                "category": _translate_dimension_name(dimension_name),
                "score": score,
                "description": dimension_result.get("comment", ""),
                "evidence": [],
                "suggestions": []
            }

            # 添加具体证据
            evidence = _collect_evidence_for_low_score(
                state, chapter_id, chapter_text, dimension_name, dimension_result
            )
            issue["evidence"] = evidence

            issues.append(issue)
            issue_id += 1

    return issues

def _generate_suggestions_for_issue(
    state: Dict[str, Any],
    chapter_id: str,
    chapter_text: str,
    issue: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """为问题生成具体建议"""

    category = issue["category"]
    suggestions = []

    if category == "伏笔与回收":
        suggestions.extend(_generate_foreshadow_suggestions(
            state, chapter_id, chapter_text, issue
        ))
    elif category == "角色刻画":
        suggestions.extend(_generate_character_suggestions(
            state, chapter_id, chapter_text, issue
        ))
    elif category == "逻辑":
        suggestions.extend(_generate_logic_suggestions(
            state, chapter_id, chapter_text, issue
        ))
    elif category == "推进":
        suggestions.extend(_generate_pace_suggestions(
            state, chapter_id, chapter_text, issue
        ))

    return suggestions

def _generate_foreshadow_suggestions(
    state: Dict[str, Any],
    chapter_id: str,
    chapter_text: str,
    issue: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """生成伏笔相关的具体建议"""

    suggestions = []

    # 获取当前章的到期伏笔
    foreshadowing = state.get("foreshadowing", {})
    due_foreshadows = [
        f for f in foreshadowing.get("foreshadows", [])
        if f.get("status") != "resolved" and _is_due_in_chapter(f, chapter_id)
    ]

    for foreshadow in due_foreshadows[:3]:  # 最多处理3条
        suggestion = {
            "priority": "high",
            "action": "advance-foreshadow",
            "targetForeshadowId": foreshadow.get("id"),
            "targetForeshadowTitle": _get_foreshadow_title(foreshadow),
            "description": f"推进伏笔：{foreshadow.get('description', '')}",
            "specificSuggestions": [
                f"在本章增加关于'{foreshadow.get('description', '')}'的线索或进展",
                f"考虑让相关角色（{_get_related_entities(foreshadow)}）提及或探索这条线索",
                f"如果这是回收章节，确保给出明确的兑现信号"
            ],
            "exampleLocation": _suggest_location_for_foreshadow(
                state, chapter_id, foreshadow
            )
        }
        suggestions.append(suggestion)

    return suggestions

def _suggest_location_for_foreshadow(
    state: Dict[str, Any],
    chapter_id: str,
    foreshadow: Dict[str, Any]
) -> str:
    """建议在章节的哪个位置插入伏笔推进"""

    outline = state.get("outline", {})
    chapter = _find_chapter(outline, chapter_id)

    if not chapter:
        return "章节中部"

    # 分析章节结构
    beats = chapter.get("beats", [])

    if len(beats) == 0:
        return "章节中部"

    # 建议在第二个beat之后插入
    if len(beats) >= 2:
        return f"在第{beats[1].get('summary', '')}之后"
    else:
        return "章节中部"

def _identify_strengths(
    dimension_map: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """识别优点"""

    strengths = []

    for dimension_name, dimension_result in dimension_map.items():
        score = dimension_result.get("score", 0)

        if score >= 14:
            strength = {
                "category": _translate_dimension_name(dimension_name),
                "description": dimension_result.get("comment", ""),
                "evidence": dimension_result.get("matched", [])
            }
            strengths.append(strength)

    return strengths

def _generate_overall_assessment(
    issues: List[Dict[str, Any]],
    strengths: List[Dict[str, Any]],
    dimension_map: Dict[str, Any]
) -> Dict[str, Any]:
    """生成总体评估"""

    # 计算平均分
    scores = [d.get("score", 0) for d in dimension_map.values()]
    avg_score = sum(scores) / len(scores) if scores else 0

    # 确定等级
    if avg_score >= 14:
        grade = "A"
        summary = "本章表现优秀，可以直接进入下一章"
    elif avg_score >= 12:
        grade = "B"
        summary = "本章整体良好，有少量可改进之处"
    elif avg_score >= 10:
        grade = "C"
        summary = "本章基本合格，建议修正主要问题后再推进"
    else:
        grade = "D"
        summary = "本章存在较多问题，建议重点修改"

    # 判断是否可以进入下一章
    high_severity_issues = [i for i in issues if i.get("severity") == "high"]
    ready_for_next = len(high_severity_issues) == 0

    return {
        "grade": grade,
        "averageScore": avg_score,
        "summary": summary,
        "readyForNext": ready_for_next,
        "blockingIssues": len(high_severity_issues)
    }
```

---

## 3. Provider复用：用Text Provider做审查

### 3.1 现有Provider Infrastructure

现有系统已有完善的provider infrastructure：
- `OpenAITextHTTPClient`：支持任意OpenAI兼容API
- `build_response_request`：构造标准化的provider请求
- `generate_text`：统一的文本生成接口

### 3.2 审查Provider设计

**核心思路**：
- 复用现有text provider infrastructure
- 审查prompt由系统生成，不依赖外部agent工具
- 保持clean-room，避免提示词污染

**实现**：

```python
# services/review_provider.py

def build_review_provider_prompt(
    state: Dict[str, Any],
    chapter_id: str,
    chapter_text: str,
    review_type: str  # "enhanced-chapter" | "enhanced-scene" | "setting" | "outline"
) -> Dict[str, Any]:
    """为审查构造provider prompt"""

    if review_type == "enhanced-chapter":
        return _build_enhanced_chapter_review_prompt(
            state, chapter_id, chapter_text
        )
    elif review_type == "enhanced-scene":
        return _build_enhanced_scene_review_prompt(
            state, chapter_id, chapter_text
        )
    # ... 其他审查类型

def _build_enhanced_chapter_review_prompt(
    state: Dict[str, Any],
    chapter_id: str,
    chapter_text: str
) -> Dict[str, Any]:
    """构造增强章节审查的provider prompt"""

    # 收集上下文
    context = _collect_review_context(state, chapter_id)

    # 构造system prompt
    system_prompt = f"""你是一位专业的小说审查专家，擅长识别小说中的问题并提供具体的修改建议。

你的任务是审查第{chapter_id}章，输出格式必须是JSON对象，包含以下结构：
{{
  "issues": [
    {{
      "severity": "high|medium|low",
      "category": "伏笔与回收|角色刻画|逻辑|推进|风格",
      "location": "具体段落或位置",
      "description": "问题描述",
      "evidence": ["证据1", "证据2"],
      "suggestions": [
        {{
          "priority": "high|medium|low",
          "action": "具体操作类型",
          "description": "修改建议描述",
          "example": "修改示例"
        }}
      ]
    }}
  ],
  "strengths": [
    {{
      "category": "优点类别",
      "description": "优点描述",
      "evidence": ["证据"]
    }}
  ]
}}

审查重点：
{context["reviewFocus"]}

项目背景：
{context["projectBackground"]}

本章目标：
{context["chapterGoal"]}

情绪契约：
{context["emotionalContract"]}
"""

    # 构造user prompt
    user_prompt = f"""请审查以下章节：

章节ID：{chapter_id}

章节正文：
{chapter_text}

相关上下文：
活跃角色：{context["activeCharacters"]}
当前状态：{context["currentStates"]}
到窗伏笔：{context["dueForeshadows"]}

请按照上述JSON格式输出审查结果。"""

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "review_type": "enhanced-chapter",
        "context": context
    }

def call_review_provider(
    state: Dict[str, Any],
    prompt_payload: Dict[str, Any],
    provider: str = "openai",
    model: str = "gpt-4o",
    temperature: float = 0.7
) -> Dict[str, Any]:
    """调用provider执行审查"""

    from story_harness_cli.providers.text import OpenAITextHTTPClient
    from story_harness_cli.providers.text import resolve_api_key, resolve_base_url

    api_key = resolve_api_key("")
    base_url = resolve_base_url("")

    client = OpenAITextHTTPClient(api_key=api_key, base_url=base_url)

    request = client.build_response_request(
        system_prompt=prompt_payload["system_prompt"],
        user_prompt=prompt_payload["user_prompt"],
        model=model,
        temperature=temperature
    )

    try:
        result = client.generate_text(request)
        text = result.get("text", "")

        # 解析JSON输出
        parsed = parse_text_provider_json_object(text)

        return {
            "success": True,
            "provider": provider,
            "model": model,
            "responseId": result.get("responseId", ""),
            "result": parsed,
            "rawText": text
        }
    except Exception as exc:
        return {
            "success": False,
            "provider": provider,
            "model": model,
            "error": str(exc)
        }

# 新增CLI命令

def command_review_with_provider(args) -> int:
    """使用provider执行审查"""

    root = Path(args.root).resolve()
    ensure_project_root(root)
    state = load_project_state(root)

    chapter_id = args.chapter_id or state["project"].get("activeChapterId")
    if not chapter_id:
        raise SystemExit("缺少 chapter id")

    chapter_file = chapter_path(root, chapter_id)
    if not chapter_file.exists():
        raise SystemExit(f"章节不存在: {chapter_file}")

    chapter_text = chapter_file.read_text(encoding="utf-8")

    # 构造provider prompt
    prompt_payload = build_review_provider_prompt(
        state, chapter_id, chapter_text,
        args.review_type or "enhanced-chapter"
    )

    # 调用provider
    result = call_review_provider(
        state, prompt_payload,
        provider=args.provider or "openai",
        model=args.model or "gpt-4o",
        temperature=args.temperature or 0.7
    )

    if not result["success"]:
        print(json.dumps({
            "error": "Provider调用失败",
            "details": result.get("error")
        }, ensure_ascii=False, indent=2))
        return 1

    # 保存审查结果
    review_result = {
        "chapterId": chapter_id,
        "reviewType": args.review_type or "enhanced-chapter",
        "provider": result["provider"],
        "model": result["model"],
        "responseId": result["responseId"],
        "generatedAt": now_iso(),
        "result": result["result"]
    }

    # 保存到reviews目录
    reviews_dir = root / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)

    review_file = reviews_dir / f"{chapter_id}-provider-review.json"
    review_file.write_text(
        json.dumps(review_result, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # 输出结果
    print(json.dumps({
        "chapterId": chapter_id,
        "reviewFile": str(review_file),
        "provider": result["provider"],
        "model": result["model"],
        "responseId": result["responseId"],
        "result": result["result"]
    }, ensure_ascii=False, indent=2))

    return 0
```

---

## 4. 人工审查集成

### 4.1 现有人工审查的问题

**问题1：审查体验割裂**
- 在Agent工具中审查 → 生成评分文件 → 在网页中查看
- 缺少统一的审查界面

**问题2：无法直接输入评审意见**
- 只能查看评分，无法直接在系统中添加人工评审
- 需要手动编辑YAML文件

**问题3：审查历史不完整**
- 缺少审查版本的追踪
- 无法看到"AI审查 → 人工修正 → 最终版本"的演变

### 4.2 人工审查系统设计

#### 4.2.1 数据结构

**新增审查记录结构**：

```yaml
# reviews/review-sessions.yaml
reviewSessions:
  - id: "review-session-001"
    chapterId: "chapter-001"
    type: "enhanced-chapter"
    status: "in-progress"  # "in-progress" | "completed" | "cancelled"

    # AI审查结果
    aiReview:
      provider: "openai"
      model: "gpt-4o"
      responseId: "resp-xxx"
      generatedAt: "2026-04-30T10:00:00Z"
      result:
        issues: [...]
        strengths: [...]
        overallAssessment: {...}

    # 人工审查输入
    humanReview:
      reviewerId: "human-reviewer-001"
      startedAt: "2026-04-30T10:05:00Z"

      # 人工对AI审查的反馈
      aiFeedback:
        agreedIssues: ["issue-001", "issue-002"]
        disagreedIssues: []
        newIssues: []

      # 人工评分
      scores:
       推进: 13  # 修改AI评分
        压力: 9
        冲突: 11
        逻辑: 14
        伏笔与回收: 12

      # 人工具体意见
      comments:
        - issueId: "issue-001"
          content: "同意AI的判断，在第3-5段确实需要加强伏笔信号"
          action: "accept"
        - issueId: "manual-001"
          category: "节奏"
          severity: "low"
          content: "个人感觉第6段节奏稍快，可以考虑加一些过渡"
          location: "第6段"
          suggestions:
            - action: "add-transition"
              description: "在动作之间加一两句过渡"
              example: "林舟刚站稳，就听到..."

    # 最终审查结论
    finalDecision:
      grade: "B+"
      readyForNext: true
      blockingIssues: []
      nextActions: ["加强伏笔信号", "微调第6段节奏"]
      decidedAt: "2026-04-30T10:15:00Z"
      decidedBy: "human-reviewer-001"

    # 审查历史
    history:
      - timestamp: "2026-04-30T10:00:00Z"
        event: "ai-review-completed"
        details: {...}
      - timestamp: "2026-04-30T10:05:00Z"
        event: "human-review-started"
        details: {...}
      - timestamp: "2026-04-30T10:15:00Z"
        event: "review-completed"
        details: {...}
```

#### 4.2.2 WebUI审查界面

**新增WebUI API端点**：

```python
# 新增审查API

# POST /api/review/start-session
async def start_review_session(request):
    """启动一个新的审查会话"""
    data = await request.json()

    root = Path(data["root"])
    chapter_id = data["chapterId"]
    review_type = data.get("reviewType", "enhanced-chapter")
    use_provider = data.get("useProvider", False)

    # 生成AI审查
    if use_provider:
        # 调用provider生成审查
        prompt_payload = build_review_provider_prompt(
            state, chapter_id, chapter_text, review_type
        )
        ai_result = call_review_provider(state, prompt_payload)
    else:
        # 使用本地审查逻辑
        ai_result = build_enhanced_chapter_review(
            state, chapter_id, chapter_text, analysis
        )

    # 创建审查会话
    session_id = f"review-session-{stable_hash(now_iso())}"
    session = {
        "id": session_id,
        "chapterId": chapter_id,
        "type": review_type,
        "status": "in-progress",
        "aiReview": ai_result,
        "humanReview": {
            "reviewerId": "webui-user",
            "startedAt": now_iso(),
            "comments": []
        },
        "history": [
            {
                "timestamp": now_iso(),
                "event": "session-created",
                "details": {"provider": use_provider}
            }
        ]
    }

    # 保存会话
    _save_review_session(root, session)

    return jsonify({
        "sessionId": session_id,
        "chapterId": chapter_id,
        "aiReview": session["aiReview"]
    })

# GET /api/review/session/{session_id}
async def get_review_session(session_id):
    """获取审查会话详情"""
    root = Path(request.args["root"])
    session = _load_review_session(root, session_id)

    if not session:
        return jsonify({"error": "Session not found"}), 404

    return jsonify(session)

# POST /api/review/session/{session_id}/feedback
async def submit_feedback(session_id):
    """提交人工审查反馈"""
    data = await request.json()

    root = Path(request.args["root"])
    session = _load_review_session(root, session_id)

    if not session:
        return jsonify({"error": "Session not found"}), 404

    # 更新人工审查反馈
    session["humanReview"].update({
        "aiFeedback": data.get("aiFeedback", {}),
        "scores": data.get("scores", {}),
        "comments": data.get("comments", [])
    })

    _save_review_session(root, session)

    return jsonify({"success": True})

# POST /api/review/session/{session_id}/complete
async def complete_review(session_id):
    """完成审查，生成最终结论"""
    data = await request.json()

    root = Path(request.args["root"])
    session = _load_review_session(root, session_id)

    if not session:
        return jsonify({"error": "Session not found"}), 404

    # 生成最终结论
    final_decision = _generate_final_decision(
        session["aiReview"],
        session["humanReview"]
    )

    session["finalDecision"] = final_decision
    session["status"] = "completed"
    session["humanReview"]["decidedAt"] = now_iso()

    # 添加历史记录
    session["history"].append({
        "timestamp": now_iso(),
        "event": "review-completed",
        "details": final_decision
    })

    _save_review_session(root, session)

    return jsonify(final_decision)
```

**WebUI审查界面设计**：

```html
<!-- 审查界面组件 -->
<div class="review-interface">
  <!-- 左侧：章节内容 -->
  <div class="chapter-content">
    <h3>章节内容</h3>
    <div class="content-display">
      {{chapter_text}}
    </div>
  </div>

  <!-- 右侧：审查面板 -->
  <div class="review-panel">
    <h3>审查面板</h3>

    <!-- AI审查结果 -->
    <div class="ai-review-section">
      <h4>AI审查结果</h4>

      <!-- 总体评估 -->
      <div class="overall-assessment">
        <div class="grade-badge">{{ai_review.overallAssessment.grade}}</div>
        <p>{{ai_review.overallAssessment.summary}}</p>
      </div>

      <!-- 问题列表 -->
      <div class="issues-list">
        <h5>发现的问题 ({{ai_review.issues.length}})</h5>

        {% for issue in ai_review.issues %}
        <div class="issue-card" data-issue-id="{{issue.id}}">
          <div class="issue-header">
            <span class="severity-badge {{issue.severity}}">
              {{issue.severity}}
            </span>
            <span class="category-badge">{{issue.category}}</span>
          </div>

          <div class="issue-description">
            {{issue.description}}
          </div>

          <div class="issue-evidence">
            <strong>证据：</strong>
            <ul>
              {% for evidence in issue.evidence %}
              <li>{{evidence}}</li>
              {% endfor %}
            </ul>
          </div>

          <div class="issue-suggestions">
            <strong>建议：</strong>
            {% for suggestion in issue.suggestions %}
            <div class="suggestion-card">
              <div class="suggestion-priority">
                优先级: {{suggestion.priority}}
              </div>
              <div class="suggestion-description">
                {{suggestion.description}}
              </div>
              <div class="suggestion-example">
                <strong>示例：</strong>
                <pre>{{suggestion.example}}</pre>
              </div>

              <!-- 操作按钮 -->
              <div class="suggestion-actions">
                <button class="btn-apply-suggestion"
                        data-issue-id="{{issue.id}}"
                        data-suggestion-index="{{loop.index}}">
                  应用此建议
                </button>
                <button class="btn-edit-suggestion">
                  编辑建议
                </button>
              </div>
            </div>
            {% endfor %}
          </div>

          <!-- 人工反馈选项 -->
          <div class="human-feedback">
            <label>
              <input type="checkbox"
                     name="agree-issue-{{issue.id}}"
                     checked>
              同意此问题
            </label>
            <label>
              <input type="checkbox"
                     name="disagree-issue-{{issue.id}}">
              不同意此问题
            </label>
          </div>
        </div>
        {% endfor %}
      </div>

      <!-- 优点列表 -->
      <div class="strengths-list">
        <h5>优点 ({{ai_review.strengths.length}})</h5>
        {% for strength in ai_review.strengths %}
        <div class="strength-card">
          <span class="category-badge">{{strength.category}}</span>
          <p>{{strength.description}}</p>
        </div>
        {% endfor %}
      </div>
    </div>

    <!-- 人工审查输入 -->
    <div class="human-review-section">
      <h4>人工审查</h4>

      <!-- 人工评分 -->
      <div class="human-scores">
        <h5>评分</h5>
        {% for dimension in ["推进", "压力", "冲突", "逻辑", "伏笔与回收"] %}
        <div class="score-input">
          <label>{{dimension}}:</label>
          <input type="range"
                 name="score-{{dimension}}"
                 min="0" max="15"
                 value="{{ai_review.dimensionScores[dimension].score}}"
                 class="score-slider">
          <span class="score-value">{{ai_review.dimensionScores[dimension].score}}</span>
        </div>
        {% endfor %}
      </div>

      <!-- 人工意见 -->
      <div class="human-comments">
        <h5>人工意见</h5>

        <!-- 添加新意见 -->
        <div class="add-comment-form">
          <textarea id="new-comment-content"
                    placeholder="输入人工审查意见..."></textarea>

          <div class="comment-meta">
            <select id="new-comment-category">
              <option value="节奏">节奏</option>
              <option value="逻辑">逻辑</option>
              <option value="角色">角色</option>
              <option value="风格">风格</option>
              <option value="其他">其他</option>
            </select>

            <select id="new-comment-severity">
              <option value="low">轻微</option>
              <option value="medium">中等</option>
              <option value="high">严重</option>
            </select>

            <button id="btn-add-comment">添加意见</button>
          </div>
        </div>

        <!-- 已有意见列表 -->
        <div class="comments-list" id="comments-list">
          <!-- 动态加载 -->
        </div>
      </div>

      <!-- 审查操作 -->
      <div class="review-actions">
        <button id="btn-save-draft" class="btn-secondary">
          保存草稿
        </button>
        <button id="btn-complete-review" class="btn-primary">
          完成审查
        </button>
      </div>
    </div>
  </div>
</div>
```

#### 4.2.3 审查工作流

```javascript
// 审查界面交互逻辑

class ReviewInterface {
  constructor(sessionId, chapterId) {
    this.sessionId = sessionId;
    this.chapterId = chapterId;
    this.sessionData = null;

    this.init();
  }

  async init() {
    // 加载会话数据
    await this.loadSession();

    // 渲染AI审查结果
    this.renderAIReview();

    // 绑定事件
    this.bindEvents();
  }

  async loadSession() {
    const response = await fetch(`/api/review/session/${this.sessionId}`);
    this.sessionData = await response.json();
  }

  renderAIReview() {
    const aiReview = this.sessionData.aiReview;

    // 渲染总体评估
    this.renderOverallAssessment(aiReview.overallAssessment);

    // 渲染问题列表
    this.renderIssues(aiReview.issues);

    // 渲染优点列表
    this.renderStrengths(aiReview.strengths);
  }

  renderIssues(issues) {
    const container = document.getElementById('issues-list');

    issues.forEach((issue, index) => {
      const issueCard = document.createElement('div');
      issueCard.className = 'issue-card';
      issueCard.dataset.issueId = issue.id;

      issueCard.innerHTML = `
        <div class="issue-header">
          <span class="severity-badge ${issue.severity}">${issue.severity}</span>
          <span class="category-badge">${issue.category}</span>
        </div>
        <div class="issue-description">${issue.description}</div>
        <div class="issue-evidence">
          <strong>证据：</strong>
          <ul>
            ${issue.evidence.map(e => `<li>${e}</li>`).join('')}
          </ul>
        </div>
        <div class="issue-suggestions">
          ${issue.suggestions.map((suggestion, sIndex) => `
            <div class="suggestion-card">
              <div class="suggestion-priority">优先级: ${suggestion.priority}</div>
              <div class="suggestion-description">${suggestion.description}</div>
              <div class="suggestion-example">
                <strong>示例：</strong>
                <pre>${suggestion.example}</pre>
              </div>
              <div class="suggestion-actions">
                <button class="btn-apply-suggestion"
                        data-issue-id="${issue.id}"
                        data-suggestion-index="${sIndex}">
                  应用此建议
                </button>
                <button class="btn-edit-suggestion">
                  编辑建议
                </button>
              </div>
            </div>
          `).join('')}
        </div>
        <div class="human-feedback">
          <label>
            <input type="checkbox"
                   name="agree-issue-${issue.id}"
                   checked>
            同意此问题
          </label>
          <label>
            <input type="checkbox"
                   name="disagree-issue-${issue.id}">
            不同意此问题
          </label>
        </div>
      `;

      container.appendChild(issueCard);
    });
  }

  bindEvents() {
    // 应用建议按钮
    document.querySelectorAll('.btn-apply-suggestion').forEach(btn => {
      btn.addEventListener('click', (e) => {
        this.applySuggestion(e.target);
      });
    });

    // 保存草稿按钮
    document.getElementById('btn-save-draft').addEventListener('click', () => {
      this.saveDraft();
    });

    // 完成审查按钮
    document.getElementById('btn-complete-review').addEventListener('click', () => {
      this.completeReview();
    });

    // 添加意见按钮
    document.getElementById('btn-add-comment').addEventListener('click', () => {
      this.addHumanComment();
    });

    // 评分滑块
    document.querySelectorAll('.score-slider').forEach(slider => {
      slider.addEventListener('input', (e) => {
        const valueSpan = e.target.nextElementSibling;
        valueSpan.textContent = e.target.value;
      });
    });
  }

  async applySuggestion(button) {
    const issueId = button.dataset.issueId;
    const suggestionIndex = button.dataset.suggestionIndex;

    const issue = this.sessionData.aiReview.issues.find(i => i.id === issueId);
    const suggestion = issue.suggestions[suggestionIndex];

    // 这里应该调用后端API应用建议到章节文本
    const confirmed = confirm(
      `确定要应用此建议吗？\n\n` +
      `操作：${suggestion.action}\n` +
      `描述：${suggestion.description}\n\n` +
      `示例：\n${suggestion.example}`
    );

    if (confirmed) {
      try {
        const response = await fetch('/api/review/apply-suggestion', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            sessionId: this.sessionId,
            issueId: issueId,
            suggestionIndex: suggestionIndex
          })
        });

        const result = await response.json();

        if (result.success) {
          alert('建议已应用');
          // 刷新显示
          await this.loadSession();
        } else {
          alert('应用失败：' + result.error);
        }
      } catch (error) {
        alert('应用失败：' + error.message);
      }
    }
  }

  async saveDraft() {
    const feedback = this.collectHumanFeedback();

    try {
      const response = await fetch(`/api/review/session/${this.sessionId}/feedback`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(feedback)
      });

      const result = await response.json();

      if (result.success) {
        alert('草稿已保存');
      } else {
        alert('保存失败：' + result.error);
      }
    } catch (error) {
      alert('保存失败：' + error.message);
    }
  }

  async completeReview() {
    const feedback = this.collectHumanFeedback();

    // 确认完成
    const confirmed = confirm(
      '确定要完成审查吗？\n\n' +
      '完成后将生成最终审查结论，无法再修改。'
    );

    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch(`/api/review/session/${this.sessionId}/complete`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(feedback)
      });

      const result = await response.json();

      if (result.grade) {
        alert(`审查已完成！\n\n最终评级：${result.grade}\n` +
                `是否可以进入下一章：${result.readyForNext ? '是' : '否'}\n` +
                `阻塞问题数：${result.blockingIssues}`);

        // 跳转到审查总结页面
        window.location.href = `/review/summary/${this.sessionId}`;
      } else {
        alert('完成失败：' + result.error);
      }
    } catch (error) {
      alert('完成失败：' + error.message);
    }
  }

  collectHumanFeedback() {
    // 收集人工反馈
    const feedback = {
      aiFeedback: {
        agreedIssues: [],
        disagreedIssues: []
      },
      scores: {},
      comments: []
    };

    // 收集问题同意/不同意
    document.querySelectorAll('input[name^="agree-issue-"]').forEach(checkbox => {
      const issueId = checkbox.name.replace('agree-issue-', '');
      if (checkbox.checked && checkbox.name.includes('agree-issue-')) {
        feedback.aiFeedback.agreedIssues.push(issueId);
      }
    });

    document.querySelectorAll('input[name^="disagree-issue-"]').forEach(checkbox => {
      const issueId = checkbox.name.replace('disagree-issue-', '');
      if (checkbox.checked) {
        feedback.aiFeedback.disagreedIssues.push(issueId);
      }
    });

    // 收集评分
    document.querySelectorAll('.score-slider').forEach(slider => {
      const dimension = slider.name.replace('score-', '');
      feedback.scores[dimension] = parseInt(slider.value);
    });

    // 收集人工意见
    document.querySelectorAll('.human-comment-card').forEach(commentCard => {
      feedback.comments.push({
        category: commentCard.dataset.category,
        severity: commentCard.dataset.severity,
        content: commentCard.dataset.content,
        location: commentCard.dataset.location
      });
    });

    return feedback;
  }
}
```

---

## 5. 实现优先级

### P0 — 审查AI增强
1. `build_enhanced_chapter_review` 函数
2. `_generate_issue_diagnoses` 函数
3. `_generate_suggestions_for_issue` 函数
4. 新的审查输出格式

### P1 — Provider复用
5. `build_review_provider_prompt` 函数
6. `call_review_provider` 函数
7. `command_review_with_provider` 命令

### P2 — 人工审查基础
8. 审查会话数据结构
9. 审查会话保存/加载函数
10. CLI命令：`review start-session`、`review complete`

### P3 — WebUI集成
11. WebUI API端点
12. 审查界面组件
13. 审查工作流JavaScript逻辑

---

## 6. 成功标准

1. **审查AI能力**：审查输出包含至少3个具体建议，每个建议都有"问题描述+证据+修改示例"
2. **Provider复用**：审查可以通过text provider执行，不依赖外部agent工具
3. **人工审查体验**：在WebUI中完成从AI审查到人工审查的完整流程，无需切换工具
4. **审查历史**：完整记录"AI审查 → 人工反馈 → 最终结论"的演变过程

---

## 7. 风险与限制

### 7.1 Provider成本风险
- **风险**：使用text provider做审查会增加API成本
- **缓解**：
  - 提供dry-run模式，只生成prompt不调用API
  - 支持本地审查逻辑作为fallback
  - 提供cost估算，让用户预估成本

### 7.2 审查质量一致性
- **风险**：不同provider的审查质量可能不一致
- **缓解**：
  - 标准化审查prompt模板
  - 提供审查质量评估指标
  - 支持多个provider交叉验证

### 7.3 人工审查工作量
- **风险**：人工审查界面复杂，增加学习成本
- **缓解**：
  - 提供渐进式复杂度（简单模式 → 详细模式）
  - 提供键盘快捷键提高效率
  - 提供审查模板和预设选项
