<template>
  <section class="context-panel">
    <header class="context-panel-head">
      <div>
        <strong>相关前文</strong>
        <p>基于当前章节内容检索相近片段</p>
      </div>
      <button class="context-refresh" type="button" :disabled="loading" @click="refresh">
        {{ loading ? "刷新中..." : "刷新" }}
      </button>
    </header>

    <div v-if="errorMessage" class="context-empty context-error">
      {{ errorMessage }}
    </div>
    <div v-else-if="loading" class="context-empty">正在检索...</div>
    <div v-else-if="contexts.length === 0" class="context-empty">暂无相关前文。</div>
    <div v-else class="context-list">
      <article v-for="item in contexts" :key="`${item.chapterId}:${item.chunkIndex}`" class="context-item">
        <div class="context-item-head">
          <strong>{{ item.chapterTitle }}</strong>
          <span>{{ (item.score * 100).toFixed(0) }}%</span>
        </div>
        <div class="context-item-meta">
          <span>{{ item.chapterId }}</span>
          <span>块 {{ item.chunkIndex }}</span>
        </div>
        <p class="context-item-text">{{ item.text }}</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";

import { fetchChapterContext, type ChapterContextItem } from "@/api/storyCanvas";

const props = defineProps<{
  root: string;
  chapterId: string;
}>();

const loading = ref(false);
const contexts = ref<ChapterContextItem[]>([]);
const errorMessage = ref("");

async function refresh() {
  const root = props.root.trim();
  const chapterId = props.chapterId.trim();
  if (!root || !chapterId) {
    contexts.value = [];
    errorMessage.value = "";
    return;
  }
  loading.value = true;
  errorMessage.value = "";
  try {
    const payload = await fetchChapterContext(root, chapterId, 3);
    contexts.value = payload.contexts;
  } catch (error) {
    contexts.value = [];
    errorMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    loading.value = false;
  }
}

watch(
  () => [props.root, props.chapterId],
  () => {
    void refresh();
  },
  { immediate: true }
);
</script>

<style scoped>
.context-panel {
  display: grid;
  gap: 8px;
  min-height: 0;
}

.context-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.context-panel-head strong {
  display: block;
  font-size: 13px;
  font-weight: 600;
}

.context-panel-head p {
  margin: 2px 0 0;
  color: var(--muted);
  font-size: 11px;
}

.context-refresh {
  flex: 0 0 auto;
  padding: 4px 8px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: var(--surface);
  color: var(--text);
  font-size: 12px;
  cursor: pointer;
}

.context-refresh:disabled {
  opacity: 0.7;
  cursor: wait;
}

.context-list {
  display: grid;
  gap: 8px;
  min-height: 0;
  max-height: 320px;
  overflow: auto;
  padding-right: 4px;
}

.context-item {
  display: grid;
  gap: 6px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: var(--surface);
}

.context-item-head,
.context-item-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.context-item-head strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}

.context-item-head span,
.context-item-meta {
  color: var(--muted);
  font-size: 11px;
}

.context-item-text {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 12px;
}

.context-empty {
  padding: 10px;
  border: 1px dashed var(--line);
  border-radius: 4px;
  color: var(--muted);
  font-size: 12px;
}

.context-error {
  color: var(--danger, #b00020);
}
</style>
