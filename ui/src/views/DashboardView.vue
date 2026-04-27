<template>
  <div class="dashboard-layout">
    <section class="summary-grid">
      <article v-for="item in dynamicStats" :key="item.label" class="summary-card">
        <span class="summary-label">{{ item.label }}</span>
        <strong class="summary-value">{{ item.value }}</strong>
        <p class="summary-detail">{{ item.detail }}</p>
      </article>
    </section>

    <section class="dashboard-columns">
      <t-card title="项目状态" class="surface-card">
        <p v-if="error" class="inline-error">{{ error }}</p>
        <div class="fact-list">
          <div v-for="item in workspaceFacts" :key="item.label" class="fact-row">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
      </t-card>

      <t-card title="最近章节" class="surface-card">
        <t-list split>
          <t-list-item v-for="chapter in chapterEntries" :key="chapter.title">
            <t-list-item-meta :title="chapter.title" :description="`${chapter.status} · ${chapter.updatedAt}`" />
            <template #action>
              <div class="job-meta">
                <span>{{ chapter.wordCount }}</span>
                <t-tag variant="light-outline">{{ chapter.reviewScore }}</t-tag>
              </div>
            </template>
          </t-list-item>
        </t-list>
      </t-card>
    </section>

    <section class="dashboard-columns">
      <t-card title="Workflow" class="surface-card">
        <div class="fact-list">
          <div v-for="item in workflowFacts" :key="item.label" class="fact-row">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
      </t-card>

      <t-card title="最近插画任务" class="surface-card">
        <t-list split>
          <t-list-item v-for="job in illustrationEntries" :key="job.title">
            <t-list-item-meta :title="job.title" :description="`${job.target} · ${job.updatedAt}`" />
            <template #action>
              <div class="job-meta">
                <span>{{ job.mode }}</span>
                <t-tag variant="light-outline">{{ job.status }}</t-tag>
              </div>
            </template>
          </t-list-item>
        </t-list>
      </t-card>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { useWorkspace } from "@/composables/useWorkspace";

type FactItem = {
  label: string;
  value: string;
};

const workspace = useWorkspace();

const error = computed(() => workspace.error.value);
const summary = computed(() => workspace.summary.value);

const dynamicStats = computed(() => {
  const project = summary.value?.project;
  const stats = summary.value?.stats;
  const workflow = summary.value?.workflow;
  return [
    {
      label: "当前项目",
      value: project?.title || "-",
      detail: project?.genre || "未选择项目",
    },
    {
      label: "章节总数",
      value: String(stats?.chapterCount ?? 0),
      detail: `已审查 ${stats?.reviewedChapterCount ?? 0} 章`,
    },
    {
      label: "插画资产",
      value: String(stats?.illustrationCount ?? 0),
      detail: `角色实体 ${stats?.entityCount ?? 0} 个`,
    },
    {
      label: "Workflow",
      value: workflow?.currentStage || "-",
      detail: workflow?.workflowStatus || "未运行",
    },
  ];
});

const workspaceFacts = computed<FactItem[]>(() => {
  const project = summary.value?.project;
  const stats = summary.value?.stats;
  return [
    { label: "项目", value: project?.title || "-" },
    { label: "题材", value: project?.genre || "-" },
    { label: "活跃章节", value: project?.activeChapterId || "-" },
    { label: "角色数", value: String(stats?.entityCount ?? 0) },
  ];
});

const workflowFacts = computed<FactItem[]>(() => {
  const workflow = summary.value?.workflow;
  return [
    { label: "当前阶段", value: workflow?.currentStage || "-" },
    { label: "状态", value: workflow?.workflowStatus || "-" },
    { label: "更新时间", value: workflow?.updatedAt || "-" },
  ];
});

const chapterEntries = computed(() =>
  (summary.value?.chapters || []).slice(0, 5).map((item) => ({
    title: item.title,
    status: item.status,
    updatedAt: item.updatedAt || "-",
    wordCount: `${item.wordCount} 字`,
    reviewScore: `${item.reviewScore} 分`,
  }))
);

const illustrationEntries = computed(() =>
  (summary.value?.illustrations || []).slice(0, 5).map((item) => ({
    title: item.revisedPrompt || item.promptText || item.targetRef?.targetId || "illustration",
    mode: item.mode || "text-to-image",
    target: item.targetRef?.targetId || item.chapterId || item.entityId || "unknown",
    status: item.artifacts?.some((asset) => asset.exists) ? "已落盘" : "待确认",
    updatedAt: item.generatedAt || "",
  }))
);
</script>
