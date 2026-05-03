<template>
  <div class="workflow-view">
    <header class="workflow-head">
      <div>
        <strong>工作流</strong>
        <p>{{ projectTitle }}</p>
      </div>
      <div class="workflow-head-meta">
        <span>项目根目录</span>
        <strong>{{ projectRoot || "未选择" }}</strong>
      </div>
    </header>

    <div class="workflow-body">
      <section class="workflow-main">
        <div class="stage-nav" role="tablist" aria-label="工作流阶段">
          <button
            v-for="(item, index) in stageItems"
            :key="item.key"
            class="stage-nav-item"
            :class="{ 'is-active': currentStage === index, 'is-complete': currentStage > index }"
            type="button"
            @click="currentStage = index"
          >
            <strong>{{ item.label }}</strong>
            <span>{{ item.hint }}</span>
          </button>
        </div>

        <t-card class="surface-card workflow-card" title="">
          <template v-if="currentStage === 0">
            <div class="workflow-stage">
              <div class="workflow-form">
                <t-form label-width="84px">
                  <t-form-item label="主题">
                    <t-input v-model="topic" placeholder="输入故事主题" />
                  </t-form-item>
                  <t-form-item label="题材">
                    <t-input v-model="genre" placeholder="例如 玄幻 / 都市 / 科幻" />
                  </t-form-item>
                  <t-form-item label="章节数">
                    <t-input-number v-model="numChapters" :min="1" :max="500" />
                  </t-form-item>
                  <t-form-item>
                    <button class="stage-action is-primary" type="button" :disabled="loading || !projectRoot" @click="handleGenerateSetting">
                      {{ loading ? "生成中..." : "生成设定" }}
                    </button>
                  </t-form-item>
                </t-form>
              </div>

              <div class="workflow-output">
                <strong class="output-title">设定结果</strong>
                <pre class="output-block">{{ generatedSetting || "尚未生成。" }}</pre>
              </div>
            </div>
          </template>

          <template v-else-if="currentStage === 1">
            <div class="workflow-stage">
              <div class="workflow-form">
                <t-form label-width="84px">
                  <t-form-item label="设定">
                    <t-textarea v-model="generatedSetting" :autosize="{ minRows: 7 }" placeholder="生成的设定会显示在这里" />
                  </t-form-item>
                  <t-form-item label="章节数">
                    <t-input-number v-model="numChapters" :min="1" :max="500" />
                  </t-form-item>
                  <t-form-item>
                    <button class="stage-action is-primary" type="button" :disabled="loading || !generatedSetting" @click="handleGenerateOutline">
                      {{ loading ? "生成中..." : "生成大纲" }}
                    </button>
                  </t-form-item>
                </t-form>
              </div>

              <div class="workflow-output">
                <strong class="output-title">大纲结果</strong>
                <pre class="output-block">{{ generatedOutline || "尚未生成。" }}</pre>
              </div>
            </div>
          </template>

          <template v-else-if="currentStage === 2">
            <div class="workflow-stage">
              <div class="workflow-form">
                <t-form label-width="84px">
                  <t-form-item label="章号">
                    <t-input-number v-model="chapterNum" :min="1" :max="500" />
                  </t-form-item>
                  <t-form-item label="大纲">
                    <t-textarea v-model="generatedOutline" :autosize="{ minRows: 7 }" placeholder="生成的大纲会显示在这里" />
                  </t-form-item>
                  <t-form-item>
                    <button class="stage-action is-primary" type="button" :disabled="loading || !generatedOutline" @click="handleGenerateChapter">
                      {{ loading ? "生成中..." : "生成章节" }}
                    </button>
                  </t-form-item>
                </t-form>
              </div>

              <div class="workflow-output">
                <strong class="output-title">章节结果</strong>
                <pre class="output-block">{{ generatedChapter || "尚未生成。" }}</pre>
                <div class="context-preview" v-if="contextUsed.length">
                  <strong class="output-title">相关前文</strong>
                  <article v-for="item in contextUsed" :key="`${item.chapterId}:${item.chunkIndex}`" class="context-preview-item">
                    <div class="context-preview-head">
                      <strong>{{ item.chapterTitle }}</strong>
                      <span>{{ item.chapterId }}</span>
                    </div>
                    <p>{{ item.text }}</p>
                  </article>
                </div>
              </div>
            </div>
          </template>

          <template v-else>
            <div class="workflow-stage workflow-finalize">
              <div class="workflow-output">
                <strong class="output-title">定稿预览</strong>
                <pre class="output-block">{{ generatedChapter || "先生成章节，再定稿。" }}</pre>
              </div>
              <div class="workflow-finalize-actions">
                <button class="stage-action is-primary" type="button" :disabled="loading || !generatedChapter" @click="handleFinalizeChapter">
                  {{ loading ? "定稿中..." : "定稿并索引" }}
                </button>
                <button class="stage-action" type="button" :disabled="loading" @click="nextChapter">
                  下一章
                </button>
              </div>
              <div v-if="finalizeMessage" class="finalize-message">
                {{ finalizeMessage }}
              </div>
            </div>
          </template>
        </t-card>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { finalizeStage, generateStage } from "@/api/storyCanvas";
import { useWorkspace } from "@/composables/useWorkspace";

const workspace = useWorkspace();
const projectRoot = computed(() => workspace.selectedRoot.value);
const projectTitle = computed(() => workspace.summary.value?.project.title || "工作流");

const currentStage = ref(0);
const loading = ref(false);
const finalizeMessage = ref("");

const topic = ref("");
const genre = ref("");
const numChapters = ref(12);
const chapterNum = ref(1);

const generatedSetting = ref("");
const generatedOutline = ref("");
const generatedChapter = ref("");
const contextUsed = ref<Array<{ chapterId: string; chapterTitle: string; chapterOrder: number; chunkIndex: number; score: number; text: string }>>([]);

const stageItems = [
  { key: "setting", label: "设定", hint: "生成故事底盘" },
  { key: "outline", label: "大纲", hint: "拆分章节结构" },
  { key: "chapter", label: "章节", hint: "生成正文" },
  { key: "finalize", label: "定稿", hint: "索引与保存" },
];

watch(
  projectRoot,
  () => {
    currentStage.value = 0;
    generatedSetting.value = "";
    generatedOutline.value = "";
    generatedChapter.value = "";
    contextUsed.value = [];
    finalizeMessage.value = "";
    chapterNum.value = 1;
  },
  { immediate: true }
);

async function handleGenerateSetting() {
  if (!projectRoot.value) {
    return;
  }
  loading.value = true;
  finalizeMessage.value = "";
  try {
    const payload = await generateStage({
      root: projectRoot.value,
      stage: "setting",
      topic: topic.value.trim(),
      genre: genre.value.trim(),
      numChapters: numChapters.value,
      projectTitle: projectTitle.value,
      model: "gpt-5.4-mini",
    });
    generatedSetting.value = payload.setting || "";
    currentStage.value = 1;
  } finally {
    loading.value = false;
  }
}

async function handleGenerateOutline() {
  if (!projectRoot.value) {
    return;
  }
  loading.value = true;
  finalizeMessage.value = "";
  try {
    const payload = await generateStage({
      root: projectRoot.value,
      stage: "outline",
      settingText: generatedSetting.value,
      numChapters: numChapters.value,
      model: "gpt-5.4-mini",
    });
    generatedOutline.value = payload.outline || "";
    currentStage.value = 2;
  } finally {
    loading.value = false;
  }
}

async function handleGenerateChapter() {
  if (!projectRoot.value) {
    return;
  }
  loading.value = true;
  finalizeMessage.value = "";
  try {
    const payload = await generateStage({
      root: projectRoot.value,
      stage: "chapter",
      outlineText: generatedOutline.value,
      chapterId: `chapter-${String(chapterNum.value).padStart(3, "0")}`,
      chapterNum: chapterNum.value,
      chapterTitle: `第${chapterNum.value}章`,
      contextCount: 3,
      model: "gpt-5.4-mini",
    });
    generatedChapter.value = payload.chapter || "";
    contextUsed.value = payload.contextUsed || [];
    currentStage.value = 3;
  } finally {
    loading.value = false;
  }
}

async function handleFinalizeChapter() {
  if (!projectRoot.value || !generatedChapter.value) {
    return;
  }
  loading.value = true;
  finalizeMessage.value = "";
  try {
    const payload = await finalizeStage({
      root: projectRoot.value,
      chapterNum: chapterNum.value,
      chapterText: generatedChapter.value,
    });
    finalizeMessage.value = `已保存到 ${payload.chapterFile}`;
  } finally {
    loading.value = false;
  }
}

function nextChapter() {
  chapterNum.value += 1;
  currentStage.value = 2;
  generatedChapter.value = "";
  contextUsed.value = [];
  finalizeMessage.value = "";
}
</script>

<style scoped>
.workflow-view {
  display: grid;
  gap: 16px;
  padding: 20px;
  min-height: 0;
}

.workflow-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.workflow-head strong {
  font-size: 18px;
  font-weight: 700;
}

.workflow-head p {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 12px;
}

.workflow-head-meta {
  display: grid;
  gap: 2px;
  justify-items: end;
  color: var(--muted);
  font-size: 11px;
}

.workflow-head-meta strong {
  color: var(--text);
  font-size: 12px;
  font-weight: 600;
}

.workflow-body {
  display: grid;
  min-height: 0;
}

.workflow-main {
  display: grid;
  gap: 12px;
  min-width: 0;
}

.stage-nav {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.stage-nav-item {
  display: grid;
  gap: 2px;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: var(--surface);
  color: var(--text);
  text-align: left;
  cursor: pointer;
}

.stage-nav-item strong {
  font-size: 13px;
}

.stage-nav-item span {
  color: var(--muted);
  font-size: 11px;
}

.stage-nav-item.is-active {
  border-color: var(--primary, #0052d9);
}

.stage-nav-item.is-complete {
  background: rgba(0, 82, 217, 0.06);
}

.workflow-card {
  min-height: 0;
}

.workflow-stage {
  display: grid;
  grid-template-columns: minmax(0, 360px) minmax(0, 1fr);
  gap: 16px;
  min-height: 0;
}

.workflow-form,
.workflow-output {
  min-width: 0;
}

.output-title {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 600;
}

.output-block {
  margin: 0;
  min-height: 320px;
  max-height: 520px;
  overflow: auto;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: var(--surface);
  white-space: pre-wrap;
  line-height: 1.7;
  font-size: 12px;
}

.context-preview {
  display: grid;
  gap: 8px;
  margin-top: 16px;
}

.context-preview-item {
  display: grid;
  gap: 4px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: var(--surface);
}

.context-preview-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.context-preview-head strong,
.context-preview-head span {
  font-size: 11px;
  color: var(--muted);
}

.context-preview-item p {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 12px;
}

.workflow-finalize {
  grid-template-columns: minmax(0, 1fr);
}

.workflow-finalize-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.stage-action {
  padding: 8px 12px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
}

.stage-action:disabled {
  cursor: wait;
  opacity: 0.7;
}

.stage-action.is-primary {
  border-color: var(--primary, #0052d9);
  background: var(--primary, #0052d9);
  color: #fff;
}

.finalize-message {
  margin-top: 12px;
  color: var(--success, #0a7a3f);
  font-size: 12px;
}

@media (max-width: 1100px) {
  .workflow-stage {
    grid-template-columns: minmax(0, 1fr);
  }

  .stage-nav {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
