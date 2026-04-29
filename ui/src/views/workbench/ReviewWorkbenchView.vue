<template>
  <ReviewWorkbenchPane :view="reviewView" />
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";

import {
  createProject,
  importProject,
  selectProjectFolder,
  type ChapterRecord,
  type EntityRecord,
  type ReviewPacketRecord,
  type VolumeRecord,
  type WorldbookRecord,
} from "@/api/storyCanvas";
import ReviewWorkbenchPane from "@/components/workbench/ReviewWorkbenchPane.vue";
import { useWorkspace } from "@/composables/useWorkspace";
import { applyTreeOrder, buildProjectOptionLabel, moveTreeItem, syncTreeOrder, type TreeDragKind } from "@/views/workbench/shared";

type ActionItem = {
  title: string;
  detail: string;
  status: string;
};

type ProtocolEntry = {
  label: string;
  value: string;
};

type SidebarGroupKey = "reviewChapters" | "reviewEntities" | "reviewReference";
type DetailMode = "chapter" | "entity" | "reference";
type ReferenceKind = "worldbook" | "volume" | "reviewPacket";
type ReferenceItem = {
  id: string;
  kind: ReferenceKind;
  title: string;
  subtitle: string;
  detail: string;
  meta: ProtocolEntry[];
  chapters?: VolumeRecord["chapters"];
  preview?: string;
  filePath?: string;
  exists?: boolean;
};

const workspace = useWorkspace();

defineModel<"review" | "illustration">("workspaceMode", { required: true });

const emit = defineEmits<{
  (
    event: "workspace-status",
    payload: {
      contextLabel: string;
      contextValue: string;
      detailLabel: string;
      detailValue: string;
      auxLabel: string;
      auxValue: string;
    }
  ): void;
  (event: "open-illustration-target", payload: { type: "entity"; id: string }): void;
}>();

const summary = computed(() => workspace.summary.value);
const workspaceError = computed(() => workspace.error.value);
const selectedRoot = computed(() => workspace.selectedRoot.value);

const selectedChapter = ref<ChapterRecord | null>(null);
const selectedEntityId = ref("");
const selectedReferenceId = ref("");
const detailMode = ref<DetailMode>("chapter");
const viewportWidth = ref(typeof window === "undefined" ? 1440 : window.innerWidth);
const isMobileLayout = computed(() => viewportWidth.value <= 900);

const projectPanelMode = ref<"import" | "create">("import");
const showProjectSetup = ref(false);
const creatingProject = ref(false);
const selectingProjectFolder = ref(false);
const projectTitleDraft = ref("");
const projectGenreDraft = ref("");
const projectDirectoryDraft = ref("");
const importProjectRootDraft = ref("");
const errorMessage = ref("");

const chapterOrderIds = ref<string[]>([]);
const entityOrderIds = ref<string[]>([]);
const dragState = ref<{ kind: TreeDragKind; id: string } | null>(null);
const sidebarGroupOpen = reactive<Record<SidebarGroupKey, boolean>>({
  reviewChapters: true,
  reviewEntities: true,
  reviewReference: false,
});

const chapterList = computed(() => summary.value?.chapters || []);
const entityList = computed(() => summary.value?.entities || []);
const worldbookList = computed(() => summary.value?.worldbook?.entries || []);
const volumeList = computed(() => summary.value?.volumes || []);
const reviewPacketList = computed(() => summary.value?.reviewPackets || []);
const existingReviewPacketCount = computed(() => reviewPacketList.value.filter((item) => item.exists).length);
const sidebarMessage = computed(() => errorMessage.value || workspaceError.value);
const explorerProjectOptions = computed(() => {
  const seen = new Set<string>();
  return workspace.projects.value
    .filter((item) => {
      if (seen.has(item.root)) {
        return false;
      }
      seen.add(item.root);
      return true;
    })
    .map((item) => ({
      label: buildProjectOptionLabel(item),
      value: item.root,
    }));
});
const orderedChapterList = computed(() => applyTreeOrder(chapterList.value, chapterOrderIds.value));
const orderedEntityList = computed(() => applyTreeOrder(entityList.value, entityOrderIds.value));
const selectedEntity = computed(() => entityList.value.find((item) => item.id === selectedEntityId.value) || null);
const referenceItems = computed<ReferenceItem[]>(() => [
  ...worldbookList.value.map(buildWorldbookReference),
  ...volumeList.value.map(buildVolumeReference),
  ...reviewPacketList.value.map(buildReviewPacketReference),
]);
const worldbookReferenceItems = computed(() => referenceItems.value.filter((item) => item.kind === "worldbook"));
const volumeReferenceItems = computed(() => referenceItems.value.filter((item) => item.kind === "volume"));
const reviewPacketReferenceItems = computed(() => referenceItems.value.filter((item) => item.kind === "reviewPacket"));
const selectedReference = computed(() => referenceItems.value.find((item) => item.id === selectedReferenceId.value) || null);

const visibleIssues = computed(() => {
  if (!selectedChapter.value) {
    return [];
  }
  return selectedChapter.value.issues.length > 0 ? selectedChapter.value.issues : ["暂无高优先级问题"];
});

const protocolEntries = computed<ProtocolEntry[]>(() => {
  const project = summary.value?.project;
  return [
    ...flattenProtocolEntries(project?.positioning).slice(0, 2),
    ...flattenProtocolEntries(project?.storyContract).slice(0, 1),
    ...flattenProtocolEntries(project?.commercialPositioning).slice(0, 1),
  ].slice(0, 4);
});

const actionQueue = computed<ActionItem[]>(() => {
  if (!selectedChapter.value) {
    return [];
  }
  return selectedChapter.value.issues.length > 0
    ? selectedChapter.value.issues.slice(0, 2).map((issue, index) => ({
        title: `修复项 ${index + 1}`,
        detail: issue,
        status: index === 0 ? "优先" : "排队",
      }))
    : [
        {
          title: "继续复检",
          detail: "当前没有暴露高优先级问题，可以转向下一轮复检。",
          status: "观察",
        },
      ];
});

function updateViewportWidth() {
  viewportWidth.value = window.innerWidth;
}

function refreshProjects() {
  void workspace.refreshProjects();
}

function expandChapterSidebarGroups() {
  sidebarGroupOpen.reviewChapters = true;
}

function handleProjectSelect(value: string) {
  showProjectSetup.value = false;
  expandChapterSidebarGroups();
  void workspace.selectProject(value);
}

function leaveProject() {
  showProjectSetup.value = false;
  errorMessage.value = "";
  void workspace.selectProject("");
}

async function handleCreateProject() {
  const title = projectTitleDraft.value.trim();
  if (!title) {
    errorMessage.value = "请先填写项目标题。";
    return;
  }
  creatingProject.value = true;
  errorMessage.value = "";
  try {
    const payload = await createProject({
      title,
      genre: projectGenreDraft.value.trim(),
      directoryName: projectDirectoryDraft.value.trim() || undefined,
    });
    showProjectSetup.value = false;
    projectTitleDraft.value = "";
    projectGenreDraft.value = "";
    projectDirectoryDraft.value = "";
    await workspace.refreshProjects();
    expandChapterSidebarGroups();
    await workspace.selectProject(payload.project.project.root);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    creatingProject.value = false;
  }
}

async function handleImportProject() {
  const root = importProjectRootDraft.value.trim();
  if (!root) {
    errorMessage.value = "请先填写要导入的项目路径。";
    return;
  }
  creatingProject.value = true;
  errorMessage.value = "";
  try {
    const payload = await importProject({ root });
    importProjectRootDraft.value = "";
    showProjectSetup.value = false;
    await workspace.refreshProjects();
    expandChapterSidebarGroups();
    await workspace.selectProject(payload.project.project.root);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    creatingProject.value = false;
  }
}

async function handleSelectProjectFolder() {
  selectingProjectFolder.value = true;
  errorMessage.value = "";
  try {
    const payload = await selectProjectFolder({
      initialPath: importProjectRootDraft.value.trim() || selectedRoot.value || undefined,
    });
    importProjectRootDraft.value = payload.path;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    selectingProjectFolder.value = false;
  }
}

function handleTreeDragStart(kind: TreeDragKind, id: string) {
  dragState.value = { kind, id };
}

function handleTreeDrop(kind: TreeDragKind, targetId: string) {
  if (!dragState.value || dragState.value.kind !== kind || dragState.value.id === targetId) {
    return;
  }
  if (kind === "chapter") {
    chapterOrderIds.value = moveTreeItem(chapterOrderIds.value, dragState.value.id, targetId);
  } else {
    entityOrderIds.value = moveTreeItem(entityOrderIds.value, dragState.value.id, targetId);
  }
  dragState.value = null;
}

function selectChapter(item: ChapterRecord) {
  selectedChapter.value = item;
  detailMode.value = "chapter";
}

function selectEntity(item: EntityRecord) {
  selectedEntityId.value = item.id;
  detailMode.value = "entity";
}

function selectReference(item: ReferenceItem) {
  selectedReferenceId.value = item.id;
  detailMode.value = "reference";
}

function handleSidebarGroupToggle(key: SidebarGroupKey, event: Event) {
  sidebarGroupOpen[key] = (event.currentTarget as HTMLDetailsElement).open;
}

function openEntityIllustration(entityId: string) {
  emit("open-illustration-target", { type: "entity", id: entityId });
}

watch(
  chapterList,
  (items) => {
    chapterOrderIds.value = syncTreeOrder(chapterOrderIds.value, items.map((item) => item.id));
    if (items.length === 0) {
      selectedChapter.value = null;
      return;
    }
    const current = items.find((item) => item.id === selectedChapter.value?.id);
    if (current) {
      selectedChapter.value = current;
      return;
    }
    if (!selectedChapter.value) {
      selectedChapter.value = applyTreeOrder(items, chapterOrderIds.value)[0] || null;
    }
  },
  { immediate: true }
);

watch(
  entityList,
  (items) => {
    entityOrderIds.value = syncTreeOrder(entityOrderIds.value, items.map((item) => item.id));
    if (selectedEntityId.value && !items.some((item) => item.id === selectedEntityId.value)) {
      selectedEntityId.value = "";
      if (detailMode.value === "entity") {
        detailMode.value = "chapter";
      }
    }
  },
  { immediate: true }
);

watch(
  referenceItems,
  (items) => {
    if (selectedReferenceId.value && !items.some((item) => item.id === selectedReferenceId.value)) {
      selectedReferenceId.value = "";
      if (detailMode.value === "reference") {
        detailMode.value = "chapter";
      }
    }
  },
  { immediate: true }
);

watch(
  () => selectedRoot.value,
  () => {
    selectedChapter.value = null;
    selectedEntityId.value = "";
    selectedReferenceId.value = "";
    detailMode.value = "chapter";
    chapterOrderIds.value = [];
    entityOrderIds.value = [];
  }
);

watch(
  () =>
    [
      detailMode.value,
      selectedChapter.value?.title || "",
      selectedChapter.value?.reviewScore || 0,
      selectedChapter.value?.wordCount || 0,
      selectedEntity.value?.name || "",
      selectedReference.value?.title || "",
    ] as const,
  ([mode, chapterTitle, reviewScore, wordCount, entityName, referenceTitle]) => {
    if (mode === "entity") {
      emit("workspace-status", {
        contextLabel: "角色",
        contextValue: entityName || "未选择角色",
        detailLabel: "类型",
        detailValue: selectedEntity.value?.type || "-",
        auxLabel: "资料",
        auxValue: selectedEntity.value?.summary ? "已接入" : "-",
      });
      return;
    }
    if (mode === "reference") {
      emit("workspace-status", {
        contextLabel: "资料",
        contextValue: referenceTitle || "未选择资料",
        detailLabel: "类型",
        detailValue: selectedReference.value?.subtitle || "-",
        auxLabel: "来源",
        auxValue: selectedReference.value?.exists === false ? "未生成" : "协议",
      });
      return;
    }
    emit("workspace-status", {
      contextLabel: "章节",
      contextValue: chapterTitle || "未选择章节",
      detailLabel: "评分",
      detailValue: chapterTitle ? `${reviewScore} 分` : "-",
      auxLabel: "字数",
      auxValue: chapterTitle ? `${wordCount} 字` : "-",
    });
  },
  { immediate: true }
);

watch(
  isMobileLayout,
  (mobile) => {
    if (mobile) {
      sidebarGroupOpen.reviewEntities = false;
      sidebarGroupOpen.reviewReference = false;
    }
  },
  { immediate: true }
);

watch(
  () => workspace.error.value,
  (value) => {
    if (value) {
      errorMessage.value = value;
    }
  }
);

onMounted(() => {
  updateViewportWidth();
  window.addEventListener("resize", updateViewportWidth);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", updateViewportWidth);
});

const reviewView = {
  summary,
  selectedRoot,
  showProjectSetup,
  projectPanelMode,
  importProjectRootDraft,
  projectTitleDraft,
  projectGenreDraft,
  projectDirectoryDraft,
  selectingProjectFolder,
  creatingProject,
  sidebarMessage,
  sidebarGroupOpen,
  chapterList,
  entityList,
  orderedChapterList,
  orderedEntityList,
  selectedChapter,
  selectedEntity,
  selectedReference,
  detailMode,
  worldbookList,
  volumeList,
  reviewPacketList,
  existingReviewPacketCount,
  referenceItems,
  worldbookReferenceItems,
  volumeReferenceItems,
  reviewPacketReferenceItems,
  visibleIssues,
  actionQueue,
  protocolEntries,
  explorerProjectOptions,
  refreshProjects,
  handleProjectSelect,
  leaveProject,
  handleSelectProjectFolder,
  handleImportProject,
  handleCreateProject,
  handleSidebarGroupToggle,
  handleTreeDragStart,
  handleTreeDrop,
  selectChapter,
  selectEntity,
  selectReference,
  openEntityIllustration,
};

function buildWorldbookReference(item: WorldbookRecord): ReferenceItem {
  return {
    id: `worldbook::${item.sourceKey || item.type}::${item.id}`,
    kind: "worldbook",
    title: item.name,
    subtitle: item.label || item.type,
    detail: item.summary || item.detail || "当前条目没有摘要。",
    meta: [
      { label: "类型", value: item.type },
      { label: "来源", value: item.sourceKey || "worldbook" },
    ],
  };
}

function buildVolumeReference(item: VolumeRecord): ReferenceItem {
  return {
    id: `volume::${item.id}`,
    kind: "volume",
    title: item.title,
    subtitle: item.id,
    detail: item.theme || "当前卷没有主题摘要。",
    chapters: item.chapters,
    meta: [
      { label: "章节数", value: String(item.chapterCount) },
      { label: "审查包", value: item.reviewPacket?.exists ? item.reviewPacket.filePath : "未生成" },
    ],
  };
}

function buildReviewPacketReference(item: ReviewPacketRecord): ReferenceItem {
  return {
    id: item.id,
    kind: "reviewPacket",
    title: item.title,
    subtitle: item.volumeId,
    detail: item.exists ? item.filePath : "审查包尚未生成。",
    preview: item.preview || "",
    filePath: item.filePath,
    exists: item.exists,
    meta: [
      { label: "文件", value: item.filePath },
      { label: "更新时间", value: item.updatedAt || "未生成" },
    ],
  };
}

function flattenProtocolEntries(source: Record<string, unknown> | undefined, prefix = "", depth = 0): ProtocolEntry[] {
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

    return [{ label, value: formatValue(rawValue) }];
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
