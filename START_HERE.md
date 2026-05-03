# 开始实施 - WebUI 集成向量检索和多阶段生成

> 快速开始指南

---

## ✅ 清理完成

已删除错误的文档，保留正确的：

**正确文档：**
- `docs/plans/2026-05-01-webui-integration-plan.md` - 完整规划
- `docs/guides/webui-integration-quickstart.md` - 快速开始

---

## 🎯 实施目标

**3个核心功能：**

1. **向量检索** - 写作时自动获取相关前文
2. **多阶段生成** - 设定→大纲→章节→定稿流程
3. **上下文面板** - 编辑器旁显示相关内容

**原则：**
- ✅ 保留现有WebUI（Vue3 + TDesign）
- ✅ 只增强写作逻辑
- ✅ 保持CLI完全兼容
- ❌ 不用PyQt
- ❌ 不重构UI框架

---

## 📝 实施步骤

### 步骤1: 后端 - 向量存储服务

```bash
# 1. 安装依赖
cd E:/Github/story-harness-cli
pip install chromadb>=0.4.0 sentence-transformers>=2.2.0

# 2. 创建服务文件
mkdir -p src/story_harness_cli/services/vector
```

创建 `src/story_harness_cli/services/vector_store.py`:

```python
import os
from typing import List
import chromadb
from chromadb.config import Settings

class VectorStore:
    def __init__(self, project_root: str):
        self.db_path = os.path.join(project_root, ".vectorstore")
        os.makedirs(self.db_path, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        self.collection = self.client.get_or_create_collection("chapters")

    def add_chapter(self, chapter_id: str, chapter_text: str):
        chunks = self._split_text(chapter_text)
        for i, chunk in enumerate(chunks):
            try:
                self.collection.add(
                    documents=[chunk],
                    ids=[f"{chapter_id}_chunk_{i}"],
                    metadatas=[{"chapter": chapter_id}]
                )
            except:
                pass

    def get_context(self, chapter_id: str, n: int = 3) -> List[str]:
        try:
            results = self.collection.query(
                query_texts=[f"chapter {chapter_id}"],
                n_results=n * 5,
                where={"chapter": {"$ne": chapter_id}}
            )

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
        return [text[i:i+size] for i in range(0, len(text), size)]
```

---

### 步骤2: 后端 - 多阶段生成器

创建 `src/story_harness_cli/services/multi_stage_generator.py`:

```python
from ..providers import create_llm_provider
from .vector_store import VectorStore

class MultiStageGenerator:
    def __init__(self, project_root: str, provider_config: dict):
        self.project_root = project_root
        self.llm = create_llm_provider(provider_config)
        self.vector_store = VectorStore(project_root)

    def generate_setting(self, topic: str, genre: str, num_chapters: int):
        prompt = f"生成{genre}小说设定：{topic}，{num_chapters}章"
        setting = self.llm.generate(prompt)

        import os
        with open(os.path.join(self.project_root, "PROJECT.md"), 'w') as f:
            f.write(setting)

        return {"setting": setting}

    def generate_chapter(self, chapter_num: int):
        # 获取相关前文（向量检索）
        chapter_id = f"chapter-{chapter_num:03d}"
        context = self.vector_store.get_context(chapter_id, n=3)

        prompt = f"生成第{chapter_num}章，参考前文：{''.join(context)}"
        chapter = self.llm.generate(prompt)

        return {"chapter": chapter, "contextUsed": context}

    def finalize_chapter(self, chapter_num: int, chapter_text: str):
        chapter_id = f"chapter-{chapter_num:03d}"
        self.vector_store.add_chapter(chapter_id, chapter_text)
        return {"chapterId": chapter_id}
```

---

### 步骤3: 后端 - API接口

修改 `src/story_harness_cli/api/endpoints.py`，添加：

```python
from fastapi import APIRouter
from ..services.multi_stage_generator import MultiStageGenerator

router = APIRouter()

@router.post("/api/generate/{stage}")
async def generate_stage(stage: str, root: str, params: dict):
    config = {"provider": "openai", "api_key": "xxx", "model": "gpt-4"}
    gen = MultiStageGenerator(root, config)

    if stage == "setting":
        return gen.generate_setting(params["topic"], params["genre"], params["numChapters"])
    elif stage == "chapter":
        return gen.generate_chapter(params["chapterNum"])
    elif stage == "finalize":
        return gen.finalize_chapter(params["chapterNum"], params["chapterText"])
```

---

### 步骤4: 前端 - API接口

修改 `ui/src/api/storyCanvas.ts`，添加：

```typescript
export async function generateStage(
  root: string,
  stage: string,
  params: any
): Promise<any> {
  return fetch(`/api/generate/${stage}?root=${root}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(params)
  }).then(r => r.json());
}
```

---

### 步骤5: 前端 - 工作流界面

创建 `ui/src/views/WorkflowView.vue`（简化版）：

```vue
<template>
  <div class="workflow">
    <t-card title="多阶段生成">
      <t-steps :current="step" :items="steps" />

      <!-- 设定 -->
      <div v-if="step===0" class="step">
        <t-input v-model="topic" placeholder="主题" />
        <t-button @click="genSetting">生成设定</t-button>
        <div v-if="result.setting">{{ result.setting }}</div>
        <t-button @click="step=1">下一步</t-button>
      </div>

      <!-- 章节 -->
      <div v-if="step===2" class="step">
        <t-input-number v-model="chapterNum" />
        <t-button @click="genChapter">生成章节</t-button>
        <div v-if="result.chapter">{{ result.chapter }}</div>
        <t-button @click="step=3">定稿</t-button>
      </div>

      <!-- 定稿 -->
      <div v-if="step===3" class="step">
        <t-button @click="finalize">定稿并索引</t-button>
        <div v-if="ok">完成！</div>
      </div>
    </t-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { generateStage } from "@/api/storyCanvas";
import { useWorkspace } from "@/composables/useWorkspace";

const workspace = useWorkspace();
const step = ref(0);
const topic = ref("");
const chapterNum = ref(1);
const result = ref<any>({});
const ok = ref(false);

const steps = [{title:"设定"}, {title:"大纲"}, {title:"章节"}, {title:"定稿"}];

async function genSetting() {
  result.value = await generateStage(workspace.activeRoot.value, "setting", {
    topic: topic.value, genre: "xuanhuan", numChapters: 50
  });
}

async function genChapter() {
  result.value = await generateStage(workspace.activeRoot.value, "chapter", {
    chapterNum: chapterNum.value
  });
}

async function finalize() {
  await generateStage(workspace.activeRoot.value, "finalize", {
    chapterNum: chapterNum.value,
    chapterText: result.value.chapter
  });
  ok.value = true;
}
</script>

<style scoped>
.workflow { padding: 20px; max-width: 800px; margin: 0 auto; }
.step { margin-top: 20px; }
</style>
```

---

### 步骤6: 添加路由

修改 `ui/src/App.vue`，在activitybar添加：

```vue
<button
  class="activitybar-button"
  :class="{ 'is-active': activePage === 'workflow' }"
  @click="setActivePage('workflow')"
>
  <svg viewBox="0 0 24 24">
    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm0-4h-2V7h2v8z"/>
  </svg>
</button>
```

在imports添加：

```typescript
const WorkflowView = defineAsyncComponent(() => import("@/views/WorkflowView.vue"));
```

在template添加：

```vue
<WorkflowView v-if="activePage === 'workflow'" />
```

---

## 🚀 开始实施

### 方式1: 从向量检索开始

```bash
# 1. 创建向量存储服务
# 复制上面的代码到 src/story_harness_cli/services/vector_store.py

# 2. 测试向量存储
python -c "
from services.vector_store import VectorStore
vs = VectorStore('.')
vs.add_chapter('test', '这是测试内容')
print(vs.get_context('test'))
"

# 3. 集成到写作辅助API
# 修改 services/comprehensive_review.py，添加向量检索

# 4. 测试前端
cd ui && npm run dev
# 打开WebUI，测试写作辅助功能
```

### 方式2: 从多阶段生成开始

```bash
# 1. 创建多阶段生成器
# 复制上面的代码

# 2. 创建WorkflowView
# 复制上面的代码

# 3. 测试工作流
cd ui && npm run dev
# 打开WebUI，进入工作流页面
```

---

## 📚 参考文档

详细代码和说明请查看：

- **完整规划:** `docs/plans/2026-05-01-webui-integration-plan.md`
- **快速指南:** `docs/guides/webui-integration-quickstart.md`

---

## ✅ 验收标准

完成后应该能够：

1. [ ] 在WebUI中完成"设定→章节→定稿"流程
2. [ ] 写作时自动获取相关前文
3. [ ] 章节自动索引到向量库
4. [ ] CLI命令仍然可用

---

## 🎯 建议

**先做向量检索**（1-2天）
- 这是核心功能
- 相对独立
- 立即见效

**再做工作流界面**（2-3天）
- 依赖向量检索
- 完整体验
- 用户友好

开始吧！
