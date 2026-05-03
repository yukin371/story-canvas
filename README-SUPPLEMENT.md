# Story Canvas README 补充文档

> 本文档包含2026-04-30实施的新功能说明，建议合并到主README中

---

## 主Agent与审查AI逻辑

### 主Agent（写作AI）职责

主Agent负责内容生成和创意输出，遵循以下约束：

**输入约束：**
- **上下文切片**：只接收"够写当前章"的最小上下文
- **风格配置**：严格遵循`style_profiles.yaml`中的术语、语域、框架策略
- **审查规则**：遵守`review_rules.yaml`中的启用规则和豁免配置
- **情绪契约**：确保核心情绪、禁止情绪、揭露偏好得到体现

**输出要求：**
- **结构化输出**：章节正文、beats、scenePlans分离管理
- **实体引用**：使用`@{实体名}`格式包裹所有已知实体
- **设定遵循**：严格遵守世界规则，不创造与设定冲突的内容
- **伏笔埋设**：按计划在指定章节埋设伏笔钩子

**质量控制：**
- **避免AI句式**：检测并避免"不是...是..."、"真正...从来都是..."等高频AI句式
- **移动端优化**：控制段落长度，适配移动端阅读体验
- **方案文档腔**：避免"目标：/风险：/约束："等结构化清单堆砌

### 审查AI（独立编辑）职责

审查AI负责质量评估和问题诊断，采用Clean-room模式：

#### 4层审查体系

**Level 1: 设定级审查** (`review-setting`)
- 检查世界规则完善度（数量+质量）
- 验证设定与核心承诺的一致性
- 评估角色/势力设定完备性
- 输出：设定完备度评分（0-15分）、问题清单、改进建议

**Level 2: 大纲级审查** (`review-outline`)
- 检查大纲与设定的一致性
- 验证伏笔埋点/回收窗口的有效性
- 评估剧情走向连贯性
- 检查角色弧线合理性
- 输出：大纲评分（0-15分）、问题清单、改进建议

**Level 3: 章节级审查** (`review chapter`)
- 评估5大维度：plotMomentum、characterPressure、conflictTension、sceneClarity、proseControl
- 检查设定遵循、角色行为逻辑一致性
- 验证章节承接质量
- 输出：结构化问题列表

**Level 4: 场景级审查** (`review scene`)
- 评估场景功能、连续性、逻辑性、伏笔细节
- 检查场景转换质量
- 输出：场景级结构化问题列表

#### 增强审查输出格式

所有层级审查都采用统一的问题诊断格式：

```json
{
  "issues": [
    {
      "severity": "critical|major|moderate|minor",
      "category": "plot|character|style|consistency|foreshadowing|handoff",
      "location": "问题描述位置",
      "description": "问题描述",
      "evidence": ["证据1", "证据2"],
      "suggestions": [
        {
          "suggestion": "改进建议",
          "example": "具体示例"
        }
      ]
    }
  ],
  "issueSummary": {
    "critical": 0,
    "major": 2,
    "moderate": 3,
    "minor": 1,
    "total": 6
  }
}
```

**严重级别定义：**
- `critical`：影响故事核心逻辑或设定基础
- `major`：显著影响读者体验
- `moderate`：可改进但不影响阅读
- `minor`：细节优化建议

#### Clean-room审查机制

**特点：**
- 使用独立的HTTP客户端，避免主Agent的提示词污染
- 通过`TEXT_PROVIDER_API_KEY`/`BASE_URL`环境变量配置
- 支持structured output（`json_object`格式）
- 提供issue-diagnosis-suggestion模式，而非简单评分

**流程：**
1. 构造独立审查prompt（包含章节全文+style分析+consistency信号）
2. 发送到外部provider
3. 解析返回的JSON对象
4. 归一为结构化问题列表

---

## 更新后的命令概览

### 项目管理
- `story-canvas init` - 初始化新项目
- `story-canvas project edit` - 编辑项目元数据
- `story-canvas doctor` - 项目健康检查

### 设定管理
- `story-canvas setting assess` - 评估设定完备性
- `story-canvas setting expand --mode progressive|targeted|brainstorm` - 渐进式扩展设定
- `story-canvas setting template [--list] [genre]` - 查看类型模板
- `story-canvas setting validate [chapter_id]` - 验证设定支持写作
- `story-canvas world add|list|check` - 世界设定管理
- `story-canvas entity create|enrich|review|list|show|graph` - 角色实体管理

### 大纲管理
- `story-canvas outline propose` - 生成初始大纲
- `story-canvas outline promote` - 提升提案为正史
- `story-canvas outline check` - 大纲一致性检查
- `story-canvas outline beat-add|beat-complete|beat-list` - 情节节点管理
- `story-canvas outline scene-add|scene-list|scene-detect|scene-update|scene-remove` - 场景计划管理
- `story-canvas outline detail-init|detail-show` - 详细大纲管理

### 架构审查（预防方向问题）
- `story-canvas architecture review --scope setting|outline|characters|plot|full` - 架构级审查
- `story-canvas review-setting --strictness minimal|standard|strict` - 设定级审查
- `story-canvas review-outline --check-consistency --check-foreshadowing` - 大纲级审查

### 写作与审查
- `story-canvas chapter write|analyze|suggest` - 章节写作与分析
- `story-canvas review apply` - 应用修改建议
- `story-canvas review chapter` - 章节级审查（增强版，含结构化问题）
- `story-canvas review scene` - 场景级审查（增强版，含结构化问题）
- `story-canvas review volume-self` - 卷级自我审查
- `story-canvas review volume-self-template` - 卷级自我审查模板

### 写作辅助
- `story-canvas writing assist --chapter-id <id>` - 全面写作辅助
- `story-canvas writing mention-check --chapter-id <id> --auto-suggest` - 检查缺失@{}
- `story-canvas writing mention-check --chapter-id <id> --auto-apply` - 自动应用@{}包裹
- `story-canvas writing relation-track --chapter-id <id> --auto-detect` - 追踪角色关系

### 状态与上下文
- `story-canvas projection apply` - 更新投影状态
- `story-canvas context refresh|show` - 刷新写作上下文
- `story-canvas workflow status|run|advance|reset|export` - 工作流管理

### 高级功能
- `story-canvas foreshadow plant|resolve|list` - 伏笔管理
- `story-canvas thread plant|resolve|list|check` - 线索管理
- `story-canvas arc define|milestone|list|check` - 角色弧线管理
- `story-canvas timeline add/list/check` - 时间线管理
- `story-canvas causality add/list/check` - 因果关系管理
- `story-canvas structure list|apply|show|check|map|scaffold` - 结构管理

### 风格与质量
- `story-canvas style check|constraints|report|repair` - 风格检查与修复
- `story-canvas consistency check` - 一致性检查
- `story-canvas search` - 跨章节搜索
- `story-canvas stats` - 项目统计

### 插画与导出
- `story-canvas illustration prompt|generate|list|config` - 插画生成
- `story-canvas export --format json|markdown|txt` - 文本导出
- `story-canvas export --format spec-outline|spec-characters|review-packet` - 专项导出

### 迁移与工具
- `story-canvas migrate` - 项目迁移
- `story-canvas brainstorm character|world|outline` - 头脑风暴

---

## 整体工作流

### 完整创作闭环

```
┌─────────────────────────────────────────────────────────────┐
│                     项目初始化阶段                            │
│  init → setting assess → setting expand → architecture review │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     架构验证阶段                              │
│  review-setting → review-outline → 设定/大纲迭代              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     大纲规划阶段                              │
│  outline propose → outline promote → projection apply        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     章节写作阶段                              │
│  context refresh → chapter write → chapter analyze           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     审查迭代阶段                              │
│  chapter suggest → review apply → writing assist             │
│    ↓                        ↓                               │
│  mention-check          relation-track                       │
│    ↓                        ↓                               │
│  auto-apply             更新关系状态                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     质量验证阶段                              │
│  review chapter → scene detect → review scene               │
│    ↓                                                           │
│  projection apply → context refresh                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
                         下一章节
```

### 设定扩展工作流

```bash
# 1. 评估设定完备性
story-canvas setting assess

# 2. 查看类型模板
story-canvas setting template --list
story-canvas setting template 奇幻

# 3. 渐进式扩展（4个阶段）
story-canvas setting expand --mode progressive --stage 1  # 核心确立
story-canvas setting expand --mode progressive --stage 2  # 基础架构
story-canvas setting expand --mode progressive --stage 3  # 历史传说
story-canvas setting expand --mode progressive --stage 4  # 细节深化

# 4. 验证设定支持写作
story-canvas setting validate chapter-001
```

### 架构审查工作流

```bash
# 1. 全面架构审查
story-canvas architecture review --scope full

# 2. 分项审查
story-canvas architecture review --scope setting
story-canvas architecture review --scope outline
story-canvas architecture review --scope characters
story-canvas architecture review --scope plot

# 3. 设定级深度审查
story-canvas review-setting --strictness standard

# 4. 大纲级深度审查
story-canvas review-outline --check-consistency --check-foreshadowing
```

### 单章创作闭环

```bash
# 1. 刷新写作上下文
story-canvas context refresh --chapter-id chapter-001

# 2. 写作（手动或AI）
# 编辑 chapters/chapter-001.md

# 3. 章节分析
story-canvas chapter analyze --chapter-id chapter-001

# 4. 生成建议
story-canvas chapter suggest --chapter-id chapter-001

# 5. 应用修改建议
story-canvas review apply --chapter-id chapter-001 --all-pending --decision accepted

# 6. 写作辅助
story-canvas writing assist --chapter-id chapter-001

# 7. 自动添加@{}包裹
story-canvas writing mention-check --chapter-id chapter-001 --auto-apply

# 8. 追踪关系变化
story-canvas writing relation-track --chapter-id chapter-001 --auto-detect

# 9. 更新投影状态
story-canvas projection apply --chapter-id chapter-001

# 10. 章节审查
story-canvas review chapter --chapter-id chapter-001

# 11. 场景检测与审查
story-canvas outline scene-detect --chapter-id chapter-001
story-canvas review scene --chapter-id chapter-001 --scene-index 1

# 12. 迭代优化
# 根据审查结果修改正文，重复步骤3-11
```

### 新项目完整工作流示例

```bash
# ========== 阶段1: 项目初始化 ==========
# 创建新项目（带完整商业定位）
story-canvas init \
  --root ./my-novel \
  --title "夜巡收煞录" \
  --genre "奇幻" \
  --primary-genre fantasy \
  --sub-genre urban-occult \
  --core-promise "每章结尾保留追读钩子" \
  --pace-contract "中快节奏" \
  --premise "夜班接尸人继承城隍夜巡牌，处理都市异案并追查失踪父亲真相" \
  --target-platform qidian \
  --serialization-model "2到3章一个单元异案，持续抬升主线阴谋" \
  --release-cadence "日更两章" \
  --chapter-word-floor 2000 \
  --chapter-word-target 3000

# ========== 阶段2: 设定扩展 ==========
# 评估设定完备性
story-canvas setting assess --root ./my-novel

# 查看类型模板
story-canvas setting template --root ./my-novel --list
story-canvas setting template --root ./my-novel 奇幻

# 渐进式扩展设定
story-canvas setting expand --root ./my-novel --mode progressive --auto

# 验证设定支持写作
story-canvas setting validate --root ./my-novel

# ========== 阶段3: 架构审查 ==========
# 全面架构审查
story-canvas architecture review --root ./my-novel --scope full

# 设定级深度审查
story-canvas review-setting --root ./my-novel --strictness standard

# 大纲级深度审查
story-canvas review-outline --root ./my-novel --check-consistency

# ========== 阶段4: 大纲规划 ==========
# 生成初始大纲
story-canvas outline propose --root ./my-novel

# 提升为正史大纲
story-canvas outline promote --root ./my-novel --all-pending

# 更新投影状态
story-canvas projection apply --root ./my-novel

# ========== 阶段5: 章节创作 ==========
# 刷新写作上下文
story-canvas context refresh --root ./my-novel --chapter-id chapter-001

# 手动写作（编辑 chapters/chapter-001.md）
# ...

# 章节分析
story-canvas chapter analyze --root ./my-novel --chapter-id chapter-001

# 生成建议
story-canvas chapter suggest --root ./my-novel --chapter-id chapter-001

# 写作辅助
story-canvas writing assist --root ./my-novel --chapter-id chapter-001

# 自动添加@{}包裹
story-canvas writing mention-check --root ./my-novel --chapter-id chapter-001 --auto-apply

# 追踪关系变化
story-canvas writing relation-track --root ./my-novel --chapter-id chapter-001 --auto-detect

# 应用修改建议
story-canvas review apply --root ./my-novel --chapter-id chapter-001 --all-pending --decision accepted

# 更新投影状态
story-canvas projection apply --root ./my-novel --chapter-id chapter-001

# 章节审查
story-canvas review chapter --root ./my-novel --chapter-id chapter-001

# 场景检测
story-canvas outline scene-detect --root ./my-novel --chapter-id chapter-001

# 场景审查
story-canvas review scene --root ./my-novel --chapter-id chapter-001 --scene-index 1

# 迭代优化（根据审查结果）
# ...

# ========== 阶段6: 继续下一章 ==========
# 重复阶段5的操作
```

---

## 类型模板系统

项目内置7种类型模板，每种包含：

- **核心承诺**：该类型的故事核心要素
- **设定要素**：必须包含的世界设定
- **扩展阶段**：4阶段渐进式扩展指导

### 支持的类型

1. **奇幻 (fantasy)**
   - 魔法体系、种族、地理、政治、神器
   - 4阶段：核心承诺→世界架构→历史传说→细节深化

2. **科幻 (scifi)**
   - 科技发展、社会结构、宇宙观、AI
   - 4阶段：核心科技→社会形态→宇宙文明→未来细节

3. **武侠 (wuxia)**
   - 武功体系、江湖规矩、历史背景、江湖地点
   - 4阶段：武功体系→江湖势力→历史背景→江湖细节

4. **都市奇幻 (urban_fantasy)**
   - 隐藏世界、现代魔法、实体引用、双世界互动
   - 4阶段：隐藏世界→超自然社区→交汇点→都市魔法

5. **言情 (romance)**
   - 角色背景、社会环境、关系发展、成长细节
   - 4阶段：人物背景→社会环境→关系发展→成长细节

6. **悬疑 (mystery)**
   - 谜题核心、线索布局、嫌疑人网络、真相构建
   - 4阶段：谜题核心→线索布局→角色网络→真相构建

7. **恐怖 (horror)**
   - 恐惧源、受困环境、心理压力、恐怖升级
   - 4阶段：恐惧源→受困环境→心理压力→恐怖升级

---

## 已实现功能（更新）

当前实现已经覆盖：

- ✅ **分层文件协议**：正文、提案、审查、投影、上下文
- ✅ **章节分析、建议生成**，以及"先审再应用"的显式流程
- ✅ **4层审查体系**：设定、大纲、章节、场景全覆盖
- ✅ **增强审查输出**：结构化问题诊断（issue-diagnosis-suggestion模式）
- ✅ **类型模板系统**：7种类型，4阶段渐进式扩展
- ✅ **设定扩展功能**：渐进式、目标式、头脑风暴三种模式
- ✅ **架构预防机制**：设定/大纲/角色/剧情4维度架构审查
- ✅ **写作辅助自动化**：@{}自动检测/应用、关系追踪
- ✅ **章节评审、场景评审、风格评审**，以及profile驱动约束
- ✅ **Clean-room独立审查**：避免主Agent提示词污染
- ✅ **outline-first gate、beat跟踪、scene plan维护**
- ✅ **project positioning、story contract、emotional contract校验**
- ✅ **worldbook / foreshadowing / threads / timeline / causality跟踪**
- ✅ **entity enrich、review、list、show、relationship graph导出**
- ✅ **workflow阶段推断、gate decision、reset/export**
- ✅ **provider-backed的插图prompt、生成、资产管理**

---

## 后续改进方向（更新）

下一轮应继续聚焦：

- ✅ ~~在早期UI并行推进的同时，继续提升结构化故事状态的人类审查体验~~（已完成）
- ✅ ~~把插图资产管理收敛到Story Canvas的视觉界面轨道~~（已完成）
- ✅ ~~继续加深review和workflow对故事约束的消费~~（已完成）
- ✅ ~~扩充题材模板与工作流模板~~（已完成）
- 🔄 **稳定provider层**，补一到两个真实可用集成
- 🔄 **继续把算法、词典、prompt资源外部化**
- 🔄 **加强长篇状态下的schema/workflow校验**
- 🔄 **在命令契约与样例稳定后，推进release/distribution**

---

**更新日期：** 2026-04-30
**版本：** v1.1.0
**新增功能：** 架构审查系统、设定扩展、写作辅助、增强审查输出
