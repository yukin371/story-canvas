<template>
  <div class="chapter-layout">
    <section class="chapter-list">
      <t-card title="章节" class="surface-card">
        <p v-if="error" class="inline-error">{{ error }}</p>
        <div class="chapter-stack">
          <button
            v-for="item in chapterList"
            :key="item.id"
            class="chapter-card"
            :class="{ 'is-active': item.id === selectedChapter?.id }"
            type="button"
            @click="selectedChapter = item"
          >
            <div class="chapter-card-head">
              <strong>{{ item.title }}</strong>
              <span>{{ item.status }}</span>
            </div>
            <p>{{ item.summary }}</p>
            <small>{{ item.updatedAt }}</small>
          </button>
        </div>
      </t-card>
    </section>

    <section class="chapter-detail">
      <template v-if="selectedChapter">
        <t-card title="审查摘要" class="surface-card packet-card">
          <div class="packet-header">
            <div class="packet-title">
              <h3>{{ selectedChapter.title }}</h3>
              <p class="detail-copy">
                {{ selectedChapter.reviewSummary || "当前章节还没有可展示的审查摘要。" }}
              </p>
            </div>

            <div class="packet-score">
              <t-progress theme="circle" :percentage="selectedChapter.reviewScore" :stroke-width="8" />
              <div class="packet-score-copy">
                <strong>{{ selectedChapter.reviewScore }}</strong>
                <span>{{ reviewTone }}</span>
              </div>
            </div>
          </div>

          <div class="packet-metrics">
            <article v-for="item in packetMetrics" :key="item.label" class="metric-tile">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <p>{{ item.detail }}</p>
            </article>
          </div>
        </t-card>

        <div class="chapter-workbench">
          <t-card title="问题与动作" class="surface-card">
            <div class="issue-list">
              <div v-for="issue in visibleIssues" :key="issue" class="issue-chip">
                {{ issue }}
              </div>
            </div>

            <div class="action-stack">
              <article v-for="item in actionQueue" :key="item.title" class="action-item">
                <div class="action-head">
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.status }}</span>
                </div>
                <p>{{ item.detail }}</p>
              </article>
            </div>
          </t-card>

          <t-card title="协议上下文镜头" class="surface-card">
            <div class="protocol-sections">
              <article v-for="section in protocolSections" :key="section.key" class="protocol-card">
                <div class="protocol-head">
                  <strong>{{ section.title }}</strong>
                  <span>{{ section.entries.length }} 条</span>
                </div>

                <div v-if="section.entries.length > 0" class="fact-grid">
                  <div v-for="entry in section.entries" :key="`${section.key}-${entry.label}`" class="fact-item">
                    <span>{{ entry.label }}</span>
                    <strong>{{ entry.value }}</strong>
                  </div>
                </div>
                <p v-else class="detail-copy">当前项目还没有这组协议字段。</p>
              </article>
            </div>
          </t-card>
        </div>
      </template>

      <t-card v-else title="审查概览" class="surface-card">
        <p class="detail-copy">当前项目没有章节数据。</p>
      </t-card>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { TCard, TProgress } from "@/tdesign/display";
import type { ChapterRecord } from "@/api/storyCanvas";
import { useWorkspace } from "@/composables/useWorkspace";

type PacketMetric = {
  label: string;
  value: string;
  detail: string;
};

type ProtocolEntry = {
  label: string;
  value: string;
};

type ProtocolSection = {
  key: string;
  title: string;
  entries: ProtocolEntry[];
};

type ActionItem = {
  title: string;
  detail: string;
  status: string;
};

const workspace = useWorkspace();
const error = computed(() => workspace.error.value);
const summary = computed(() => workspace.summary.value);
const chapterList = computed(() => workspace.summary.value?.chapters || []);
const selectedChapter = ref<ChapterRecord | null>(null);

const visibleIssues = computed(() => {
  if (!selectedChapter.value) {
    return [];
  }
  if (selectedChapter.value.issues.length > 0) {
    return selectedChapter.value.issues;
  }
  return ["当前章节暂无高优先级问题。"];
});

const reviewTone = computed(() => {
  const score = selectedChapter.value?.reviewScore ?? 0;
  if (score >= 85) {
    return "可进入复检";
  }
  if (score >= 70) {
    return "建议定向修补";
  }
  return "需要回到审查队列";
});

const packetMetrics = computed<PacketMetric[]>(() => {
  if (!selectedChapter.value) {
    return [];
  }
  return [
    {
      label: "章节标识",
      value: selectedChapter.value.id,
      detail: "当前选中的章节协议 ID",
    },
    {
      label: "审查状态",
      value: selectedChapter.value.status,
      detail: selectedChapter.value.updatedAt || "暂无审查时间",
    },
    {
      label: "字数",
      value: String(selectedChapter.value.wordCount),
      detail: "正文词数估算",
    },
    {
      label: "优先问题",
      value: String(selectedChapter.value.issues.length),
      detail: "来自当前审查结果的问题数",
    },
  ];
});

const protocolSections = computed<ProtocolSection[]>(() => {
  const project = summary.value?.project;
  return [
    buildProtocolSection("positioning", "Positioning", project?.positioning),
    buildProtocolSection("contract", "Story Contract", project?.storyContract),
    buildProtocolSection("commercial", "Commercial Positioning", project?.commercialPositioning),
  ];
});

const actionQueue = computed<ActionItem[]>(() => {
  if (!selectedChapter.value) {
    return [];
  }

  const baseIssues =
    selectedChapter.value.issues.length > 0
      ? selectedChapter.value.issues.map((issue, index) => ({
          title: `修复项 ${index + 1}`,
          detail: issue,
          status: index === 0 ? "优先" : "待排队",
        }))
      : [
          {
            title: "继续下一轮检查",
            detail: "当前 summary 没有暴露高优先级问题，可以转向复检或下一章。",
            status: "观察",
          },
        ];

  const protocolCount = protocolSections.value.reduce((count, section) => count + section.entries.length, 0);

  return [
    {
      title: "回看本章摘要",
      detail: selectedChapter.value.reviewSummary || "当前章节暂无审查摘要文本。",
      status: "已加载",
    },
    ...baseIssues,
    {
      title: "对齐协议约束",
      detail:
        protocolCount > 0
          ? `当前项目已暴露 ${protocolCount} 条协议字段，可直接拿来对照本章修改。`
          : "项目协议字段尚未暴露到这一页，后续需要 API 补齐更完整的 context lens。",
      status: protocolCount > 0 ? "可用" : "待接入",
    },
  ];
});

watch(
  chapterList,
  (items) => {
    if (items.length === 0) {
      selectedChapter.value = null;
      return;
    }
    if (!selectedChapter.value || !items.some((item) => item.id === selectedChapter.value?.id)) {
      selectedChapter.value = items[0];
    }
  },
  { immediate: true }
);

function buildProtocolSection(
  key: string,
  title: string,
  source: Record<string, unknown> | undefined
): ProtocolSection {
  return {
    key,
    title,
    entries: flattenProtocolEntries(source),
  };
}

function flattenProtocolEntries(
  source: Record<string, unknown> | undefined,
  prefix = "",
  depth = 0
): ProtocolEntry[] {
  if (!source || typeof source !== "object") {
    return [];
  }

  return Object.entries(source).flatMap(([rawKey, rawValue]) => {
    if (rawValue === null || rawValue === undefined || rawValue === "") {
      return [];
    }

    const label = prefix ? `${prefix} / ${formatKey(rawKey)}` : formatKey(rawKey);

    if (!Array.isArray(rawValue) && typeof rawValue === "object" && depth < 1) {
      return flattenProtocolEntries(rawValue as Record<string, unknown>, label, depth + 1);
    }

    return [
      {
        label,
        value: formatValue(rawValue),
      },
    ];
  });
}

function formatKey(value: string): string {
  return value
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/[_-]+/g, " ")
    .trim();
}

function formatValue(value: unknown): string {
  if (Array.isArray(value)) {
    return value
      .map((item) => formatValue(item))
      .filter(Boolean)
      .join(" / ");
  }
  if (typeof value === "object" && value !== null) {
    return JSON.stringify(value, null, 0);
  }
  return String(value);
}
</script>
