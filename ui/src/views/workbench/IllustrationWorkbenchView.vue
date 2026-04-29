<template>
  <IllustrationWorkbenchPane :view="illustrationView" />
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";

import {
  buildWorkbenchAssetUrl,
  buildProjectAssetUrl,
  createProject,
  dryRunIllustration,
  dryRunIllustrationForm,
  fetchPromptPackLibrary,
  getIllustrationDefaultUseCase,
  getIllustrationTemplateOptions,
  getIllustrationUseCaseOptions,
  ILLUSTRATION_TEXT_DESIGN_OPTIONS,
  importProject,
  openLocalFolder,
  pickIllustrationTemplateId,
  pickIllustrationUseCase,
  selectProjectFolder,
  savePromptPack,
  type EntityRecord,
  type IllustrationDryRunResult,
  type IllustrationGenerateResult,
  type IllustrationRecord,
  type IllustrationTargetType,
  type IllustrationTextDesignMode,
  type IllustrationTemplateSummary,
  type PromptPackCommercialPolicyDocument,
  type PromptPackDocument,
  type PromptPackLibraryResponse,
  type PromptPackModifierDocument,
  type PromptPackNegativePolicyDocument,
  type PromptPackTemplateDocument,
  generateIllustration,
  generateIllustrationForm,
} from "@/api/storyCanvas";
import { useWorkspace } from "@/composables/useWorkspace";
import { applyTreeOrder, buildProjectOptionLabel, moveTreeItem, syncTreeOrder, type TreeDragKind } from "@/views/workbench/shared";

const IllustrationWorkbenchPane = defineAsyncComponent(() => import("@/components/workbench/IllustrationWorkbenchPane.vue"));

type IllustrationHistoryRow = {
  id: string;
  title: string;
  target: string;
  mode: string;
  updatedAt: string;
  scope: "project" | "workspace";
  sourceLabel: string;
  root: string;
  raw: IllustrationRecord;
};

type ResultExportItem = {
  id: string;
  label: string;
  href: string;
  downloadName: string;
  isPrimary: boolean;
};

type PromptPackTemplateOption = IllustrationTemplateSummary;

type PromptModifierOption = {
  id: string;
  group: string;
  label: string;
  negativeFragment?: string;
};

type PromptNegativePolicy = {
  id: string;
  label: string;
  negativePrompt: string;
};

type PromptPackSourceGroup = {
  key: string;
  label: string;
  packs: Array<{
    id: string;
    name: string;
    label: string;
    source?: string;
  }>;
};

type SidebarGroupKey =
  | "illustrationEntities"
  | "illustrationChapters"
  | "illustrationHistory";

function historyTimestamp(value: string): number {
  const timestamp = Date.parse(value);
  return Number.isNaN(timestamp) ? 0 : timestamp;
}

function formatHistoryTarget(item: IllustrationRecord): string {
  const targetName = String(item.targetName || "").trim();
  const targetId = String(item.targetRef?.targetId || item.chapterId || item.entityId || item.tempLabel || "").trim();
  if (targetName) {
    if (!targetId || targetId === targetName || targetId.startsWith("workspace-")) {
      return targetName;
    }
    return `${targetName} · ${targetId}`;
  }
  return targetId || "-";
}

function buildHistoryRows(
  records: IllustrationRecord[],
  scope: "project" | "workspace",
  root: string,
): IllustrationHistoryRow[] {
  return [...records]
    .reverse()
    .map((item) => ({
      id: item.id || `${item.generatedAt || "history"}-${item.targetRef?.targetId || item.chapterId || item.entityId || "item"}`,
      title: item.revisedPrompt || item.promptText || "illustration",
      target: formatHistoryTarget(item),
      mode: item.mode || "text-to-image",
      updatedAt: item.generatedAt || "-",
      scope,
      sourceLabel: scope === "workspace" ? "自由模式" : "当前项目",
      root,
      raw: item,
    }));
}

const workspace = useWorkspace();

const props = defineProps<{
  pendingTarget?: { type: "chapter" | "entity"; id: string } | null;
}>();

const emit = defineEmits<{
  (event: "open-settings"): void;
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
  (event: "consume-pending-target"): void;
}>();

const summary = computed(() => workspace.summary.value);
const settings = computed(() => workspace.settings.value);
const workspaceError = computed(() => workspace.error.value);
const selectedRoot = computed(() => workspace.selectedRoot.value);
const isProjectBound = computed(() => Boolean(summary.value?.project.root));

const workspaceMode = defineModel<"review" | "illustration">("workspaceMode", { required: true });
const viewportWidth = ref(typeof window === "undefined" ? 1440 : window.innerWidth);
const isTabletLayout = computed(() => viewportWidth.value <= 1180);
const isMobileLayout = computed(() => viewportWidth.value <= 900);
const showAdvancedTemplateEditor = ref(false);

const projectPanelMode = ref<"import" | "create">("import");
const showProjectSetup = ref(false);
const creatingProject = ref(false);
const selectingProjectFolder = ref(false);
const projectTitleDraft = ref("");
const projectGenreDraft = ref("");
const projectDirectoryDraft = ref("");
const importProjectRootDraft = ref("");

const mode = ref<"text-to-image" | "image-to-image" | "inpaint">("text-to-image");
const targetType = ref<"chapter" | "entity">("chapter");
const targetId = ref("");
const manualTargetName = ref("");
const useCase = ref(getIllustrationDefaultUseCase(targetType.value));
const textDesignMode = ref<IllustrationTextDesignMode>("none");
const titleText = ref("");
const subtitleText = ref("");
const bodyText = ref("");
const fontStyleHint = ref("");
const promptPack = ref("default");
const templateId = ref("");
const modifierRefs = ref<string[]>([]);
const commercialMode = ref<"personal" | "commercial">("personal");
const responseModel = ref("gpt-5.4");
const size = ref("1024x1024");
const quality = ref("high");
const batchCount = ref(1);
const outputName = ref("");
const positivePrompt = ref("");
const negativePrompt = ref("");

const inputImageFile = ref<File | null>(null);
const maskFile = ref<File | null>(null);
const inputImagePath = ref("");
const maskPath = ref("");
const inputImagePreviewUrl = ref("");
const maskPreviewUrl = ref("");

const dryRunResult = ref<IllustrationDryRunResult | null>(null);
const generateResult = ref<IllustrationGenerateResult | null>(null);
const activePreviewRecord = ref<IllustrationRecord | null>(null);
const activePreviewScope = ref<"project" | "workspace" | null>(null);
const activePreviewRoot = ref("");
const resultLightboxVisible = ref(false);
const submitting = ref(false);
const errorMessage = ref("");
const promptPackLibrary = ref<PromptPackLibraryResponse | null>(null);
const loadingPromptPackLibrary = ref(false);
const savingPromptPackLibrary = ref(false);
const promptPackLibraryError = ref("");
const promptPackDraft = ref<PromptPackDocument | null>(null);
const promptPackDraftFileName = ref("");
const promptPackDraftTemplateId = ref("");
const promptPackDraftMode = ref<"new" | "copy" | "edit">("new");
const promptPackSetAsDefault = ref(false);
const syncedProjectRoot = ref("");
const lastAutoPrompt = ref("");
const lastAutoNegativePrompt = ref("");

const chapterOrderIds = ref<string[]>([]);
const entityOrderIds = ref<string[]>([]);
const dragState = ref<{ kind: TreeDragKind; id: string } | null>(null);
const sidebarGroupOpen = reactive<Record<SidebarGroupKey, boolean>>({
  illustrationEntities: true,
  illustrationChapters: true,
  illustrationHistory: false,
});

async function refreshLatestIllustrationPreview(forceRefresh = false) {
  if (forceRefresh) {
    if (workspace.selectedRoot.value) {
      await Promise.all([workspace.refreshSummary(), workspace.refreshSettings(workspace.selectedRoot.value)]);
    } else {
      await workspace.refreshSettings("");
    }
  }
  await nextTick();
  if (generateResult.value?.illustration || dryRunResult.value) {
    return;
  }
  setActivePreviewFromHistoryRow(latestHistoryRow.value);
}

function handleWindowFocusRefresh() {
  void refreshLatestIllustrationPreview(true);
}

function handleVisibilityRefresh() {
  if (document.visibilityState !== "visible") {
    return;
  }
  void refreshLatestIllustrationPreview(true);
}

function updateViewportWidth() {
  viewportWidth.value = window.innerWidth;
}

const responseModelOptions = [
  { label: "gpt-5.4", value: "gpt-5.4" },
  { label: "gpt-5.5", value: "gpt-5.5" },
];
const sizeOptions = [
  { label: "1024 x 1024", value: "1024x1024" },
  { label: "1536 x 1024", value: "1536x1024" },
  { label: "1024 x 1536", value: "1024x1536" },
];
const qualityOptions = [
  { label: "auto", value: "auto" },
  { label: "medium", value: "medium" },
  { label: "high", value: "high" },
];
const commercialModeOptions = [
  { label: "个人", value: "personal" },
  { label: "商用", value: "commercial" },
];

const chapterList = computed(() => summary.value?.chapters || []);
const entityList = computed(() => summary.value?.entities || []);
const sidebarMessage = computed(() => errorMessage.value || workspaceError.value);
const explorerProjectOptions = computed(() => {
  const seen = new Set<string>();
  const options = workspace.projects.value
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
  return options;
});

const orderedChapterList = computed(() => applyTreeOrder(chapterList.value, chapterOrderIds.value));
const orderedEntityList = computed(() => applyTreeOrder(entityList.value, entityOrderIds.value));

const targetOptions = computed(() => {
  if (targetType.value === "entity") {
    return (summary.value?.entities || []).map((item) => ({
      label: item.appearanceSummary ? `${item.name} · ${item.appearanceSummary}` : item.name,
      value: item.id,
    }));
  }
  return (summary.value?.chapters || []).map((item) => ({
    label: `${item.title} · ${item.id}`,
    value: item.id,
  }));
});

const projectIllustrationHistory = computed<IllustrationHistoryRow[]>(() =>
  buildHistoryRows(summary.value?.illustrations || [], "project", summary.value?.project.root || "")
);
const workspaceIllustrationHistory = computed<IllustrationHistoryRow[]>(() =>
  buildHistoryRows(
    settings.value?.workspaceIllustration.recentIllustrations || [],
    "workspace",
    settings.value?.workspaceIllustration.root || "",
  )
);
const illustrationHistory = computed<IllustrationHistoryRow[]>(() => {
  if (!summary.value) {
    return workspaceIllustrationHistory.value;
  }
  return [...projectIllustrationHistory.value, ...workspaceIllustrationHistory.value].sort(
    (left, right) => historyTimestamp(right.updatedAt) - historyTimestamp(left.updatedAt)
  );
});
const historyEmptyCopy = computed(() =>
  summary.value ? "当前项目和自由模式都还没有插画记录。" : "自由模式还没有插画记录。"
);

const availablePromptPacks = computed(
  () =>
    promptPackLibrary.value?.availablePromptPacks ||
    summary.value?.illustrationConfig.availablePromptPacks ||
    settings.value?.workspaceIllustration.availablePromptPacks ||
    []
);
const promptPackDocuments = computed(() => promptPackLibrary.value?.packs || []);
const promptPackSourceGroups = computed<PromptPackSourceGroup[]>(() => {
  const systemPacks = availablePromptPacks.value.filter((item) => String(item.source || "").trim() === "builtin");
  const userPacks = availablePromptPacks.value.filter((item) => String(item.source || "").trim() !== "builtin");
  return [
    {
      key: "system",
      label: "系统模板",
      packs: systemPacks,
    },
    {
      key: "user",
      label: "用户模板",
      packs: userPacks,
    },
  ].filter((group) => group.packs.length > 0);
});
const selectedPromptPack = computed(() => {
  return availablePromptPacks.value.find((item) => item.name === promptPack.value) || availablePromptPacks.value[0];
});
const selectedPromptPackDocument = computed<PromptPackDocument | null>(() => {
  const selected = selectedPromptPack.value;
  if (!selected) {
    return null;
  }
  return promptPackDocuments.value.find((item) => item.id === selected.id || item.name === selected.name) || null;
});
const packTemplates = computed<PromptPackTemplateOption[]>(() => (selectedPromptPack.value?.templates || []) as PromptPackTemplateOption[]);
const modifierOptions = computed<PromptModifierOption[]>(() => (selectedPromptPack.value?.modifierGroups || []) as PromptModifierOption[]);
const negativePolicies = computed<PromptNegativePolicy[]>(() => (selectedPromptPack.value?.negativePolicies || []) as PromptNegativePolicy[]);
const selectedTemplate = computed<PromptPackTemplateOption | null>(() => {
  return packTemplates.value.find((item) => item.id === templateId.value) || null;
});
const selectedEntity = computed<EntityRecord | null>(() => {
  if (targetType.value !== "entity") {
    return null;
  }
  return (summary.value?.entities || []).find((item) => item.id === targetId.value) || null;
});

const promptPackOptions = computed(() =>
  availablePromptPacks.value.map((item) => ({
    label: item.label,
    value: item.name,
  }))
);
const useCaseOptions = computed(() => getIllustrationUseCaseOptions(packTemplates.value, targetType.value, mode.value));
const templateOptions = computed(() => getIllustrationTemplateOptions(packTemplates.value, mode.value, useCase.value));

const currentTemplateLabel = computed(() => {
  return templateOptions.value.find((item) => item.value === templateId.value)?.label || templateId.value || "-";
});
const currentPackLabel = computed(() => selectedPromptPack.value?.label || promptPack.value || "-");
const currentModeLabel = computed(() => {
  if (mode.value === "image-to-image") {
    return "图生图";
  }
  if (mode.value === "inpaint") {
    return "重绘";
  }
  return "文生图";
});
const currentPackSourceLabel = computed(() => {
  const source = String(selectedPromptPack.value?.source || "").trim();
  return source === "builtin" ? "系统模板" : source ? "用户模板" : "-";
});
const modifierSummaryLabel = computed(() => {
  const labels = modifierOptions.value
    .filter((item) => modifierRefs.value.includes(item.id))
    .map((item) => item.label);
  return labels.length > 0 ? labels.join(" / ") : "未选择";
});
const promptPackDraftTemplate = computed<PromptPackTemplateDocument | null>(() => {
  if (!promptPackDraft.value) {
    return null;
  }
  return promptPackDraft.value.templates.find((item) => item.id === promptPackDraftTemplateId.value) || promptPackDraft.value.templates[0] || null;
});
const promptPackDraftNegativePolicyOptions = computed(() =>
  (promptPackDraft.value?.policies.negativePolicies || []).map((item) => ({
    label: item.label || item.id || "未命名负向策略",
    value: item.id,
  }))
);
const promptPackDraftCommercialPolicyOptions = computed(() =>
  (promptPackDraft.value?.policies.commercialPolicies || []).map((item) => ({
    label: item.label || item.id || "未命名商用策略",
    value: item.id,
  }))
);
const promptPackLibraryDir = computed(
  () =>
    promptPackLibrary.value?.userPromptPackDir ||
    summary.value?.illustrationConfig.promptPackDir ||
    settings.value?.workspaceIllustration.promptPackDir ||
    ""
);
const promptPackDraftStateLabel = computed(() => {
  if (!promptPackDraft.value) {
    return "未打开编辑器";
  }
  if (promptPackDraftMode.value === "edit") {
    return "编辑用户模板";
  }
  if (promptPackDraftMode.value === "copy") {
    return "复制系统模板";
  }
  return "新建用户模板";
});
const negativePromptStateLabel = computed(() => (negativePrompt.value.trim() ? "已填写" : "未填写"));
const resolvedPromptPreview = computed(() => {
  const generatedPrompt = generateResult.value?.illustration.promptSnapshot?.resolvedPrompt;
  const dryRunPrompt = typeof dryRunResult.value?.promptSnapshot?.resolvedPrompt === "string" ? dryRunResult.value.promptSnapshot.resolvedPrompt : "";
  return generatedPrompt || dryRunPrompt || positivePrompt.value.trim() || "";
});
const resolvedNegativePreview = computed(() => {
  const generatedNegative = generateResult.value?.illustration.policySnapshot?.negativePrompt;
  const dryRunNegative = typeof dryRunResult.value?.policySnapshot?.negativePrompt === "string" ? dryRunResult.value.policySnapshot.negativePrompt : "";
  return generatedNegative || dryRunNegative || negativePrompt.value.trim() || "";
});
const outputNameStateLabel = computed(() => (outputName.value.trim() ? outputName.value.trim() : "默认命名"));

const currentProjectRoot = computed(() => summary.value?.project.root || "");
function fileNameFromPath(filePath: string): string {
  return filePath.split(/[\\/]/).pop() || filePath;
}

function fileDirFromPath(filePath: string): string {
  const normalized = filePath.replace(/\\/g, "/");
  const cut = normalized.lastIndexOf("/");
  return cut >= 0 ? normalized.slice(0, cut) : "";
}

function buildIllustrationAssetUrl(filePath: string, scope: string, root: string): string {
  if (!filePath) {
    return "";
  }
  if (scope === "workspace" || !root) {
    return buildWorkbenchAssetUrl(filePath);
  }
  return buildProjectAssetUrl(root, filePath);
}

const inputImageDisplayName = computed(() => inputImageFile.value?.name || inputImagePath.value || "");
const maskDisplayName = computed(() => maskFile.value?.name || maskPath.value || "");
const inputImageResolvedPreviewUrl = computed(() => {
  if (inputImagePreviewUrl.value) {
    return inputImagePreviewUrl.value;
  }
  if (!currentProjectRoot.value || !inputImagePath.value) {
    return "";
  }
  return buildProjectAssetUrl(currentProjectRoot.value, inputImagePath.value);
});
const maskResolvedPreviewUrl = computed(() => {
  if (maskPreviewUrl.value) {
    return maskPreviewUrl.value;
  }
  if (!currentProjectRoot.value || !maskPath.value) {
    return "";
  }
  return buildProjectAssetUrl(currentProjectRoot.value, maskPath.value);
});

const latestProjectHistoryRow = computed<IllustrationHistoryRow | null>(() => projectIllustrationHistory.value[0] || null);
const latestWorkspaceHistoryRow = computed<IllustrationHistoryRow | null>(() => workspaceIllustrationHistory.value[0] || null);
const latestHistoryRow = computed<IllustrationHistoryRow | null>(() =>
  summary.value ? latestProjectHistoryRow.value || latestWorkspaceHistoryRow.value : latestWorkspaceHistoryRow.value
);
const latestHistoryRecord = computed<IllustrationRecord | null>(() => latestHistoryRow.value?.raw || null);
const previewRecord = computed(
  () => generateResult.value?.illustration || activePreviewRecord.value || latestHistoryRecord.value
);
const resultScope = computed(
  () => generateResult.value?.scope || activePreviewScope.value || (currentProjectRoot.value ? "project" : "workspace")
);
const resultRoot = computed(() => generateResult.value?.summary?.project.root || activePreviewRoot.value || currentProjectRoot.value);
const resultSourceLabel = computed(() => {
  if (generateResult.value?.illustration) {
    return "本次生成";
  }
  if (activePreviewRecord.value?.id && latestHistoryRecord.value?.id) {
    return activePreviewRecord.value.id === latestHistoryRecord.value.id ? "最近生成" : "历史记录";
  }
  if (activePreviewRecord.value) {
    return "历史记录";
  }
  if (latestHistoryRecord.value) {
    return "最近生成";
  }
  if (dryRunResult.value) {
    return "试运行";
  }
  return "等待结果";
});
const resultPreviewUrl = computed(() => {
  const filePath = previewRecord.value?.filePath || "";
  if (!filePath) {
    return "";
  }
  return buildIllustrationAssetUrl(filePath, resultScope.value, resultRoot.value);
});
const resultExportItems = computed<ResultExportItem[]>(() => {
  if (!previewRecord.value) {
    return [];
  }
  const artifacts =
    previewRecord.value.artifacts && previewRecord.value.artifacts.length > 0
      ? previewRecord.value.artifacts.filter((item) => item.exists !== false && item.filePath)
      : previewRecord.value.filePath
        ? [{ filePath: previewRecord.value.filePath, exists: true, isPrimary: true }]
        : [];
  return artifacts
    .map((item, index) => {
      const href = buildIllustrationAssetUrl(item.filePath, resultScope.value, resultRoot.value);
      return {
        id: `${previewRecord.value?.id || "illustration"}-${index}`,
        label: item.isPrimary ? "导出主图" : `导出变体 ${index + 1}`,
        href,
        downloadName: fileNameFromPath(item.filePath),
        isPrimary: Boolean(item.isPrimary),
      };
    })
    .filter((item) => item.href);
});
const primaryResultExportItem = computed<ResultExportItem | null>(
  () => resultExportItems.value.find((item) => item.isPrimary) || resultExportItems.value[0] || null
);
const resultArtifactFolder = computed(() => {
  const filePath = previewRecord.value?.filePath || dryRunResult.value?.outputFile || "";
  return fileDirFromPath(filePath);
});
const resultPackLabel = computed(() => {
  const packId = previewRecord.value?.promptSnapshot?.packRef?.packId || previewRecord.value?.promptPackRef?.packId || "";
  if (!packId) {
    return currentPackLabel.value;
  }
  const match = availablePromptPacks.value.find((item) => item.id === packId || item.name === packId);
  return match?.label || packId.split("/").pop() || currentPackLabel.value;
});
const resultTemplateLabel = computed(() => {
  const templateRef = previewRecord.value?.templateId || previewRecord.value?.promptSnapshot?.templateRef || "";
  if (!templateRef) {
    return currentTemplateLabel.value;
  }
  const match = availablePromptPacks.value
    .flatMap((item) => item.templates || [])
    .find((template) => template.id === templateRef);
  return match?.label || templateRef;
});
const resultModifierLabel = computed(() => {
  const refs = previewRecord.value?.promptSnapshot?.modifierRefs || previewRecord.value?.modifierRefs || [];
  if (refs.length === 0) {
    return modifierSummaryLabel.value;
  }
  const labels = refs
    .map((item) => modifierOptions.value.find((option) => option.id === item)?.label || item)
    .filter(Boolean);
  return labels.length > 0 ? labels.join(" / ") : modifierSummaryLabel.value;
});

const resultSummary = computed(() => {
  if (previewRecord.value) {
    const item = previewRecord.value;
    return {
      mode: item.mode || "-",
      target: (item as IllustrationRecord & { targetLabel?: string }).targetLabel || formatHistoryTarget(item),
      output: item.filePath || "-",
      text: item.revisedPrompt || item.promptSnapshot?.resolvedPrompt || item.promptText || "-",
      batchCount: item.batch?.count || 1,
    };
  }
  if (dryRunResult.value) {
    const payload = dryRunResult.value.payload as {
      mode?: string;
      targetId?: string;
      promptText?: string;
      batch?: {
        count?: number;
      };
    };
    return {
      mode: payload.mode || "-",
      target: String((dryRunResult.value as IllustrationDryRunResult & { targetLabel?: string }).targetLabel || payload.targetId || "-"),
      output: dryRunResult.value.outputFile,
      text: payload.promptText || "-",
      batchCount: payload.batch?.count || 1,
    };
  }
  return null;
});
const currentTargetLabel = computed(() => {
  if (!summary.value) {
    return manualTargetName.value.trim() || (targetType.value === "entity" ? "自由角色" : "自由场景");
  }
  if (targetType.value === "entity") {
    return selectedEntity.value?.name || targetId.value || "-";
  }
  return chapterList.value.find((item) => item.id === targetId.value)?.title || targetId.value || "-";
});

const promptSeedTitle = computed(() => (targetType.value === "entity" ? "角色卡外貌基线" : "场景提示基线"));
const promptSeedHint = computed(() => {
  if (targetType.value === "entity") {
    if (!summary.value) {
      return "当前未绑定项目，按自由角色模式处理；建议把外貌、服装和气质直接写进正面提示词。";
    }
    const entity = selectedEntity.value;
    if (!entity) {
      return "选择角色后，会优先回填角色卡里的外貌、状态和人物简介。";
    }
    return entity.appearanceSummary || entity.summary || "当前角色卡还没有明确外貌描述，请在下方手动补充。";
  }
  if (!summary.value) {
    return "当前未绑定项目，按自由场景模式处理；请直接填写人物、动作、镜头、环境和氛围。";
  }
  return "章节模式不再自动注入正文；请手动填写出场角色、动作、镜头、环境和氛围。";
});

const defaultNegativePrompt = computed(() => {
  const policyRef = selectedTemplate.value?.defaultNegativePolicyRef || "";
  const base = negativePolicies.value.find((item) => item.id === policyRef)?.negativePrompt || "";
  const modifierNegative = modifierOptions.value
    .filter((item) => modifierRefs.value.includes(item.id) && item.negativeFragment)
    .map((item) => item.negativeFragment?.trim() || "")
    .filter(Boolean)
    .join(", ");
  return [base.trim(), modifierNegative].filter(Boolean).join(", ");
});

const illustrationSetupWarning = computed(() => {
  if (!settings.value?.local.apiKeyConfigured) {
    return "缺少提供商 API key。请先进入设置页保存本地 key，或通过环境变量提供。";
  }
  if (!summary.value) {
    return "";
  }
  const adapterName = summary.value.illustrationConfig.adapterName || "";
  if (!adapterName) {
    return "当前项目没有服务商配置。";
  }
  if (adapterName !== "openai") {
    return `当前工作台只支持 openai adapter，当前为 ${adapterName}。`;
  }
  return "";
});

function refreshProjects() {
  void workspace.refreshProjects();
}

function expandIllustrationSidebarGroups() {
  sidebarGroupOpen.illustrationChapters = true;
}

onMounted(() => {
  updateViewportWidth();
  window.addEventListener("resize", updateViewportWidth);
  window.addEventListener("focus", handleWindowFocusRefresh);
  document.addEventListener("visibilitychange", handleVisibilityRefresh);
  void refreshLatestIllustrationPreview(true);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", updateViewportWidth);
  window.removeEventListener("focus", handleWindowFocusRefresh);
  document.removeEventListener("visibilitychange", handleVisibilityRefresh);
});

async function handleProjectSelect(value: string) {
  showProjectSetup.value = false;
  expandIllustrationSidebarGroups();
  await workspace.selectProject(value);
  await refreshLatestIllustrationPreview(false);
}

function leaveProject() {
  showProjectSetup.value = false;
  syncedProjectRoot.value = "";
  resetResultPanels();
  clearInputImageSelection();
  clearMaskSelection();
  inputImagePath.value = "";
  maskPath.value = "";
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
    expandIllustrationSidebarGroups();
    await workspace.selectProject(payload.project.project.root);
    await refreshLatestIllustrationPreview(false);
    workspaceMode.value = "illustration";
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
    expandIllustrationSidebarGroups();
    await workspace.selectProject(payload.project.project.root);
    await refreshLatestIllustrationPreview(false);
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

function handleSidebarGroupToggle(key: SidebarGroupKey, event: Event) {
  sidebarGroupOpen[key] = (event.currentTarget as HTMLDetailsElement).open;
}

function openEntityIllustration(entityId: string) {
  workspaceMode.value = "illustration";
  targetType.value = "entity";
  targetId.value = entityId;
  applySuggestedPrompt(true);
  applySuggestedNegativePrompt(true);
}

function openChapterIllustration(chapterId: string) {
  workspaceMode.value = "illustration";
  targetType.value = "chapter";
  targetId.value = chapterId;
  applySuggestedPrompt(true);
  applySuggestedNegativePrompt(true);
}

function resetResultPanels() {
  dryRunResult.value = null;
  generateResult.value = null;
  setActivePreviewFromHistoryRow(null);
  resultLightboxVisible.value = false;
}

function setActivePreviewFromHistoryRow(item: IllustrationHistoryRow | null) {
  activePreviewRecord.value = item?.raw || null;
  activePreviewScope.value = item?.scope || null;
  activePreviewRoot.value = item?.root || "";
}

function openResultLightbox() {
  if (!resultPreviewUrl.value) {
    return;
  }
  resultLightboxVisible.value = true;
}

function closeResultLightbox() {
  resultLightboxVisible.value = false;
}
function clonePromptPackDocument(pack: PromptPackDocument | null): PromptPackDocument | null {
  if (!pack) {
    return null;
  }
  return JSON.parse(JSON.stringify(pack)) as PromptPackDocument;
}

function slugifyPromptPackFileName(value: string): string {
  return (
    value
      .trim()
      .replace(/[\\/]+/g, "-")
      .replace(/[<>:"|?*\u0000-\u001f]+/g, "-")
      .replace(/\s+/g, "-")
      .replace(/-{2,}/g, "-")
      .replace(/^-+|-+$/g, "") || "custom-pack"
  );
}

function basePromptPackFileName(pack: PromptPackDocument | null): string {
  const sourceFile = String(pack?.sourceFile || "").trim();
  if (sourceFile) {
    const match = sourceFile.split(/[\\/]/).pop() || "";
    return match.replace(/\.yaml$/i, "");
  }
  return slugifyPromptPackFileName(String(pack?.name || pack?.label || pack?.id || "custom-pack"));
}

function createDraftTemplate(useCase = getIllustrationDefaultUseCase(targetType.value)): PromptPackTemplateDocument {
  const draftId = `draft-${useCase}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
  return {
    id: draftId,
    label: "",
    useCase,
    mode: mode.value,
    complexity: "standard",
    promptTemplate: "{subject}\n{styleModifiers}\n{userExtraPrompt}",
    defaultNegativePolicyRef: "",
    defaultCommercialPolicyRef: "",
  };
}

function createDraftModifier(): PromptPackModifierDocument {
  const draftId = `draft-modifier-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
  return {
    id: draftId,
    group: "style",
    label: "",
    promptFragment: "",
    negativeFragment: "",
    commercialTags: [],
  };
}

function createDraftNegativePolicy(): PromptPackNegativePolicyDocument {
  const draftId = `draft-negative-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
  return {
    id: draftId,
    label: "",
    negativePrompt: "",
  };
}

function createDraftCommercialPolicy(): PromptPackCommercialPolicyDocument {
  const draftId = `draft-commercial-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
  return {
    id: draftId,
    label: "",
    mode: "personal",
    extraPrompt: "",
    restrictions: [],
  };
}

function createEmptyPromptPackDraft(): PromptPackDocument {
  return {
    id: "",
    version: "project",
    label: "",
    description: "",
    supports: {
      modes: [mode.value],
      commercial: true,
    },
    templates: [createDraftTemplate()],
    modifierGroups: [],
    policies: {
      negativePolicies: [],
      commercialPolicies: [],
    },
  };
}

function applyPromptPackDraft(pack: PromptPackDocument, draftMode: "new" | "copy" | "edit", fileName = "") {
  promptPackDraft.value = clonePromptPackDocument(pack);
  promptPackDraftMode.value = draftMode;
  promptPackDraftFileName.value = slugifyPromptPackFileName(fileName || basePromptPackFileName(pack));
  promptPackDraftTemplateId.value = promptPackDraft.value?.templates[0]?.id || "";
  const defaultPackName = summary.value?.illustrationConfig.promptPackName || settings.value?.workspaceIllustration.promptPackName || "";
  promptPackSetAsDefault.value = draftMode !== "new" && defaultPackName === (pack.name || "");
}

async function refreshPromptPackLibrary(root = summary.value?.project.root || "") {
  loadingPromptPackLibrary.value = true;
  promptPackLibraryError.value = "";
  try {
    promptPackLibrary.value = await fetchPromptPackLibrary(root || undefined);
  } catch (error) {
    promptPackLibraryError.value = error instanceof Error ? error.message : String(error);
  } finally {
    loadingPromptPackLibrary.value = false;
  }
}

function startNewPromptPackDraft() {
  applyPromptPackDraft(createEmptyPromptPackDraft(), "new", `自定义-${targetType.value === "entity" ? "角色" : "场景"}-${mode.value}`);
}

function startDraftFromSelectedPack() {
  const source = selectedPromptPackDocument.value;
  if (!source) {
    startNewPromptPackDraft();
    return;
  }
  const draft = clonePromptPackDocument(source) || createEmptyPromptPackDraft();
  const isBuiltin = String(source.source || "").trim() === "builtin";
  if (isBuiltin) {
    draft.id = "";
    draft.name = "";
    draft.version = "project";
    draft.source = "";
    draft.sourceFile = "";
    draft.writable = true;
  }
  applyPromptPackDraft(
    draft,
    isBuiltin ? "copy" : "edit",
    isBuiltin ? `${basePromptPackFileName(source)}-custom` : basePromptPackFileName(source)
  );
}

function resetPromptPackDraft() {
  if (selectedPromptPackDocument.value) {
    startDraftFromSelectedPack();
    return;
  }
  startNewPromptPackDraft();
}

function addPromptPackDraftTemplate() {
  if (!promptPackDraft.value) {
    startNewPromptPackDraft();
  }
  const nextTemplate = createDraftTemplate();
  promptPackDraft.value?.templates.push(nextTemplate);
  promptPackDraftTemplateId.value = nextTemplate.id;
}

function removePromptPackDraftTemplate(templateToRemove: PromptPackTemplateDocument) {
  if (!promptPackDraft.value) {
    return;
  }
  promptPackDraft.value.templates = promptPackDraft.value.templates.filter((item) => item !== templateToRemove);
  if (promptPackDraft.value.templates.length === 0) {
    promptPackDraft.value.templates.push(createDraftTemplate());
  }
  promptPackDraftTemplateId.value = promptPackDraft.value.templates[0]?.id || "";
}

function addPromptPackDraftModifier() {
  if (!promptPackDraft.value) {
    startNewPromptPackDraft();
  }
  promptPackDraft.value?.modifierGroups.push(createDraftModifier());
}

function removePromptPackDraftModifier(index: number) {
  promptPackDraft.value?.modifierGroups.splice(index, 1);
}

function addPromptPackDraftNegativePolicy() {
  if (!promptPackDraft.value) {
    startNewPromptPackDraft();
  }
  promptPackDraft.value?.policies.negativePolicies.push(createDraftNegativePolicy());
}

function removePromptPackDraftNegativePolicy(index: number) {
  promptPackDraft.value?.policies.negativePolicies.splice(index, 1);
}

function addPromptPackDraftCommercialPolicy() {
  if (!promptPackDraft.value) {
    startNewPromptPackDraft();
  }
  promptPackDraft.value?.policies.commercialPolicies.push(createDraftCommercialPolicy());
}

function removePromptPackDraftCommercialPolicy(index: number) {
  promptPackDraft.value?.policies.commercialPolicies.splice(index, 1);
}

function normalizePromptPackDraftForSave(pack: PromptPackDocument): PromptPackDocument {
  const cloned = clonePromptPackDocument(pack) || createEmptyPromptPackDraft();
  cloned.label = cloned.label.trim();
  cloned.description = cloned.description.trim();
  cloned.templates = cloned.templates.map((item) => ({
    ...item,
    id: item.id.trim(),
    label: item.label.trim(),
    useCase: item.useCase.trim(),
    mode: item.mode.trim(),
    complexity: item.complexity.trim() || "standard",
    promptTemplate: item.promptTemplate,
    defaultNegativePolicyRef: item.defaultNegativePolicyRef?.trim() || "",
    defaultCommercialPolicyRef: item.defaultCommercialPolicyRef?.trim() || "",
  }));
  cloned.modifierGroups = cloned.modifierGroups.map((item) => ({
    ...item,
    id: item.id.trim(),
    group: item.group.trim() || "style",
    label: item.label.trim(),
    promptFragment: item.promptFragment,
    negativeFragment: item.negativeFragment?.trim() || "",
    commercialTags: item.commercialTags || [],
  }));
  cloned.policies = {
    negativePolicies: (cloned.policies.negativePolicies || []).map((item) => ({
      ...item,
      id: item.id.trim(),
      label: item.label.trim(),
      negativePrompt: item.negativePrompt,
    })),
    commercialPolicies: (cloned.policies.commercialPolicies || []).map((item) => ({
      ...item,
      id: item.id.trim(),
      label: item.label.trim(),
      mode: item.mode.trim() || "personal",
      extraPrompt: item.extraPrompt,
      restrictions: item.restrictions || [],
    })),
  };
  return cloned;
}

async function handleSavePromptPackDraft() {
  if (!promptPackDraft.value) {
    startNewPromptPackDraft();
    return;
  }
  const fileName = slugifyPromptPackFileName(promptPackDraftFileName.value);
  if (!promptPackDraft.value.label.trim()) {
    promptPackLibraryError.value = "请先填写模板包名称。";
    return;
  }
  if (!fileName) {
    promptPackLibraryError.value = "请先填写文件名。";
    return;
  }
  if (!promptPackDraft.value.templates.some((item) => item.id.trim() && item.useCase.trim() && item.promptTemplate.trim())) {
    promptPackLibraryError.value = "至少保留一个有效模板。";
    return;
  }
  promptPackLibraryError.value = "";
  savingPromptPackLibrary.value = true;
  try {
    const payload = await savePromptPack({
      root: summary.value?.project.root || undefined,
      fileName,
      setAsDefault: Boolean(summary.value?.project.root) && promptPackSetAsDefault.value,
      pack: normalizePromptPackDraftForSave(promptPackDraft.value),
    });
    promptPackLibrary.value = payload;
    const savedPackName = payload.savedPack?.name || "";
    if (savedPackName) {
      promptPack.value = savedPackName;
    }
    await Promise.all([
      workspace.refreshSettings(summary.value?.project.root || ""),
      summary.value?.project.root ? workspace.refreshSummary() : Promise.resolve(),
    ]);
    if (payload.savedPack) {
      applyPromptPackDraft(payload.savedPack, "edit");
    }
  } catch (error) {
    promptPackLibraryError.value = error instanceof Error ? error.message : String(error);
  } finally {
    savingPromptPackLibrary.value = false;
  }
}

function syncFromProject() {
  const projectSummary = summary.value;
  const config = projectSummary?.illustrationConfig || settings.value?.workspaceIllustration;
  if (!config) {
    return;
  }
  syncedProjectRoot.value = projectSummary?.project.root || "";
  responseModel.value = config.responseModel || "gpt-5.4";
  size.value = config.defaultSize || "1024x1024";
  quality.value = config.quality || "auto";
  batchCount.value = parseInt(config.defaultBatchCount || "1", 10) || 1;
  outputName.value = "";
  promptPack.value = config.promptPackName || "default";
  commercialMode.value = config.commercialMode || "personal";
  modifierRefs.value = [...(config.defaultModifierRefs || [])];
  mode.value = "text-to-image";
  textDesignMode.value = "none";
  titleText.value = "";
  subtitleText.value = "";
  bodyText.value = "";
  fontStyleHint.value = "";
  clearInputImageSelection();
  clearMaskSelection();
  inputImagePath.value = "";
  maskPath.value = "";
  resetResultPanels();
  errorMessage.value = "";

  if (projectSummary?.entities.length) {
    targetType.value = "entity";
    targetId.value = projectSummary.entities[0].id;
  } else if (projectSummary?.project.activeChapterId) {
    targetType.value = "chapter";
    targetId.value = projectSummary.project.activeChapterId;
  } else if (projectSummary?.chapters.length) {
    targetType.value = "chapter";
    targetId.value = projectSummary.chapters[0].id;
  } else {
    targetId.value = "";
  }
  if (!projectSummary) {
    manualTargetName.value = targetType.value === "entity" ? "自由角色" : "自由场景";
  }

  useCase.value = pickIllustrationUseCase(
    packTemplates.value,
    targetType.value,
    mode.value,
    getIllustrationDefaultUseCase(targetType.value)
  );
  const nextTemplate =
    (config.defaultTemplateByUseCase?.[useCase.value] || "") &&
    packTemplates.value.some((item) => item.id === config.defaultTemplateByUseCase?.[useCase.value])
      ? String(config.defaultTemplateByUseCase?.[useCase.value] || "")
      : "";
  templateId.value = pickIllustrationTemplateId(packTemplates.value, mode.value, useCase.value, nextTemplate);
  applySuggestedPrompt(true);
  applySuggestedNegativePrompt(true);
}

function buildIllustrationRequest() {
  const boundRoot = summary.value?.project.root || "";
  const isFreeMode = !boundRoot;
  if (!isFreeMode && !targetId.value) {
    throw new Error("请选择目标章节或角色。");
  }
  if (isFreeMode && !manualTargetName.value.trim()) {
    throw new Error("自由模式下请先填写目标。");
  }
  if (!positivePrompt.value.trim()) {
    throw new Error("请先填写正面提示词。");
  }
  if ((mode.value === "image-to-image" || mode.value === "inpaint") && !inputImageFile.value && !inputImagePath.value.trim()) {
    throw new Error("图生图 / 重绘模式需要提供源图。");
  }
  if (mode.value === "inpaint" && !maskFile.value && !maskPath.value.trim()) {
    throw new Error("重绘模式需要提供 mask。");
  }
  return {
    root: boundRoot || undefined,
    mode: mode.value,
    targetType: targetType.value,
    useCase: useCase.value || undefined,
    textDesignMode: textDesignMode.value,
    titleText: textDesignMode.value === "designed" ? titleText.value.trim() || undefined : undefined,
    subtitleText: textDesignMode.value === "designed" ? subtitleText.value.trim() || undefined : undefined,
    bodyText: textDesignMode.value === "designed" ? bodyText.value.trim() || undefined : undefined,
    fontStyleHint: textDesignMode.value === "designed" ? fontStyleHint.value.trim() || undefined : undefined,
    manualTargetName: isFreeMode ? manualTargetName.value.trim() : undefined,
    chapterId: !isFreeMode && targetType.value === "chapter" ? targetId.value : undefined,
    entityId: !isFreeMode && targetType.value === "entity" ? targetId.value : undefined,
    promptText: positivePrompt.value.trim(),
    extraPrompt: positivePrompt.value.trim(),
    negativePrompt: negativePrompt.value.trim() || undefined,
    promptPack: promptPack.value || undefined,
    templateId: templateId.value || undefined,
    modifierRefs: [...modifierRefs.value],
    commercialMode: commercialMode.value,
    size: size.value,
    quality: quality.value,
    batchCount: batchCount.value,
    baseUrl: boundRoot ? summary.value?.illustrationConfig.baseUrl || undefined : settings.value?.workspaceIllustration.baseUrl || undefined,
    responseModel: responseModel.value,
    outputName: outputName.value.trim() || undefined,
    inputImages: mode.value === "image-to-image" || mode.value === "inpaint" ? [inputImagePath.value.trim()] : [],
    maskPath: mode.value === "inpaint" ? maskPath.value.trim() || undefined : undefined,
  };
}

function buildIllustrationFormData() {
  const request = buildIllustrationRequest();
  const body = new FormData();
  const usesInputImage = mode.value === "image-to-image" || mode.value === "inpaint";
  const usesMask = mode.value === "inpaint";
  if (request.root) {
    body.append("root", request.root);
  }
  if (request.targetType) {
    body.append("targetType", request.targetType);
  }
  if (request.manualTargetName) {
    body.append("manualTargetName", request.manualTargetName);
  }
  if (request.textDesignMode) {
    body.append("textDesignMode", request.textDesignMode);
  }
  if (request.titleText) {
    body.append("titleText", request.titleText);
  }
  if (request.subtitleText) {
    body.append("subtitleText", request.subtitleText);
  }
  if (request.bodyText) {
    body.append("bodyText", request.bodyText);
  }
  if (request.fontStyleHint) {
    body.append("fontStyleHint", request.fontStyleHint);
  }
  body.append("mode", request.mode);
  if (request.chapterId) {
    body.append("chapterId", request.chapterId);
  }
  if (request.entityId) {
    body.append("entityId", request.entityId);
  }
  if (request.promptText) {
    body.append("promptText", request.promptText);
    body.append("extraPrompt", request.promptText);
  }
  if (request.negativePrompt) {
    body.append("negativePrompt", request.negativePrompt);
  }
  if (request.promptPack) {
    body.append("promptPack", request.promptPack);
  }
  if (request.useCase) {
    body.append("useCase", request.useCase);
  }
  if (request.templateId) {
    body.append("templateId", request.templateId);
  }
  for (const item of request.modifierRefs || []) {
    body.append("modifierRefs", item);
  }
  if (request.commercialMode) {
    body.append("commercialMode", request.commercialMode);
  }
  if (request.size) {
    body.append("size", request.size);
  }
  if (request.quality) {
    body.append("quality", request.quality);
  }
  if (request.batchCount && request.batchCount > 1) {
    body.append("batchCount", String(request.batchCount));
  }
  if (request.responseModel) {
    body.append("responseModel", request.responseModel);
  }
  if (request.baseUrl) {
    body.append("baseUrl", request.baseUrl);
  }
  if (request.outputName) {
    body.append("outputName", request.outputName);
  }
  if (usesInputImage) {
    if (inputImageFile.value) {
      body.append("inputImageFile", inputImageFile.value);
    } else if (request.inputImages?.[0]) {
      body.append("inputImagePath", request.inputImages[0]);
    }
  }
  if (usesMask) {
    if (maskFile.value) {
      body.append("maskFile", maskFile.value);
    } else if (request.maskPath) {
      body.append("maskPath", request.maskPath);
    }
  }
  return body;
}

async function applyHistoryItem(item: IllustrationHistoryRow) {
  workspaceMode.value = "illustration";
  if (item.scope === "workspace" && summary.value?.project.root) {
    await workspace.selectProject("");
    await nextTick();
  }
  const record = item.raw;
  const nextTargetType = record.targetRef?.type === "entity" || record.entityId ? "entity" : "chapter";
  const nextPromptPack = resolveHistoryPromptPack(record) || promptPack.value;
  targetType.value = nextTargetType;
  targetId.value = item.scope === "project" ? record.targetRef?.targetId || record.chapterId || record.entityId || "" : "";
  manualTargetName.value =
    item.scope === "workspace"
      ? String(record.targetName || "").trim() || (nextTargetType === "entity" ? "自由角色" : "自由场景")
      : manualTargetName.value;
  mode.value = record.mode === "image-to-image" || record.mode === "inpaint" ? record.mode : "text-to-image";
  promptPack.value = nextPromptPack;
  useCase.value = resolveHistoryUseCase(record, nextPromptPack, nextTargetType);
  templateId.value = record.templateId || record.promptSnapshot?.templateRef || "";
  modifierRefs.value = [...(record.promptSnapshot?.modifierRefs || record.modifierRefs || [])];
  commercialMode.value = record.commercialMode || record.policySnapshot?.commercialMode || "personal";
  textDesignMode.value = record.promptSnapshot?.textDesign?.mode === "designed" ? "designed" : "none";
  titleText.value = record.promptSnapshot?.textDesign?.titleText || "";
  subtitleText.value = record.promptSnapshot?.textDesign?.subtitleText || "";
  bodyText.value = record.promptSnapshot?.textDesign?.bodyText || "";
  fontStyleHint.value = record.promptSnapshot?.textDesign?.fontStyleHint || "";
  batchCount.value = record.batch?.count || 1;
  outputName.value = record.filePath?.split(/[\\/]/).pop() || "";
  positivePrompt.value = record.promptSnapshot?.userExtraPrompt || record.promptText || "";
  negativePrompt.value = record.policySnapshot?.negativePrompt || "";
  lastAutoPrompt.value = "";
  lastAutoNegativePrompt.value = "";
  clearInputImageSelection();
  clearMaskSelection();
  inputImagePath.value = record.inputImages?.[0] || "";
  maskPath.value = record.maskPath || "";
  errorMessage.value = "";
  dryRunResult.value = null;
  generateResult.value = null;
  setActivePreviewFromHistoryRow(item);
}

function resolveHistoryPromptPack(item: IllustrationRecord): string {
  const packId = item.promptSnapshot?.packRef?.packId || item.promptPackRef?.packId;
  if (!packId) {
    return "";
  }
  const match = availablePromptPacks.value.find((pack) => pack.id === packId || pack.name === packId);
  return match?.name || "";
}

function resolveHistoryUseCase(item: IllustrationRecord, packName: string, target: IllustrationTargetType): string {
  if (item.useCase) {
    return item.useCase;
  }
  const templateRef = item.templateId || item.promptSnapshot?.templateRef || "";
  if (templateRef) {
    const pack = availablePromptPacks.value.find((entry) => entry.name === packName);
    const matchedTemplate = pack?.templates.find((template) => template.id === templateRef);
    if (matchedTemplate?.useCase) {
      return matchedTemplate.useCase;
    }
  }
  return getIllustrationDefaultUseCase(target);
}

function toggleModifier(modifierId: string) {
  if (modifierRefs.value.includes(modifierId)) {
    modifierRefs.value = modifierRefs.value.filter((item) => item !== modifierId);
    return;
  }
  modifierRefs.value = [...modifierRefs.value, modifierId];
}

function buildEntityPromptSeed(entity: EntityRecord | null): string {
  if (!entity) {
    return "";
  }
  const currentStateText =
    typeof entity.currentState === "string"
      ? entity.currentState
      : entity.currentState && typeof entity.currentState === "object"
        ? Object.values(entity.currentState)
            .map((item) => String(item ?? "").trim())
            .filter(Boolean)
            .join("；")
        : "";
  const fragments = [entity.appearanceSummary || "", currentStateText, entity.summary || ""]
    .map((item) => item.trim())
    .filter(Boolean);
  return fragments.slice(0, 3).join("；");
}

function applySuggestedPrompt(force = false) {
  const nextPrompt = targetType.value === "entity" ? buildEntityPromptSeed(selectedEntity.value) : "";
  if (!force && positivePrompt.value.trim() && positivePrompt.value !== lastAutoPrompt.value) {
    return;
  }
  positivePrompt.value = nextPrompt;
  lastAutoPrompt.value = nextPrompt;
}

function applySuggestedNegativePrompt(force = false) {
  const nextPrompt = defaultNegativePrompt.value.trim();
  if (!force && negativePrompt.value.trim() && negativePrompt.value !== lastAutoNegativePrompt.value) {
    return;
  }
  negativePrompt.value = nextPrompt;
  lastAutoNegativePrompt.value = nextPrompt;
}

async function handleDryRun() {
  errorMessage.value = "";
  submitting.value = true;
  try {
    const request = buildIllustrationRequest();
    const form = buildIllustrationFormData();
    const useMultipart =
      (mode.value === "image-to-image" || mode.value === "inpaint") &&
      (Boolean(inputImageFile.value) || Boolean(maskFile.value));
    activePreviewRecord.value = null;
    generateResult.value = null;
    dryRunResult.value = useMultipart ? await dryRunIllustrationForm(form) : await dryRunIllustration(request);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    submitting.value = false;
  }
}

async function handleGenerate() {
  errorMessage.value = "";
  if (illustrationSetupWarning.value) {
    errorMessage.value = illustrationSetupWarning.value;
    return;
  }
  submitting.value = true;
  try {
    const request = buildIllustrationRequest();
    const form = buildIllustrationFormData();
    const useMultipart =
      (mode.value === "image-to-image" || mode.value === "inpaint") &&
      (Boolean(inputImageFile.value) || Boolean(maskFile.value));
    activePreviewRecord.value = null;
    activePreviewScope.value = null;
    activePreviewRoot.value = "";
    dryRunResult.value = null;
    generateResult.value = useMultipart ? await generateIllustrationForm(form) : await generateIllustration(request);
    if (generateResult.value.scope === "workspace") {
      await workspace.refreshSettings("");
    } else {
      await workspace.refreshSummary();
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    submitting.value = false;
  }
}

async function handleOpenResultFolder() {
  errorMessage.value = "";
  const targetPath = previewRecord.value?.filePath || "";
  if (!targetPath) {
    errorMessage.value = "当前没有可打开目录的生成结果。";
    return;
  }
  try {
    await openLocalFolder({
      root: resultScope.value === "project" ? resultRoot.value : undefined,
      path: targetPath,
      scope: resultScope.value === "workspace" ? "workspace" : "project",
    });
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : String(error);
  }
}

function revokePreviewUrl(url: string) {
  if (url.startsWith("blob:")) {
    URL.revokeObjectURL(url);
  }
}

function clearInputImageSelection() {
  revokePreviewUrl(inputImagePreviewUrl.value);
  inputImagePreviewUrl.value = "";
  inputImageFile.value = null;
}

function clearMaskSelection() {
  revokePreviewUrl(maskPreviewUrl.value);
  maskPreviewUrl.value = "";
  maskFile.value = null;
}

function handleInputImageChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0] || null;
  clearInputImageSelection();
  if (!file) {
    return;
  }
  inputImageFile.value = file;
  inputImagePath.value = "";
  inputImagePreviewUrl.value = URL.createObjectURL(file);
}

function handleMaskChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0] || null;
  clearMaskSelection();
  if (!file) {
    return;
  }
  maskFile.value = file;
  maskPath.value = "";
  maskPreviewUrl.value = URL.createObjectURL(file);
}

function clearInputAsset(kind: "input" | "mask") {
  if (kind === "input") {
    clearInputImageSelection();
    inputImagePath.value = "";
    return;
  }
  clearMaskSelection();
  maskPath.value = "";
}

watch(
  illustrationHistory,
  (items) => {
    if (generateResult.value?.illustration) {
      return;
    }
    if (items.length === 0) {
      if (!dryRunResult.value) {
        activePreviewRecord.value = null;
      }
      return;
    }
    const activeId = activePreviewRecord.value?.id || "";
    if (activeId) {
      const matched = items.find((item) => item.raw.id === activeId);
      if (matched) {
        activePreviewRecord.value = matched.raw;
        return;
      }
    }
    activePreviewRecord.value = items[0].raw;
  },
  { immediate: true }
);

watch(
  chapterList,
  (items) => {
    chapterOrderIds.value = syncTreeOrder(chapterOrderIds.value, items.map((item) => item.id));
  },
  { immediate: true }
);

watch(
  () =>
    [
      targetType.value,
      currentTargetLabel.value,
      currentPackLabel.value,
      currentModeLabel.value,
      size.value,
      batchCount.value,
    ] as const,
  ([currentTargetType, targetLabel, packLabel, modeLabel, currentSize, currentBatch]) => {
    emit("workspace-status", {
      contextLabel: currentTargetType === "entity" ? "角色" : "场景",
      contextValue: targetLabel || "未选择目标",
      detailLabel: "模板包",
      detailValue: packLabel || "-",
      auxLabel: "出图",
      auxValue: `${modeLabel} · ${currentSize} · x${currentBatch}`,
    });
  },
  { immediate: true }
);

watch(
  entityList,
  (items) => {
    entityOrderIds.value = syncTreeOrder(entityOrderIds.value, items.map((item) => item.id));
  },
  { immediate: true }
);

watch(
  () => [targetType.value, targetOptions.value] as const,
  ([kind, options]) => {
    if (!summary.value) {
      targetId.value = "";
      if (!manualTargetName.value.trim()) {
        manualTargetName.value = kind === "entity" ? "自由角色" : "自由场景";
      }
      return;
    }
    if (options.length === 0) {
      targetId.value = "";
      return;
    }
    if (!options.some((item) => item.value === targetId.value)) {
      if (kind === "chapter") {
        targetId.value = summary.value?.project.activeChapterId || String(options[0].value);
      } else {
        targetId.value = String(options[0].value);
      }
    }
  },
  { immediate: true }
);

watch(
  () => [targetType.value, targetId.value, selectedEntity.value?.id || "", summary.value?.project.root || ""] as const,
  () => {
    applySuggestedPrompt(false);
  },
  { immediate: true }
);

watch(
  () => [packTemplates.value, targetType.value, mode.value, useCase.value] as const,
  ([templates, kind, currentMode, currentUseCase]) => {
    const nextUseCase = pickIllustrationUseCase(templates, kind, currentMode, currentUseCase);
    if (nextUseCase !== useCase.value) {
      useCase.value = nextUseCase;
      return;
    }
    const nextTemplateId = pickIllustrationTemplateId(templates, currentMode, nextUseCase, templateId.value);
    if (nextTemplateId !== templateId.value) {
      templateId.value = nextTemplateId;
    }
    modifierRefs.value = modifierRefs.value.filter((item) => modifierOptions.value.some((option) => option.id === item));
  },
  { immediate: true, deep: true }
);

watch(
  () => [templateId.value, modifierRefs.value.join("|")] as const,
  () => {
    applySuggestedNegativePrompt(false);
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

watch(
  () => summary.value?.project.root || "",
  (root) => {
    void refreshPromptPackLibrary(root);
  },
  { immediate: true }
);

watch(
  selectedPromptPackDocument,
  (pack) => {
    if (!pack) {
      if (!promptPackDraft.value) {
        startNewPromptPackDraft();
      }
      return;
    }
    if (!promptPackDraft.value || promptPackDraftMode.value === "edit") {
      applyPromptPackDraft(pack, String(pack.source || "").trim() === "builtin" ? "copy" : "edit");
    }
  },
  { immediate: true }
);

watch(
  isMobileLayout,
  (mobile) => {
    if (mobile) {
      sidebarGroupOpen.illustrationHistory = false;
    }
  },
  { immediate: true }
);

watch(
  () => [summary.value?.project.root || "", settings.value?.workspaceIllustration.promptPackName || ""] as const,
  ([root]) => {
    if (root === syncedProjectRoot.value && (root || !settings.value?.workspaceIllustration)) {
      return;
    }
    syncedProjectRoot.value = root;
    syncFromProject();
  },
  { immediate: true }
);

watch(
  () => props.pendingTarget,
  (target) => {
    if (!target) {
      return;
    }
    if (target.type === "entity") {
      openEntityIllustration(target.id);
    } else {
      openChapterIllustration(target.id);
    }
    emit("consume-pending-target");
  },
  { immediate: true }
);

const illustrationView = {
  summary,
  selectedRoot,
  isProjectBound,
  showProjectSetup,
  projectPanelMode,
  importProjectRootDraft,
  projectTitleDraft,
  projectGenreDraft,
  projectDirectoryDraft,
  selectingProjectFolder,
  creatingProject,
  sidebarMessage,
  illustrationSetupWarning,
  targetType,
  targetId,
  manualTargetName,
  mode,
  promptPack,
  useCase,
  templateId,
  textDesignMode,
  positivePrompt,
  negativePrompt,
  titleText,
  subtitleText,
  bodyText,
  fontStyleHint,
  outputName,
  modifierRefs,
  showAdvancedTemplateEditor,
  submitting,
  promptPackDraft,
  promptPackDraftFileName,
  promptPackDraftTemplateId,
  promptPackSetAsDefault,
  promptPackLibraryError,
  savingPromptPackLibrary,
  promptPackDraftTemplate,
  promptPackDraftStateLabel,
  currentPackSourceLabel,
  promptPackDraftNegativePolicyOptions,
  promptPackDraftCommercialPolicyOptions,
  explorerProjectOptions,
  targetOptions,
  promptPackOptions,
  useCaseOptions,
  templateOptions,
  entityList,
  chapterList,
  orderedEntityList,
  orderedChapterList,
  illustrationHistory,
  historyEmptyCopy,
  modifierOptions,
  promptSeedTitle,
  inputImageResolvedPreviewUrl,
  maskResolvedPreviewUrl,
  inputImageDisplayName,
  maskDisplayName,
  resolvedPromptPreview,
  resolvedNegativePreview,
  currentTargetLabel,
  currentTemplateLabel,
  modifierSummaryLabel,
  outputNameStateLabel,
  resultSummary,
  resultPreviewUrl,
  resultSourceLabel,
  resultExportItems,
  primaryResultExportItem,
  resultArtifactFolder,
  resultPackLabel,
  resultTemplateLabel,
  resultModifierLabel,
  currentPackLabel,
  negativePromptStateLabel,
  sidebarGroupOpen,
  illustrationTextDesignOptions: ILLUSTRATION_TEXT_DESIGN_OPTIONS,
  openSettings: () => emit("open-settings"),
  refreshProjects,
  handleProjectSelect,
  leaveProject,
  handleSelectProjectFolder,
  handleImportProject,
  handleCreateProject,
  handleSidebarGroupToggle,
  handleTreeDragStart,
  handleTreeDrop,
  openEntityIllustration,
  openChapterIllustration,
  syncFromProject,
  toggleModifier,
  applySuggestedPrompt,
  applySuggestedNegativePrompt,
  handleInputImageChange,
  handleMaskChange,
  clearInputAsset,
  handleGenerate,
  handleDryRun,
  handleOpenResultFolder,
  resultLightboxVisible,
  openResultLightbox,
  closeResultLightbox,
  applyHistoryItem,
  startNewPromptPackDraft,
  startDraftFromSelectedPack,
  addPromptPackDraftTemplate,
  removePromptPackDraftTemplate,
  addPromptPackDraftModifier,
  removePromptPackDraftModifier,
  addPromptPackDraftNegativePolicy,
  removePromptPackDraftNegativePolicy,
  addPromptPackDraftCommercialPolicy,
  removePromptPackDraftCommercialPolicy,
  resetPromptPackDraft,
  handleSavePromptPackDraft,
};

</script>

<style scoped>
.workbench-shell {
  display: grid;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}
</style>

