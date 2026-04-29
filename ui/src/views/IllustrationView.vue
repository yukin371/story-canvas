<template>
  <div class="illustration-layout">
    <section class="illustration-main">
      <t-card title="插画请求" class="surface-card">
        <p v-if="errorMessage" class="inline-error">{{ errorMessage }}</p>
        <t-form layout="vertical">
          <t-form-item label="目标类型">
            <t-radio-group v-model="targetType">
              <t-radio-button value="chapter">章节</t-radio-button>
              <t-radio-button value="entity">角色</t-radio-button>
            </t-radio-group>
          </t-form-item>

          <t-form-item :label="targetType === 'chapter' ? '章节' : '角色'">
            <t-select v-model="targetId" :options="targetOptions" />
          </t-form-item>

          <t-form-item label="目标">
            <t-radio-group v-model="mode">
              <t-radio-button value="text-to-image">文生图</t-radio-button>
              <t-radio-button value="image-to-image">图生图</t-radio-button>
              <t-radio-button value="inpaint">重绘</t-radio-button>
            </t-radio-group>
          </t-form-item>

          <div class="form-grid">
            <t-form-item label="Prompt Pack">
              <t-select v-model="promptPack" :options="promptPackOptions" />
            </t-form-item>
            <t-form-item label="用途">
              <t-select v-model="useCase" :options="useCaseOptions" />
            </t-form-item>
            <t-form-item label="模板">
              <t-select v-model="templateId" :options="templateOptions" />
            </t-form-item>
            <t-form-item label="商业模式">
              <t-select v-model="commercialMode" :options="commercialModeOptions" />
            </t-form-item>
          </div>

          <t-form-item label="额外提示词">
            <t-textarea
              v-model="prompt"
              :autosize="{ minRows: 6, maxRows: 9 }"
              placeholder="在模板基础上补充本次想强调的场景、角色、镜头或氛围。"
            />
          </t-form-item>

          <div class="form-grid">
            <t-form-item label="文字设计">
              <t-select v-model="textDesignMode" :options="ILLUSTRATION_TEXT_DESIGN_OPTIONS" />
            </t-form-item>
            <t-form-item v-if="textDesignMode === 'designed'" label="标题">
              <t-input v-model="titleText" placeholder="可留空" />
            </t-form-item>
            <t-form-item v-if="textDesignMode === 'designed'" label="副标题">
              <t-input v-model="subtitleText" placeholder="可留空" />
            </t-form-item>
            <t-form-item v-if="textDesignMode === 'designed'" label="字体气质">
              <t-input v-model="fontStyleHint" placeholder="例如：墨明风题字、冷峻无衬线" />
            </t-form-item>
          </div>

          <t-form-item v-if="textDesignMode === 'designed'" label="简介 / 导语">
            <t-textarea
              v-model="bodyText"
              :autosize="{ minRows: 3, maxRows: 5 }"
              placeholder="可留空；留空时只保留版式空间，不强行生成具体文字。"
            />
          </t-form-item>

          <div class="form-grid">
            <t-form-item label="Response Model">
              <t-select v-model="responseModel" :options="responseModelOptions" />
            </t-form-item>
            <t-form-item label="Image Model">
              <t-select v-model="imageModel" :options="imageModelOptions" disabled />
            </t-form-item>
            <t-form-item label="尺寸">
              <t-select v-model="size" :options="sizeOptions" />
            </t-form-item>
            <t-form-item label="质量">
              <t-select v-model="quality" :options="qualityOptions" />
            </t-form-item>
          </div>

          <div class="form-grid" v-if="mode === 'image-to-image' || mode === 'inpaint'">
            <t-form-item label="源图路径">
              <t-input v-model="inputImagePath" placeholder="E:\\path\\to\\reference.png" />
            </t-form-item>
            <t-form-item label="Mask 路径">
              <t-input v-model="maskPath" placeholder="可选，E:\\path\\to\\mask.png" />
            </t-form-item>
          </div>

          <div class="detail-actions">
            <t-button theme="primary" :loading="submitting" @click="handleDryRun">Dry Run</t-button>
            <t-button theme="default" :loading="submitting" @click="handleGenerate">Generate</t-button>
            <t-button variant="outline" @click="syncFromProject">同步项目默认值</t-button>
          </div>
        </t-form>
      </t-card>
    </section>

    <section class="illustration-side">
      <t-card title="项目默认值" class="surface-card">
        <div class="config-grid">
          <div v-for="item in configFacts" :key="item.label" class="fact-item">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
      </t-card>

      <t-card :title="resultCardTitle" class="surface-card preview-card">
        <div class="preview-stage" v-if="resultText">
          <div class="preview-copy">
            <strong>{{ resultOutputFile }}</strong>
            <p>{{ resultHint }}</p>
          </div>
          <t-textarea :model-value="resultText" :autosize="{ minRows: 12, maxRows: 18 }" readonly />
        </div>
        <p v-else class="detail-copy">先选择项目目标，再执行 dry-run 或 generate。</p>
      </t-card>

      <t-card title="任务历史" class="surface-card">
        <t-table
          row-key="id"
          :columns="columns"
          :data="illustrationHistory"
          size="small"
          table-layout="auto"
        >
          <template #actions="{ row }">
            <t-button theme="primary" variant="text" size="small" @click="applyHistoryItem(row.raw)">复用</t-button>
          </template>
        </t-table>
      </t-card>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

import {
  dryRunIllustration,
  generateIllustration,
  getIllustrationDefaultUseCase,
  getIllustrationTemplateOptions,
  getIllustrationUseCaseOptions,
  ILLUSTRATION_TEXT_DESIGN_OPTIONS,
  pickIllustrationTemplateId,
  pickIllustrationUseCase,
  type IllustrationTargetType,
  type IllustrationTextDesignMode,
  type IllustrationTemplateSummary,
  type IllustrationDryRunResult,
  type IllustrationGenerateResult,
  type IllustrationRecord,
} from "@/api/storyCanvas";
import { useWorkspace } from "@/composables/useWorkspace";
import { TCard } from "@/tdesign/display";
import {
  TButton,
  TForm,
  TFormItem,
  TInput,
  TRadioButton,
  TRadioGroup,
  TSelect,
  TTextarea,
} from "@/tdesign/forms";
import { TTable, type PrimaryTableCol } from "@/tdesign/table";

type ConfigFact = {
  label: string;
  value: string;
};

type IllustrationHistoryRow = {
  id: string;
  title: string;
  target: string;
  mode: string;
  status: string;
  updatedAt: string;
  raw: IllustrationRecord;
};

const mode = ref<"text-to-image" | "image-to-image" | "inpaint">("text-to-image");
const targetType = ref<"chapter" | "entity">("chapter");
const targetId = ref("");
const useCase = ref(getIllustrationDefaultUseCase(targetType.value));
const textDesignMode = ref<IllustrationTextDesignMode>("none");
const titleText = ref("");
const subtitleText = ref("");
const bodyText = ref("");
const fontStyleHint = ref("");
const prompt = ref(
  "都市夜港，潮湿柏油路反射橙色路灯，主角林舟站在半开的仓库门前，画面压抑但克制。"
);
const promptPack = ref("default");
const templateId = ref("");
const commercialMode = ref<"personal" | "commercial">("personal");
const responseModel = ref("gpt-5.4");
const imageModel = ref("gpt-image-2");
const size = ref("1024x1024");
const quality = ref("high");
const inputImagePath = ref("");
const maskPath = ref("");
const dryRunResult = ref<IllustrationDryRunResult | null>(null);
const generateResult = ref<IllustrationGenerateResult | null>(null);
const submitting = ref(false);
const errorMessage = ref("");
const syncedProjectRoot = ref("");

const workspace = useWorkspace();
const summary = computed(() => workspace.summary.value);

const responseModelOptions = [
  { label: "gpt-5.4", value: "gpt-5.4" },
  { label: "gpt-5.5", value: "gpt-5.5" },
];

const imageModelOptions = [{ label: "gpt-image-2", value: "gpt-image-2" }];
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

const targetOptions = computed(() => {
  if (targetType.value === "entity") {
    return (summary.value?.entities || []).map((item) => ({
      label: `${item.name} · ${item.type || "entity"}`,
      value: item.id,
    }));
  }
  return (summary.value?.chapters || []).map((item) => ({
    label: `${item.title} · ${item.id}`,
    value: item.id,
  }));
});

const illustrationHistory = computed<IllustrationHistoryRow[]>(() =>
  (summary.value?.illustrations || []).map((item) => ({
    id: item.id || `${item.generatedAt || "history"}-${item.targetRef?.targetId || item.chapterId || item.entityId || "item"}`,
    title: item.revisedPrompt || item.promptText || item.targetRef?.targetId || "illustration",
    mode: item.mode || "text-to-image",
    target: item.targetRef?.targetId || item.chapterId || item.entityId || "-",
    status: item.artifacts?.some((asset) => asset.exists) ? "已落盘" : "待确认",
    updatedAt: item.generatedAt || "-",
    raw: item,
  }))
);

const availablePromptPacks = computed(() => summary.value?.illustrationConfig.availablePromptPacks || []);
const selectedPromptPack = computed(() => {
  return availablePromptPacks.value.find((item) => item.name === promptPack.value) || availablePromptPacks.value[0];
});
const packTemplates = computed<IllustrationTemplateSummary[]>(() => (selectedPromptPack.value?.templates || []) as IllustrationTemplateSummary[]);
const promptPackOptions = computed(() =>
  availablePromptPacks.value.map((item) => ({
    label: `${item.label} · ${item.version}`,
    value: item.name,
  }))
);
const useCaseOptions = computed(() => getIllustrationUseCaseOptions(packTemplates.value, targetType.value, mode.value));
const templateOptions = computed(() => getIllustrationTemplateOptions(packTemplates.value, mode.value, useCase.value));

const configFacts = computed<ConfigFact[]>(() => {
  const config = summary.value?.illustrationConfig;
  return [
    { label: "Adapter", value: config?.adapterName || "-" },
    { label: "Response", value: config?.responseModel || "-" },
    { label: "Image", value: config?.imageModel || "-" },
    { label: "默认尺寸", value: config?.defaultSize || "-" },
    { label: "质量", value: config?.quality || "-" },
    { label: "Prompt Pack", value: config?.promptPackName || "-" },
    { label: "商用模式", value: config?.commercialMode || "-" },
  ];
});

const resultCardTitle = computed(() => {
  if (generateResult.value) {
    return "生成结果";
  }
  if (dryRunResult.value) {
    return "Dry Run 结果";
  }
  return "最近结果";
});

const resultOutputFile = computed(() => generateResult.value?.illustration.filePath || dryRunResult.value?.outputFile || "-");
const resultHint = computed(() => {
  if (generateResult.value) {
    return "已写入 illustrations.yaml 和资产目录。";
  }
  if (dryRunResult.value) {
    return "展示 provider 请求和预期落盘路径。";
  }
  return "";
});
const resultText = computed(() => {
  if (generateResult.value) {
    return JSON.stringify(generateResult.value.illustration, null, 2);
  }
  if (dryRunResult.value) {
    return JSON.stringify(dryRunResult.value, null, 2);
  }
  return "";
});

const columns: PrimaryTableCol[] = [
  { colKey: "title", title: "任务" },
  { colKey: "target", title: "目标" },
  { colKey: "mode", title: "模式" },
  { colKey: "status", title: "状态" },
  { colKey: "updatedAt", title: "时间" },
  { colKey: "actions", title: "操作", width: 88 },
];

function resetResultPanels() {
  dryRunResult.value = null;
  generateResult.value = null;
}

function syncFromProject() {
  const projectSummary = summary.value;
  if (!projectSummary) {
    return;
  }
  syncedProjectRoot.value = projectSummary.project.root;
  const config = projectSummary.illustrationConfig;
  responseModel.value = config.responseModel || "gpt-5.4";
  imageModel.value = config.imageModel || "gpt-image-2";
  size.value = config.defaultSize || "1024x1024";
  quality.value = config.quality || "auto";
  promptPack.value = config.promptPackName || "default";
  commercialMode.value = config.commercialMode || "personal";
  mode.value = "text-to-image";
  textDesignMode.value = "none";
  titleText.value = "";
  subtitleText.value = "";
  bodyText.value = "";
  fontStyleHint.value = "";
  inputImagePath.value = "";
  maskPath.value = "";
  resetResultPanels();
  errorMessage.value = "";

  if (projectSummary.project.activeChapterId) {
    targetType.value = "chapter";
    targetId.value = projectSummary.project.activeChapterId;
  } else if (projectSummary.chapters.length > 0) {
    targetType.value = "chapter";
    targetId.value = projectSummary.chapters[0].id;
  } else if (projectSummary.entities.length > 0) {
    targetType.value = "entity";
    targetId.value = projectSummary.entities[0].id;
  }
  useCase.value = pickIllustrationUseCase(
    packTemplates.value,
    targetType.value,
    mode.value,
    getIllustrationDefaultUseCase(targetType.value)
  );
  templateId.value = pickIllustrationTemplateId(
    packTemplates.value,
    mode.value,
    useCase.value,
    config.defaultTemplateByUseCase?.[useCase.value] || ""
  );
}

function buildIllustrationRequest() {
  if (!summary.value?.project.root) {
    throw new Error("请先选择项目。");
  }
  if (!targetId.value) {
    throw new Error("请选择目标章节或角色。");
  }
  if ((mode.value === "image-to-image" || mode.value === "inpaint") && !inputImagePath.value.trim()) {
    throw new Error("图生图 / 重绘模式需要提供源图路径。");
  }
  if (mode.value === "inpaint" && !maskPath.value.trim()) {
    throw new Error("重绘模式需要提供 mask 路径。");
  }
  return {
    root: summary.value.project.root,
    mode: mode.value,
    targetType: targetType.value,
    useCase: useCase.value || undefined,
    textDesignMode: textDesignMode.value,
    titleText: textDesignMode.value === "designed" ? titleText.value.trim() || undefined : undefined,
    subtitleText: textDesignMode.value === "designed" ? subtitleText.value.trim() || undefined : undefined,
    bodyText: textDesignMode.value === "designed" ? bodyText.value.trim() || undefined : undefined,
    fontStyleHint: textDesignMode.value === "designed" ? fontStyleHint.value.trim() || undefined : undefined,
    chapterId: targetType.value === "chapter" ? targetId.value : undefined,
    entityId: targetType.value === "entity" ? targetId.value : undefined,
    extraPrompt: prompt.value.trim() || undefined,
    promptPack: promptPack.value || undefined,
    templateId: templateId.value || undefined,
    commercialMode: commercialMode.value,
    size: size.value,
    quality: quality.value,
    responseModel: responseModel.value,
    inputImages:
      mode.value === "image-to-image" || mode.value === "inpaint"
        ? [inputImagePath.value.trim()]
        : [],
    maskPath: mode.value === "inpaint" ? maskPath.value.trim() || undefined : undefined,
  };
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

function applyHistoryItem(item: IllustrationRecord) {
  const nextTargetType = item.targetRef?.type === "entity" || item.entityId ? "entity" : "chapter";
  const nextPromptPack = resolveHistoryPromptPack(item) || promptPack.value;
  targetType.value = nextTargetType;
  targetId.value = item.targetRef?.targetId || item.chapterId || item.entityId || "";
  mode.value = item.mode === "image-to-image" || item.mode === "inpaint" ? item.mode : "text-to-image";
  promptPack.value = nextPromptPack;
  useCase.value = resolveHistoryUseCase(item, nextPromptPack, nextTargetType);
  templateId.value = item.templateId || item.promptSnapshot?.templateRef || "";
  commercialMode.value = item.commercialMode || item.policySnapshot?.commercialMode || "personal";
  textDesignMode.value = item.promptSnapshot?.textDesign?.mode === "designed" ? "designed" : "none";
  titleText.value = item.promptSnapshot?.textDesign?.titleText || "";
  subtitleText.value = item.promptSnapshot?.textDesign?.subtitleText || "";
  bodyText.value = item.promptSnapshot?.textDesign?.bodyText || "";
  fontStyleHint.value = item.promptSnapshot?.textDesign?.fontStyleHint || "";
  prompt.value = item.promptSnapshot?.userExtraPrompt || item.promptText || "";
  inputImagePath.value = item.inputImages?.[0] || "";
  maskPath.value = item.maskPath || "";
  errorMessage.value = "";
  resetResultPanels();
}

async function handleDryRun() {
  errorMessage.value = "";
  submitting.value = true;
  try {
    const request = buildIllustrationRequest();
    generateResult.value = null;
    dryRunResult.value = await dryRunIllustration(request);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    submitting.value = false;
  }
}

async function handleGenerate() {
  errorMessage.value = "";
  submitting.value = true;
  try {
    const request = buildIllustrationRequest();
    dryRunResult.value = null;
    generateResult.value = await generateIllustration(request);
    await workspace.refreshSummary();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    submitting.value = false;
  }
}

watch(
  () => [targetType.value, targetOptions.value] as const,
  ([kind, options]) => {
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
  },
  { immediate: true, deep: true }
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
    if (!root || root === syncedProjectRoot.value) {
      return;
    }
    syncedProjectRoot.value = root;
    syncFromProject();
  },
  { immediate: true }
);
</script>
