# Story Canvas WebUI 简化集成方案

> 目标：将NovelGenerator的核心写作逻辑融入现有WebUI
> 原则：最小改动，聚焦写作体验
> 状态：探索性草案，不是当前执行入口；不得按本文直接向 base install 添加第三方依赖

---

> 2026-05-03 口径更新：当前仓库仍以 stdlib-only base + optional extras 为依赖边界。本文中的 ChromaDB 示例只能作为 future optional lane 参考；真实实施必须先补 extras 设计、builtin fallback 和离线 smoke test。

## 当前WebUI架构分析

### 现有结构
```
ui/src/
├── App.vue                    # 主应用
├── main.ts                    # 入口
├── api/
│   └── storyCanvas.ts         # API接口定义
├── views/
│   ├── SettingsView.vue       # 设置管理
│   ├── DashboardView.vue      # 仪表盘
│   ├── ChaptersView.vue       # 章节管理
│   ├── IllustrationView.vue   # 插画工作区
│   ├── WorkbenchView.vue      # 工作台（review/illustration）
│   └── workbench/             # 工作台子组件
├── composables/
│   └── useWorkspace.ts        # 工作区状态管理
└── components/                # 通用组件
```

### 现有功能
- ✅ 项目管理（打开、新建、切换）
- ✅ 设定管理（PROJECT.md、实体）
- ✅ 章节管理（列表、编辑）
- ✅ 插画生成
- ✅ 审查功能

---

## 集成NovelGenerator核心功能

### 重点1: 向量检索 - 增强上下文感知

**目标：** 写作时自动获取相关前文

**实现方式：**

1. **后端：向量存储服务**
```python
# src/story_harness_cli/services/vector/vector_store.py
class VectorStore:
    """向量存储 - 基于ChromaDB"""

    def add_chapter(self, chapter_id: str, chapter_text: str):
        """添加章节到向量库"""
        # 分段并索引
        chunks = self._split_text(chapter_text)
        for i, chunk in enumerate(chunks):
            self.collection.add(
                documents=[chunk],
                ids=[f"{chapter_id}_chunk_{i}"],
                metadatas=[{"chapter": chapter_id, "chunk": i}]
            )

    def get_relevant_context(self, chapter_id: str, n=3) -> List[str]:
        """获取相关前文"""
        # 语义搜索获取最相关的前N章片段
        results = self.collection.query(
            query_texts=[f"chapter {chapter_id}"],
            n_results=n*10,
            where={"chapter": {"$ne": chapter_id}}
        )
        # 去重并返回
        return self._deduplicate_results(results)
```

2. **后端：增强写作辅助API**
```python
# src/story_harness_cli/api/endpoints.py
from fastapi import APIRouter, HTTPException
from ..services.vector.vector_store import VectorStore

router = APIRouter()

@router.get("/api/writing/assist/{chapter_id}")
async def get_writing_assist(chapter_id: str, root: str):
    """获取写作辅助 - 增强版（包含向量检索上下文）"""
    state = load_state(root)

    # 加载章节文本
    chapter_file = chapter_path(root, chapter_id)
    chapter_text = chapter_file.read_text()

    # 新增：向量检索相关上下文
    vector_store = VectorStore(root)
    try:
        relevant_context = vector_store.get_relevant_context(chapter_id, n=3)
        context_text = "\n".join(relevant_context)
    except:
        context_text = ""

    # 构建辅助建议
    assistance = build_writing_assistance(
        state, chapter_id, chapter_text,
        context=context_text  # 传入上下文
    )

    return {
        "chapterId": chapter_id,
        "context": context_text,
        "assistance": assistance
    }
```

3. **前端：增强写作界面**
```typescript
// ui/src/composables/useWritingAssist.ts
import { computed, ref } from "vue";
import { storyCanvasAPI } from "@/api/storyCanvas";

export function useWritingAssist(projectRoot: string, chapterId: Ref<string>) {
  const loading = ref(false);
  const context = ref("");
  const suggestions = ref<any>(null);

  const fetchAssist = async () => {
    loading.value = true;
    try {
      const response = await storyCanvasAPI.getWritingAssist(
        projectRoot,
        chapterId.value
      );
      context.value = response.context;
      suggestions.value = response.assistance;
    } finally {
      loading.value = false;
    }
  };

  return {
    loading,
    context,
    suggestions,
    fetchAssist
  };
}
```

---

### 重点2: 多阶段生成工作流

**目标：** 设定 → 大纲 → 章节 → 定稿的完整流程

**实现方式：**

1. **后端：多阶段生成服务**
```python
# src/story_harness_cli/services/multi_stage_generator.py
class MultiStageGenerator:
    """多阶段生成器"""

    def __init__(self, project_root: str, llm_provider):
        self.project_root = project_root
        self.llm = llm_provider
        self.vector_store = VectorStore(project_root)

    def stage1_generate_setting(
        self,
        topic: str,
        genre: str,
        num_chapters: int
    ) -> dict:
        """阶段1: 生成设定"""
        prompt = f"""
        基于以下信息生成小说设定：
        - 主题：{topic}
        - 类型：{genre}
        - 章节数：{num_chapters}

        请生成包含以下内容的设定：
        1. 核心承诺
        2. 情绪契约
        3. 商业定位
        4. 故事简介
        5. 第一卷规划
        """
        setting = self.llm.generate(prompt)

        # 保存设定
        setting_file = os.path.join(self.project_root, "PROJECT.md")
        with open(setting_file, 'w', encoding='utf-8') as f:
            f.write(setting)

        return {"setting": setting}

    def stage2_generate_outline(
        self,
        setting: dict,
        num_chapters: int
    ) -> dict:
        """阶段2: 生成大纲"""
        prompt = f"""
        基于以下设定生成章节大纲：
        {setting['setting']}

        请生成{num_chapters}章的大纲，每章包含：
        1. 章节标题
        2. 章节目的
        3. 剧情要点
        4. 伏笔安排
        """
        outline = self.llm.generate(prompt)

        # 保存大纲
        outline_file = os.path.join(self.project_root, "outline.yaml")
        with open(outline_file, 'w', encoding='utf-8') as f:
            f.write(outline)

        return {"outline": outline}

    def stage3_generate_chapter(
        self,
        chapter_num: int,
        outline: dict,
        previous_chapters: list
    ) -> dict:
        """阶段3: 生成章节"""
        # 新增：使用向量检索获取相关前文
        chapter_id = f"chapter-{chapter_num:03d}"
        relevant_context = self.vector_store.get_relevant_context(
            chapter_id, n=3
        )

        prompt = f"""
        请生成第{chapter_num}章：

        大纲要求：
        {outline['chapters'][chapter_num-1]}

        前文参考（用于保持一致性）：
        {chr(10).join(relevant_context)}

        请生成2000-3000字的章节内容。
        """
        chapter = self.llm.generate(prompt)

        return {"chapter": chapter, "context_used": relevant_context}

    def stage4_finalize_chapter(
        self,
        chapter_num: int,
        chapter_text: str
    ) -> dict:
        """阶段4: 定稿章节"""
        # 索引到向量库
        chapter_id = f"chapter-{chapter_num:03d}"
        self.vector_store.add_chapter(chapter_id, chapter_text)

        # 生成摘要
        summary = self._generate_summary(chapter_text)

        # 更新状态
        state = load_state(self.project_root)
        state["project"]["activeChapterId"] = chapter_id
        save_state(self.project_root, state)

        return {"summary": summary, "chapter_id": chapter_id}
```

2. **后端：API接口**
```python
# src/story_harness_cli/api/endpoints.py
@router.post("/api/generate/stage")
async def generate_stage(
    stage: str,
    root: str,
    topic: str = None,
    genre: str = None,
    num_chapters: int = None,
    chapter_num: int = None
):
    """多阶段生成"""
    llm = create_llm_provider()
    generator = MultiStageGenerator(root, llm)

    if stage == "setting":
        result = generator.stage1_generate_setting(topic, genre, num_chapters)
    elif stage == "outline":
        setting = load_setting(root)
        result = generator.stage2_generate_outline(setting, num_chapters)
    elif stage == "chapter":
        outline = load_outline(root)
        previous = load_previous_chapters(root, chapter_num)
        result = generator.stage3_generate_chapter(chapter_num, outline, previous)
    elif stage == "finalize":
        chapter = load_chapter(root, chapter_num)
        result = generator.stage4_finalize_chapter(chapter_num, chapter)

    return result
```

3. **前端：生成工作流界面**
```vue
<!-- ui/src/views/WorkflowView.vue -->
<template>
  <div class="workflow-view">
    <t-card title="多阶段生成工作流">
      <!-- 阶段进度 -->
      <t-steps :current="currentStage" :items="stages" />

      <!-- 阶段1: 设定生成 -->
      <div v-if="currentStage === 0" class="stage-panel">
        <h3>阶段1: 生成设定</h3>
        <t-form>
          <t-form-item label="主题" name="topic">
            <t-input v-model="topic" placeholder="请输入主题" />
          </t-form-item>
          <t-form-item label="类型" name="genre">
            <t-select v-model="genre" :options="genreOptions" />
          </t-form-item>
          <t-form-item label="章节数" name="numChapters">
            <t-input-number v-model="numChapters" :min="10" :max="500" />
          </t-form-item>
          <t-form-item>
            <t-button
              theme="primary"
              @click="generateSetting"
              :loading="generating"
            >
              生成设定
            </t-button>
          </t-form-item>
        </t-form>

        <!-- 设定预览 -->
        <div v-if="generatedSetting" class="result-panel">
          <h4>生成的设定：</h4>
          <t-textarea
            :value="generatedSetting"
            readonly
            :autosize="{ minRows: 10 }"
          />
          <t-button @click="nextStage">下一步 →</t-button>
        </div>
      </div>

      <!-- 阶段2: 大纲生成 -->
      <div v-if="currentStage === 1" class="stage-panel">
        <h3>阶段2: 生成大纲</h3>
        <t-button
          theme="primary"
          @click="generateOutline"
          :loading="generating"
        >
          生成大纲
        </t-button>

        <!-- 大纲预览 -->
        <div v-if="generatedOutline" class="result-panel">
          <h4>生成的大纲：</h4>
          <t-textarea
            :value="generatedOutline"
            readonly
            :autosize="{ minRows: 10 }"
          />
          <t-button @click="nextStage">下一步 →</t-button>
        </div>
      </div>

      <!-- 阶段3: 章节生成 -->
      <div v-if="currentStage === 2" class="stage-panel">
        <h3>阶段3: 生成章节</h3>
        <t-form-item label="章节号">
          <t-input-number
            v-model="targetChapter"
            :min="1"
            :max="numChapters"
          />
        </t-form-item>
        <t-button
          theme="primary"
          @click="generateChapter"
          :loading="generating"
        >
          生成章节
        </t-button>

        <!-- 章节预览 -->
        <div v-if="generatedChapter" class="result-panel">
          <h4>生成的章节：</h4>
          <div class="chapter-content">{{ generatedChapter }}</div>
          <t-button @click="nextStage">下一步 →</t-button>
        </div>
      </div>

      <!-- 阶段4: 定稿 -->
      <div v-if="currentStage === 3" class="stage-panel">
        <h3>阶段4: 定稿章节</h3>
        <p>定稿将索引到向量库，用于后续章节的上下文检索。</p>
        <t-button
          theme="primary"
          @click="finalizeChapter"
          :loading="generating"
        >
          定稿
        </t-button>

        <div v-if="finalized" class="result-panel">
          <t-result status="success" title="定稿成功！">
            <template #extra>
              <p>章节已索引到向量库，可以继续生成下一章。</p>
              <t-button @click="resetForNext">生成下一章</t-button>
            </template>
          </t-result>
        </div>
      </div>
    </t-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { storyCanvasAPI } from "@/api/storyCanvas";

const currentStage = ref(0);
const generating = ref(false);

// 阶段1
const topic = ref("");
const genre = ref("xuanhuan");
const numChapters = ref(50);
const generatedSetting = ref("");

// 阶段2
const generatedOutline = ref("");

// 阶段3
const targetChapter = ref(1);
const generatedChapter = ref("");

// 阶段4
const finalized = ref(false);

const stages = [
  { title: "生成设定", description: "创建PROJECT.md" },
  { title: "生成大纲", description: "创建outline.yaml" },
  { title: "生成章节", description: "写作章节内容" },
  { title: "定稿", description: "索引到向量库" }
];

const genreOptions = [
  { label: "玄幻", value: "xuanhuan" },
  { label: "都市", value: "urban" },
  { label: "科幻", value: "scifi" }
];

async function generateSetting() {
  generating.value = true;
  try {
    const result = await storyCanvasAPI.generateStage(
      workspace.activeRoot.value,
      "setting",
      {
        topic: topic.value,
        genre: genre.value,
        numChapters: numChapters.value
      }
    );
    generatedSetting.value = result.setting;
  } finally {
    generating.value = false;
  }
}

async function generateOutline() {
  generating.value = true;
  try {
    const result = await storyCanvasAPI.generateStage(
      workspace.activeRoot.value,
      "outline"
    );
    generatedOutline.value = result.outline;
  } finally {
    generating.value = false;
  }
}

async function generateChapter() {
  generating.value = true;
  try {
    const result = await storyCanvasAPI.generateStage(
      workspace.activeRoot.value,
      "chapter",
      { chapterNum: targetChapter.value }
    );
    generatedChapter.value = result.chapter;
    // 显示使用的上下文
    console.log("使用的前文上下文：", result.context_used);
  } finally {
    generating.value = false;
  }
}

async function finalizeChapter() {
  generating.value = true;
  try {
    await storyCanvasAPI.generateStage(
      workspace.activeRoot.value,
      "finalize",
      { chapterNum: targetChapter.value }
    );
    finalized.value = true;
  } finally {
    generating.value = false;
  }
}

function nextStage() {
  currentStage.value++;
}

function resetForNext() {
  currentStage.value = 2;
  targetChapter.value++;
  generatedChapter.value = "";
  finalized.value = false;
}
</script>

<style scoped>
.workflow-view {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
}

.stage-panel {
  margin-top: 20px;
}

.result-panel {
  margin-top: 20px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: 4px;
}

.chapter-content {
  white-space: pre-wrap;
  line-height: 1.8;
  max-height: 400px;
  overflow-y: auto;
}
</style>
```

---

### 重点3: 智能上下文面板

**目标：** 在编辑器旁显示相关前文

**实现方式：**

1. **后端：上下文检索API**
```python
@router.get("/api/context/{chapter_id}")
async def get_chapter_context(chapter_id: str, root: str, n: int = 3):
    """获取章节相关上下文"""
    vector_store = VectorStore(root)
    contexts = vector_store.get_relevant_context(chapter_id, n=n)

    return {
        "chapterId": chapter_id,
        "contexts": [
            {
                "chapter": meta["chapter"],
                "chunk": meta["chunk"],
                "text": text,
                "relevance": 1 - distance  # 转换为相关性分数
            }
            for text, meta, distance in zip(
                contexts["documents"],
                contexts["metadatas"],
                contexts["distances"]
            )
        ]
    }
```

2. **前端：上下文面板组件**
```vue
<!-- ui/src/components/ContextPanel.vue -->
<template>
  <div class="context-panel">
    <div class="context-header">
      <h4>相关前文</h4>
      <t-button
        size="small"
        variant="text"
        @click="refresh"
      >
        <template #icon><refresh-icon /></template>
        刷新
      </t-button>
    </div>

    <div v-if="loading" class="context-loading">
      <t-loading />
    </div>

    <div v-else-if="contexts.length === 0" class="context-empty">
      <p>暂无相关前文</p>
    </div>

    <div v-else class="context-list">
      <div
        v-for="(context, index) in contexts"
        :key="index"
        class="context-item"
      >
        <div class="context-meta">
          <span class="context-chapter">{{ context.chapter }}</span>
          <span class="context-relevance">
            相关度: {{ (context.relevance * 100).toFixed(0) }}%
          </span>
        </div>
        <div class="context-text">{{ context.text }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { storyCanvasAPI } from "@/api/storyCanvas";

const props = defineProps<{
  projectRoot: string;
  chapterId: string;
}>();

const loading = ref(false);
const contexts = ref<any[]>([]);

const refresh = async () => {
  loading.value = true;
  try {
    const response = await storyCanvasAPI.getChapterContext(
      props.projectRoot,
      props.chapterId
    );
    contexts.value = response.contexts;
  } finally {
    loading.value = false;
  }
};

watch(() => props.chapterId, refresh, { immediate: true });
</script>

<style scoped>
.context-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  border-left: 1px solid var(--line);
}

.context-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
}

.context-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.context-item {
  padding: 12px;
  margin-bottom: 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
  font-size: 13px;
}

.context-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.context-text {
  white-space: pre-wrap;
  line-height: 1.6;
  color: var(--text);
}
</style>
```

3. **集成到现有编辑界面**
```vue
<!-- 修改 ui/src/views/workbench/review/ChapterEditorView.vue -->
<template>
  <div class="chapter-editor-view">
    <!-- 主编辑区 -->
    <div class="editor-main">
      <div class="editor-toolbar">
        <!-- 现有工具栏... -->
      </div>

      <div class="editor-content">
        <t-textarea
          v-model="chapterContent"
          :autosize="{ minRows: 20 }"
          placeholder="在这里输入章节内容..."
          @input="onContentChange"
        />
      </div>
    </div>

    <!-- 侧边栏：新增上下文面板 -->
    <div class="editor-sidebar">
      <ContextPanel
        :project-root="projectRoot"
        :chapter-id="chapterId"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import ContextPanel from "@/components/ContextPanel.vue";
// 现有代码...
</script>

<style scoped>
.chapter-editor-view {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 16px;
  height: 100%;
}

.editor-main {
  min-width: 0;
}

.editor-sidebar {
  border-left: 1px solid var(--line);
}
</style>
```

---

## 实施计划

### Phase 1: 向量检索集成（1周）

**后端任务：**
- [ ] 复制ChromaDB向量存储代码
- [ ] 创建vector_store服务
- [ ] 添加上下文检索API
- [ ] 集成到写作辅助接口

**前端任务：**
- [ ] 创建ContextPanel组件
- [ ] 修改章节编辑界面
- [ ] 添加上下文显示

### Phase 2: 多阶段生成工作流（1-2周）

**后端任务：**
- [ ] 创建MultiStageGenerator服务
- [ ] 添加生成阶段API
- [ ] 实现定稿时的向量索引

**前端任务：**
- [ ] 创建WorkflowView界面
- [ ] 集成到App.vue路由
- [ ] 添加工作流入口

### Phase 3: 优化完善（1周）

- [ ] 性能优化
- [ ] 错误处理
- [ ] 用户体验改进

---

## 文件清单

### 后端新增

```
src/story_harness_cli/
├── services/vector/          # [新增] 向量服务
│   ├── __init__.py
│   ├── vector_store.py       # 向量存储
│   └── embedding_adapter.py  # Embedding接口
├── services/
│   └── multi_stage_generator.py  # [新增] 多阶段生成
└── api/
    └── endpoints.py          # [修改] 添加新API
```

### 前端新增

```
ui/src/
├── components/
│   └── ContextPanel.vue       # [新增] 上下文面板
├── views/
│   └── WorkflowView.vue       # [新增] 工作流界面
├── composables/
│   └── useWritingAssist.ts    # [新增] 写作辅助
└── api/
    └── storyCanvas.ts         # [修改] 添加新API
```

---

## 依赖更新

### 后端

```txt
# future optional lane only；不得加入 base install

# 向量数据库
chromadb>=0.4.0

# Embedding
sentence-transformers>=2.2.0
```

### 前端

```json
// package.json 无需额外依赖
// 使用现有的TDesign组件即可
```

---

## 关键改进点

### 1. 写作体验增强

**之前：** 写作时需要手动翻看前文
**现在：** 自动显示最相关的前文片段

### 2. 多阶段生成

**之前：** 需要手动执行多个CLI命令
**现在：** 一站式工作流界面

### 3. 长程一致性

**之前：** 容易出现前后文矛盾
**现在：** 向量检索自动维护一致性

---

## 总结

本方案聚焦于**写作逻辑**的增强，而非UI重构：

1. **向量检索** - 自动获取相关前文
2. **多阶段生成** - 完整工作流
3. **智能上下文面板** - 写作时显示相关内容

**原则：**
- 最小改动现有WebUI
- 复用现有组件和样式
- 保持与CLI的兼容性

**预期效果：**
用户在WebUI中可以享受更智能的写作体验，同时保留CLI的所有功能。
