# WebUI 快速集成指南

> 简化版 - 集成NovelGenerator核心写作逻辑
> 聚焦：向量检索 + 多阶段生成
> 状态：探索性草案，不是当前执行入口；不得按本文直接向 base install 添加第三方依赖

---

> 2026-05-03 口径更新：当前仓库仍以 stdlib-only base 为边界。本文中的 ChromaDB / FastAPI / sentence-transformers 示例只能作为 future optional lane 参考；真实实施必须先回到 `docs/roadmap.md` 与 `docs/adr/ADR-002-optional-dependencies-and-providers.md`，并提供 builtin fallback。

## 核心理念

**不重构UI，只增强写作逻辑**

- 保留现有WebUI框架
- 添加向量检索能力
- 添加多阶段生成工作流
- 保持CLI完全兼容

---

## 步骤1: 向量检索后端

### 1.1 安装依赖

```bash
# future optional lane only
# 不得加入 base install；需要先设计 extras、fallback 与离线 smoke。
pip install "chromadb>=0.4.0" "sentence-transformers>=2.2.0"
```

### 1.2 创建向量存储服务

```python
# src/story_harness_cli/services/vector_store.py
"""
向量存储服务 - 用于语义检索
"""
import os
from typing import List
import chromadb
from chromadb.config import Settings

class VectorStore:
    """向量存储"""

    def __init__(self, project_root: str):
        self.db_path = os.path.join(project_root, ".vectorstore")
        os.makedirs(self.db_path, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        self.collection = self.client.get_or_create_collection("chapters")

    def add_chapter(self, chapter_id: str, chapter_text: str):
        """添加章节到向量库"""
        chunks = self._split_text(chapter_text)

        for i, chunk in enumerate(chunks):
            try:
                self.collection.add(
                    documents=[chunk],
                    ids=[f"{chapter_id}_chunk_{i}"],
                    metadatas=[{"chapter": chapter_id}]
                )
            except Exception:
                # 已存在，跳过
                pass

    def get_context(self, chapter_id: str, n: int = 3) -> List[str]:
        """获取相关上下文"""
        try:
            results = self.collection.query(
                query_texts=[f"chapter {chapter_id}"],
                n_results=n * 5,
                where={"chapter": {"$ne": chapter_id}}
            )

            # 去重
            seen = set()
            contexts = []
            for doc, meta in zip(results["documents"], results["metadatas"]):
                ch = meta["chapter"]
                if ch not in seen:
                    contexts.append(doc)
                    seen.add(ch)
                    if len(contexts) >= n:
                        break

            return contexts
        except:
            return []

    def _split_text(self, text: str, size: int = 500) -> List[str]:
        """分割文本"""
        chunks = []
        for i in range(0, len(text), size):
            chunks.append(text[i:i+size])
        return chunks
```

### 1.3 集成到现有服务

```python
# 修改: src/story_harness_cli/services/comprehensive_review.py

# 在现有函数中添加向量检索支持
def comprehensive_review(state, chapter_id, chapter_text, focus_areas, strictness):
    """综合审查 - 增强版"""
    # 现有代码...

    # 新增：使用向量检索获取相关前文
    from .vector_store import VectorStore
    vector_store = VectorStore(state["project"]["root"])
    context = vector_store.get_context(chapter_id, n=3)

    # 将上下文传递给各审查模块
    result = {
        # 现有字段...
        "contextUsed": context,
        "contextAwareReview": True
    }

    return result
```

---

## 步骤2: 多阶段生成后端

### 2.1 创建多阶段生成器

```python
# src/story_harness_cli/services/multi_stage_generator.py
"""
多阶段生成服务
"""
import os
from ..providers import create_llm_provider
from .vector_store import VectorStore
from ..protocol.io import load_state, save_state

class MultiStageGenerator:
    """多阶段生成器"""

    def __init__(self, project_root: str, provider_config: dict):
        self.project_root = project_root
        self.llm = create_llm_provider(provider_config)
        self.vector_store = VectorStore(project_root)

    def generate_setting(self, topic: str, genre: str, num_chapters: int) -> dict:
        """生成设定"""
        prompt = f"""生成小说设定：
主题：{topic}
类型：{genre}
章节数：{num_chapters}

请生成包含以下内容的完整设定：
1. 核心承诺（装逼打脸、倒贴流等）
2. 情绪契约
3. 商业定位
4. 故事简介
5. 第一卷规划
"""

        setting = self.llm.generate(prompt)

        # 保存
        setting_path = os.path.join(self.project_root, "PROJECT.md")
        with open(setting_path, 'w', encoding='utf-8') as f:
            f.write(setting)

        return {"setting": setting}

    def generate_outline(self, num_chapters: int) -> dict:
        """生成大纲"""
        # 读取设定
        setting_path = os.path.join(self.project_root, "PROJECT.md")
        with open(setting_path, 'r', encoding='utf-8') as f:
            setting = f.read()

        prompt = f"""基于以下设定生成章节大纲：
{setting}

请生成{num_chapters}章的大纲，每章包含：
- 章节标题
- 章节日标
- 剧情要点
- 伏笔安排（如适用）
"""

        outline = self.llm.generate(prompt)

        # 保存
        outline_path = os.path.join(self.project_root, "outline.yaml")
        with open(outline_path, 'w', encoding='utf-8') as f:
            f.write(outline)

        return {"outline": outline}

    def generate_chapter(self, chapter_num: int) -> dict:
        """生成章节"""
        # 读取大纲
        outline_path = os.path.join(self.project_root, "outline.yaml")
        with open(outline_path, 'r', encoding='utf-8') as f:
            outline = f.read()

        # 获取相关前文（向量检索）
        chapter_id = f"chapter-{chapter_num:03d}"
        context = self.vector_store.get_context(chapter_id, n=3)
        context_text = "\n".join(context) if context else "（这是第一章）"

        prompt = f"""生成第{chapter_num}章：

大纲要求：
{outline}

前文参考（保持一致性）：
{context_text}

请生成2000-3000字的章节内容。
要求：
1. 遵循玄幻网文风格（压制→反压→爽点）
2. 每章至少一个爽点
3. 结尾留下追读钩子
"""

        chapter = self.llm.generate(prompt)

        return {
            "chapter": chapter,
            "contextUsed": context_text
        }

    def finalize_chapter(self, chapter_num: int, chapter_text: str) -> dict:
        """定稿章节"""
        chapter_id = f"chapter-{chapter_num:03d}"

        # 保存章节
        chapter_path = os.path.join(
            self.project_root,
            "chapters",
            f"{chapter_id}.md"
        )
        os.makedirs(os.path.dirname(chapter_path), exist_ok=True)
        with open(chapter_path, 'w', encoding='utf-8') as f:
            f.write(chapter_text)

        # 索引到向量库
        self.vector_store.add_chapter(chapter_id, chapter_text)

        # 更新状态
        state = load_state(self.project_root)
        state["project"]["activeChapterId"] = chapter_id
        save_state(self.project_root, state)

        return {"chapterId": chapter_id, "indexed": True}
```

### 2.2 添加API接口

```python
# 修改: src/story_harness_cli/api/endpoints.py

from fastapi import APIRouter, HTTPException
from ..services.multi_stage_generator import MultiStageGenerator

router = APIRouter()

@router.post("/generate/{stage}")
async def generate_stage(
    stage: str,
    root: str,
    topic: str = None,
    genre: str = "xuanhuan",
    num_chapters: int = 50,
    chapter_num: int = 1,
    chapter_text: str = None
):
    """多阶段生成API"""

    provider_config = {
        "provider": "openai",
        "api_key": "your-api-key",
        "model": "gpt-4"
    }

    generator = MultiStageGenerator(root, provider_config)

    try:
        if stage == "setting":
            return generator.generate_setting(topic, genre, num_chapters)

        elif stage == "outline":
            return generator.generate_outline(num_chapters)

        elif stage == "chapter":
            return generator.generate_chapter(chapter_num)

        elif stage == "finalize":
            if not chapter_text:
                raise HTTPException(400, "需要提供chapter_text")
            return generator.finalize_chapter(chapter_num, chapter_text)

        else:
            raise HTTPException(400, "未知阶段")

    except Exception as e:
        raise HTTPException(500, f"生成失败: {str(e)}")
```

---

## 步骤3: 前端集成

### 3.1 添加API接口定义

```typescript
// ui/src/api/storyCanvas.ts - 添加

export async function generateStage(
  root: string,
  stage: string,
  params: {
    topic?: string;
    genre?: string;
    numChapters?: number;
    chapterNum?: number;
    chapterText?: string;
  }
): Promise<any> {
  return fetch(`/api/generate/${stage}?root=${root}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  }).then(r => r.json());
}
```

### 3.2 创建上下文面板组件

```vue
<!-- ui/src/components/ContextPanel.vue -->
<template>
  <div class="context-panel">
    <div class="context-header">
      <span>相关前文</span>
      <t-button
        size="small"
        variant="text"
        @click="refresh"
      >
        刷新
      </t-button>
    </div>

    <div v-if="contexts.length === 0" class="context-empty">
      <p>暂无相关前文</p>
    </div>

    <div v-else class="context-list">
      <div
        v-for="(ctx, i) in contexts"
        :key="i"
        class="context-item"
      >
        <div class="context-meta">
          <span>{{ ctx.chapter }}</span>
          <span>{{ (ctx.relevance * 100).toFixed(0) }}%</span>
        </div>
        <p>{{ ctx.text }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";

const props = defineProps<{
  root: string;
  chapterId: string;
}>();

const contexts = ref<any[]>([]);

const refresh = async () => {
  const res = await fetch(`/api/context/${props.chapterId}?root=${props.root}`);
  const data = await res.json();
  contexts.value = data.contexts;
};

watch(() => props.chapterId, refresh);
</script>

<style scoped>
.context-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.context-header {
  padding: 12px;
  border-bottom: 1px solid var(--line);
  display: flex;
  justify-content: space-between;
}

.context-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.context-item {
  padding: 10px;
  margin-bottom: 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
}

.context-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 6px;
}
</style>
```

### 3.3 创建工作流界面

```vue
<!-- ui/src/views/WorkflowView.vue -->
<template>
  <div class="workflow-view">
    <t-card title="多阶段生成">
      <t-steps :current="step" :items="steps" />

      <!-- 步骤1 -->
      <div v-if="step === 0" class="step-content">
        <h3>生成设定</h3>
        <t-form>
          <t-form-item label="主题">
            <t-input v-model="topic" />
          </t-form-item>
          <t-form-item label="类型">
            <t-select v-model="genre" :options="genres" />
          </t-form-item>
          <t-form-item label="章节数">
            <t-input-number v-model="numChapters" />
          </t-form-item>
          <t-button @click="genSetting" :loading="loading">
            生成
          </t-button>
        </t-form>

        <div v-if="result.setting" class="result">
          <pre>{{ result.setting }}</pre>
          <t-button @click="next">下一步</t-button>
        </div>
      </div>

      <!-- 步骤2 -->
      <div v-if="step === 1" class="step-content">
        <h3>生成大纲</h3>
        <t-button @click="genOutline" :loading="loading">
          生成
        </t-button>

        <div v-if="result.outline" class="result">
          <pre>{{ result.outline }}</pre>
          <t-button @click="next">下一步</t-button>
        </div>
      </div>

      <!-- 步骤3 -->
      <div v-if="step === 2" class="step-content">
        <h3>生成章节</h3>
        <t-form-item label="章节号">
          <t-input-number v-model="chapterNum" />
        </t-form-item>
        <t-button @click="genChapter" :loading="loading">
          生成
        </t-button>

        <div v-if="result.chapter" class="result">
          <div class="chapter-text">{{ result.chapter }}</div>
          <t-button @click="next">下一步</t-button>
        </div>
      </div>

      <!-- 步骤4 -->
      <div v-if="step === 3" class="step-content">
        <h3>定稿</h3>
        <p>定稿将索引到向量库</p>
        <t-button @click="finalize" :loading="loading">
          定稿
        </t-button>

        <div v-if="result.finalized" class="result">
          <t-result status="success" title="完成">
            <t-button @click="reset">继续生成下一章</t-button>
          </t-result>
        </div>
      </div>
    </t-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useWorkspace } from "@/composables/useWorkspace";
import { generateStage } from "@/api/storyCanvas";

const workspace = useWorkspace();
const step = ref(0);
const loading = ref(false);
const result = ref<any>({});

const topic = ref("");
const genre = ref("xuanhuan");
const numChapters = ref(50);
const chapterNum = ref(1);

const steps = [
  { title: "设定" },
  { title: "大纲" },
  { title: "章节" },
  { title: "定稿" }
];

const genres = [
  { label: "玄幻", value: "xuanhuan" },
  { label: "都市", value: "urban" }
];

async function genSetting() {
  loading.value = true;
  result.value = await generateStage(workspace.activeRoot.value, "setting", {
    topic: topic.value,
    genre: genre.value,
    numChapters: numChapters.value
  });
  loading.value = false;
}

async function genOutline() {
  loading.value = true;
  result.value = await generateStage(workspace.activeRoot.value, "outline", {
    numChapters: numChapters.value
  });
  loading.value = false;
}

async function genChapter() {
  loading.value = true;
  result.value = await generateStage(workspace.activeRoot.value, "chapter", {
    chapterNum: chapterNum.value
  });
  loading.value = false;
}

async function finalize() {
  loading.value = true;
  result.value = await generateStage(workspace.activeRoot.value, "finalize", {
    chapterNum: chapterNum.value,
    chapterText: result.value.chapter
  });
  loading.value = false;
}

function next() {
  step.value++;
}

function reset() {
  step.value = 2;
  chapterNum.value++;
  result.value = {};
}
</script>

<style scoped>
.workflow-view {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.step-content {
  margin-top: 24px;
}

.result {
  margin-top: 16px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: 4px;
}

.chapter-text {
  white-space: pre-wrap;
  line-height: 1.8;
  max-height: 400px;
  overflow-y: auto;
}
</style>
```

### 3.4 添加路由

```typescript
// 修改: ui/src/App.vue

// 在activitybar中添加工作流按钮
<button
  class="activitybar-button"
  :class="{ 'is-active': activePage === 'workflow' }"
  @click="setActivePage('workflow')"
>
  <svg>...</svg> <!-- 工作流图标 -->
</button>

// 在imports中添加
const WorkflowView = defineAsyncComponent(() => import("@/views/WorkflowView.vue"));

// 在template中添加
<WorkflowView v-if="activePage === 'workflow'" />
```

---

## 步骤4: 测试

### 4.1 启动后端

```bash
cd E:/Github/story-harness-cli
python -m story_harness_cli.api.server
```

### 4.2 启动前端

```bash
cd E:/Github/story-harness-cli/ui
npm run dev
```

### 4.3 测试工作流

1. 打开WebUI
2. 进入"工作流"页面
3. 按步骤生成：
   - 输入主题、类型、章节数
   - 生成设定
   - 生成大纲
   - 生成章节
   - 定稿

### 4.4 测试上下文面板

1. 打开"审查工作区"
2. 选择一个章节
3. 查看"相关前文"面板
4. 验证是否显示相关的前文片段

---

## 验收标准

- [ ] 可以通过WebUI完成多阶段生成
- [ ] 向量检索正常工作
- [ ] 上下文面板显示相关前文
- [ ] CLI命令仍然可用
- [ ] 现有功能不受影响

---

## 总结

本快速指南聚焦于核心功能：

**后端：**
1. 向量存储服务（VectorStore）
2. 多阶段生成器（MultiStageGenerator）
3. API接口

**前端：**
1. 上下文面板组件（ContextPanel）
2. 工作流界面（WorkflowView）
3. API集成

**预期效果：**
用户可以在WebUI中享受智能的写作体验，同时保留CLI的完整功能。
