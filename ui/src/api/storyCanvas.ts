export type ProjectOption = {
  key: string;
  root: string;
  title: string;
  genre: string;
  activeChapterId?: string | null;
  chapterCount: number;
  illustrationCount: number;
  source?: "recent" | "library";
};

export type ProjectListPayload = {
  recentProjects: ProjectOption[];
  libraryProjects: ProjectOption[];
  activeRoot: string;
  registryFile: string;
};

export type ChapterRecord = {
  id: string;
  title: string;
  status: string;
  summary: string;
  reviewSummary: string;
  content: string;
  reviewScore: number;
  updatedAt: string;
  issues: string[];
  wordCount: number;
};

export type IllustrationRecord = {
  id?: string;
  type?: string;
  mode?: string;
  useCase?: string;
  targetName?: string;
  chapterId?: string | null;
  entityId?: string | null;
  tempLabel?: string | null;
  promptText?: string;
  promptPackRef?: {
    source?: string;
    packId?: string;
    version?: string;
  };
  templateId?: string;
  modifierRefs?: string[];
  commercialMode?: "personal" | "commercial";
  revisedPrompt?: string;
  generatedAt?: string;
  filePath?: string;
  inputImages?: string[];
  maskPath?: string;
  targetRef?: {
    type: string;
    targetId: string;
  };
  batch?: {
    count?: number;
    variantStrategy?: string;
  };
  promptSnapshot?: {
    packRef?: {
      source?: string;
      packId?: string;
      version?: string;
    };
    templateRef?: string;
    modifierRefs?: string[];
    userExtraPrompt?: string;
    resolvedPrompt?: string;
    textDesign?: {
      mode?: IllustrationTextDesignMode;
      titleText?: string;
      subtitleText?: string;
      bodyText?: string;
      fontStyleHint?: string;
      promptHint?: string;
    };
  };
  policySnapshot?: {
    negativePolicyRef?: string;
    commercialPolicyRef?: string;
    commercialMode?: "personal" | "commercial";
    negativePrompt?: string;
  };
  artifacts?: Array<{
    filePath: string;
    exists: boolean;
    isPrimary: boolean;
  }>;
};

export type EntityRecord = {
  id: string;
  name: string;
  type: string;
  summary?: string;
  aliases?: string[];
  seed?: Record<string, unknown>;
  profile?: Record<string, unknown>;
  currentState?: string | Record<string, unknown>;
  appearanceSummary?: string;
};

export type WorldbookRecord = {
  id: string;
  type: string;
  label: string;
  name: string;
  summary?: string;
  detail?: string;
  sourceKey?: string;
};

export type ReviewPacketRecord = {
  id: string;
  volumeId: string;
  title: string;
  filePath: string;
  exists: boolean;
  updatedAt?: string;
  preview?: string;
};

export type VolumeRecord = {
  id: string;
  title: string;
  theme?: string;
  chapterCount: number;
  chapters: Array<{
    id: string;
    title: string;
    status?: string;
    summary?: string;
  }>;
  reviewPacket?: ReviewPacketRecord;
};

export type PromptPackTemplateDocument = {
  id: string;
  label: string;
  useCase: string;
  mode: string;
  complexity: string;
  promptTemplate: string;
  defaultNegativePolicyRef?: string;
  defaultCommercialPolicyRef?: string;
};

export type PromptPackModifierDocument = {
  id: string;
  group: string;
  label: string;
  promptFragment: string;
  negativeFragment?: string;
  commercialTags?: string[];
};

export type PromptPackNegativePolicyDocument = {
  id: string;
  label: string;
  negativePrompt: string;
};

export type PromptPackCommercialPolicyDocument = {
  id: string;
  label: string;
  mode: string;
  extraPrompt: string;
  restrictions: string[];
};

export type PromptPackDocument = {
  id: string;
  name?: string;
  version: string;
  label: string;
  description: string;
  source?: string;
  sourceFile?: string;
  writable?: boolean;
  supports: Record<string, unknown>;
  templates: PromptPackTemplateDocument[];
  modifierGroups: PromptPackModifierDocument[];
  policies: {
    negativePolicies: PromptPackNegativePolicyDocument[];
    commercialPolicies: PromptPackCommercialPolicyDocument[];
  };
};

export type ProjectSummary = {
  project: {
    key: string;
    root: string;
    title: string;
    genre: string;
    activeChapterId?: string | null;
    positioning: Record<string, unknown>;
    storyContract: Record<string, unknown>;
    commercialPositioning: Record<string, unknown>;
  };
  workflow: {
    currentStage: string;
    workflowStatus: string;
    updatedAt: string;
  };
  illustrationConfig: {
    adapterName: string;
    responseModel: string;
    imageModel: string;
    defaultSize: string;
    quality: string;
    baseUrl: string;
    promptPackName: string;
    promptPackVersion?: string;
    promptPackDir?: string;
    commercialMode?: "personal" | "commercial";
    defaultBatchCount?: string;
    defaultTemplateByUseCase?: Record<string, string>;
    defaultModifierRefs?: string[];
    availablePromptPacks?: Array<{
      id: string;
      name: string;
      version: string;
      label: string;
      description: string;
      source?: string;
      sourceFile?: string;
      supports: Record<string, unknown>;
      templates: Array<{
        id: string;
        label: string;
        useCase: string;
        mode: string;
        complexity: string;
        defaultNegativePolicyRef?: string;
        defaultCommercialPolicyRef?: string;
      }>;
      modifierGroups: Array<{
        id: string;
        group: string;
        label: string;
        negativeFragment?: string;
      }>;
      negativePolicies?: Array<{
        id: string;
        label: string;
        negativePrompt: string;
      }>;
    }>;
  };
  chapters: ChapterRecord[];
  illustrations: IllustrationRecord[];
  entities: EntityRecord[];
  worldbook: {
    entries: WorldbookRecord[];
    stats: Record<string, number>;
  };
  volumes: VolumeRecord[];
  reviewPackets: ReviewPacketRecord[];
  stats: {
    chapterCount: number;
    reviewedChapterCount: number;
    illustrationCount: number;
    entityCount: number;
  };
};

export type IllustrationDryRunRequest = {
  root?: string;
  mode: "text-to-image" | "image-to-image" | "inpaint";
  targetType?: "entity" | "chapter";
  useCase?: string;
  textDesignMode?: IllustrationTextDesignMode;
  titleText?: string;
  subtitleText?: string;
  bodyText?: string;
  fontStyleHint?: string;
  manualTargetName?: string;
  chapterId?: string;
  entityId?: string;
  promptText?: string;
  extraPrompt?: string;
  negativePrompt?: string;
  promptPack?: string;
  templateId?: string;
  modifierRefs?: string[];
  commercialMode?: "personal" | "commercial";
  size?: string;
  quality?: string;
  responseModel?: string;
  baseUrl?: string;
  apiKey?: string;
  outputName?: string;
  batchCount?: number;
  inputImages?: string[];
  maskPath?: string;
};

export type IllustrationDryRunResult = {
  dryRun: true;
  projectRoot?: string;
  scope?: "project" | "workspace";
  payload: Record<string, unknown>;
  promptSnapshot: Record<string, unknown>;
  policySnapshot: Record<string, unknown>;
  providerRequest: Record<string, unknown>;
  outputFile: string;
  outputFiles?: string[];
};

export type IllustrationGenerateRequest = IllustrationDryRunRequest;

export type IllustrationGenerateResult = {
  saved: true;
  scope?: "project" | "workspace";
  illustration: IllustrationRecord;
  summary?: ProjectSummary | null;
};

export type IllustrationTargetType = "entity" | "chapter";
export type IllustrationTextDesignMode = "none" | "designed";

export type IllustrationTemplateSummary = {
  id: string;
  label: string;
  useCase: string;
  mode: string;
  complexity: string;
  defaultNegativePolicyRef?: string;
  defaultCommercialPolicyRef?: string;
};

export const ILLUSTRATION_USE_CASE_LABELS: Record<string, string> = {
  character: "角色",
  "character-sheet": "人物设定图",
  "chapter-scene": "章节场景",
  "cover-concept": "封面概念",
  "cover-poster": "收藏版海报",
  "ensemble-key-visual": "群像主视觉",
  "duel-scene": "角色对决",
  "chase-escape": "追逐逃脱",
  "comic-relief": "轻松搞笑图",
  promo: "宣传图",
  product: "产品图",
  "prop-relic": "道具遗物图",
  "creature-sheet": "生物设定图",
  "manga-panel": "漫画单格",
  "manga-page": "漫画分镜页",
};

const ILLUSTRATION_USE_CASES_BY_TARGET: Record<IllustrationTargetType, string[]> = {
  entity: [
    "character",
    "character-sheet",
    "cover-concept",
    "cover-poster",
    "comic-relief",
    "promo",
    "product",
    "prop-relic",
    "creature-sheet",
    "manga-panel",
  ],
  chapter: [
    "chapter-scene",
    "cover-concept",
    "cover-poster",
    "ensemble-key-visual",
    "duel-scene",
    "chase-escape",
    "comic-relief",
    "promo",
    "product",
    "prop-relic",
    "creature-sheet",
    "manga-panel",
    "manga-page",
  ],
};

export const ILLUSTRATION_KNOWN_USE_CASE_OPTIONS = Object.entries(ILLUSTRATION_USE_CASE_LABELS).map(([value, label]) => ({
  label,
  value,
}));

export const ILLUSTRATION_TEXT_DESIGN_OPTIONS: Array<{ label: string; value: IllustrationTextDesignMode }> = [
  { label: "纯绘图", value: "none" },
  { label: "文字设计", value: "designed" },
];

export function getIllustrationUseCaseLabel(useCase: string): string {
  return ILLUSTRATION_USE_CASE_LABELS[useCase] || useCase || "未命名用途";
}

export function getIllustrationDefaultUseCase(targetType: IllustrationTargetType): string {
  return targetType === "entity" ? "character" : "chapter-scene";
}

export function getCompatibleIllustrationUseCases(targetType: IllustrationTargetType): string[] {
  return [...ILLUSTRATION_USE_CASES_BY_TARGET[targetType]];
}

export function getIllustrationUseCaseOptions(
  templates: IllustrationTemplateSummary[],
  targetType: IllustrationTargetType,
  mode: IllustrationDryRunRequest["mode"]
): Array<{ label: string; value: string }> {
  const allowed = new Set(getCompatibleIllustrationUseCases(targetType));
  const seen = new Set<string>();
  return templates
    .filter((item) => item.mode === mode && allowed.has(item.useCase))
    .filter((item) => {
      if (seen.has(item.useCase)) {
        return false;
      }
      seen.add(item.useCase);
      return true;
    })
    .map((item) => ({
      label: getIllustrationUseCaseLabel(item.useCase),
      value: item.useCase,
    }));
}

export function pickIllustrationUseCase(
  templates: IllustrationTemplateSummary[],
  targetType: IllustrationTargetType,
  mode: IllustrationDryRunRequest["mode"],
  preferredUseCase?: string
): string {
  const options = getIllustrationUseCaseOptions(templates, targetType, mode);
  if (preferredUseCase && options.some((item) => item.value === preferredUseCase)) {
    return preferredUseCase;
  }
  const defaultUseCase = getIllustrationDefaultUseCase(targetType);
  return options.find((item) => item.value === defaultUseCase)?.value || options[0]?.value || defaultUseCase;
}

export function getIllustrationTemplateOptions(
  templates: IllustrationTemplateSummary[],
  mode: IllustrationDryRunRequest["mode"],
  useCase: string
): Array<{ label: string; value: string }> {
  return templates
    .filter((item) => item.useCase === useCase && item.mode === mode)
    .map((item) => ({
      label: item.label,
      value: item.id,
    }));
}

export function pickIllustrationTemplateId(
  templates: IllustrationTemplateSummary[],
  mode: IllustrationDryRunRequest["mode"],
  useCase: string,
  preferredTemplateId?: string
): string {
  const options = getIllustrationTemplateOptions(templates, mode, useCase);
  if (preferredTemplateId && options.some((item) => item.value === preferredTemplateId)) {
    return preferredTemplateId;
  }
  return options[0]?.value || "";
}

export type LocalProviderProfile = {
  id: string;
  label: string;
  baseUrl: string;
  apiKey: string;
  enabled: boolean;
  priority: number;
  hasApiKey: boolean;
  maskedKey: string;
  fingerprint: string;
};

export type WorkbenchSettings = {
  local: {
    apiKeyConfigured: boolean;
    apiKeySource: "local" | "env" | "none";
    configFile: string;
    providers: LocalProviderProfile[];
    fallbackCount: number;
    defaultModel: string;
    defaultSize: string;
    defaultQuality: string;
    defaultCommercialMode: string;
    defaultBatchCount: string;
  };
  workspaceIllustration: {
    root: string;
    title?: string;
    adapterName: string;
    responseModel: string;
    imageModel: string;
    defaultSize: string;
    quality: string;
    baseUrl: string;
    promptPackName: string;
    promptPackDir?: string;
    commercialMode: "personal" | "commercial";
    defaultBatchCount?: string;
    defaultTemplateByUseCase?: Record<string, string>;
    defaultModifierRefs?: string[];
    recentIllustrations?: IllustrationRecord[];
    availablePromptPacks?: Array<{
      id: string;
      name: string;
      version: string;
      label: string;
      description: string;
      source?: string;
      sourceFile?: string;
      supports: Record<string, unknown>;
      templates: Array<{
        id: string;
        label: string;
        useCase: string;
        mode: string;
        complexity: string;
        defaultNegativePolicyRef?: string;
        defaultCommercialPolicyRef?: string;
      }>;
      modifierGroups: Array<{
        id: string;
        group: string;
        label: string;
        negativeFragment?: string;
      }>;
      negativePolicies?: Array<{
        id: string;
        label: string;
        negativePrompt: string;
      }>;
    }>;
  };
  project: null | {
    root: string;
    title: string;
    adapterName: string;
    responseModel: string;
    imageModel: string;
    defaultSize: string;
    quality: string;
    baseUrl: string;
    promptPackName: string;
    promptPackDir?: string;
    commercialMode: "personal" | "commercial";
  };
  capabilities: {
    supportedProviders: string[];
  };
};

export type PromptPackLibraryResponse = {
  scope: "project" | "workspace";
  root: string;
  userPromptPackDir: string;
  packs: PromptPackDocument[];
  systemPacks: PromptPackDocument[];
  userPacks: PromptPackDocument[];
  availablePromptPacks: NonNullable<ProjectSummary["illustrationConfig"]["availablePromptPacks"]>;
  saved?: boolean;
  savedPack?: PromptPackDocument;
  exported?: boolean;
  exportedPack?: PromptPackDocument;
  migration?: {
    root: string;
    packsDir: string;
    dryRun: boolean;
    packCount: number;
    changedCount: number;
    writtenCount: number;
    results: Array<{
      path: string;
      packId: string;
      label: string;
      changed: boolean;
      written: boolean;
      templateCount: number;
      modifierCount: number;
    }>;
  };
};

export type SavePromptPackRequest = {
  root?: string;
  fileName?: string;
  setAsDefault?: boolean;
  pack: PromptPackDocument;
};

export type MigratePromptPackRequest = {
  root?: string;
  dryRun?: boolean;
};

export type ExportPromptPackRequest = {
  root?: string;
  promptPackName?: string;
  fileName?: string;
  setAsDefault?: boolean;
};

export type WorkbenchSettingsUpdate = {
  root?: string;
  providers?: Array<{
    id?: string;
    label: string;
    baseUrl: string;
    enabled: boolean;
    priority: number;
    apiKey?: string;
    clearApiKey?: boolean;
  }>;
  adapterName?: string;
  responseModel?: string;
  imageModel?: string;
  defaultSize?: string;
  quality?: string;
  baseUrl?: string;
  promptPackName?: string;
  commercialMode?: "personal" | "commercial";
  defaultModel?: string;
  defaultQuality?: string;
  defaultCommercialMode?: string;
  defaultBatchCount?: string;
};

export type CreateProjectRequest = {
  title: string;
  genre?: string;
  directoryName?: string;
};

export type CreateProjectResponse = {
  project: ProjectSummary;
};

export type ImportProjectRequest = {
  root: string;
};

export type SelectFolderRequest = {
  initialPath?: string;
};

export type SelectFolderResponse = {
  path: string;
};

const LOCAL_UI_PORT = "43187";
const LOCAL_API_ORIGIN = "http://127.0.0.1:43188";

function resolveApiOrigin(): string {
  const configuredOrigin = String(import.meta.env.VITE_STORY_CANVAS_API_ORIGIN || "").trim();
  if (configuredOrigin) {
    return configuredOrigin.replace(/\/+$/, "");
  }
  if (typeof window !== "undefined" && window.location.hostname === "127.0.0.1" && window.location.port === LOCAL_UI_PORT) {
    return LOCAL_API_ORIGIN;
  }
  return "";
}

const API_ORIGIN = resolveApiOrigin();

function withApiOrigin(path: string): string {
  if (!path.startsWith("/")) {
    return path;
  }
  return API_ORIGIN ? `${API_ORIGIN}${path}` : path;
}

async function fetchJson<T>(input: string, init?: RequestInit): Promise<T> {
  const response = await fetch(withApiOrigin(input), init);
  const rawText = await response.text();
  let payload: (T & { error?: string }) | null = null;

  if (rawText.trim()) {
    try {
      payload = JSON.parse(rawText) as T & { error?: string };
    } catch {
      throw new Error(`接口返回了非 JSON 响应: ${response.status} ${response.statusText}`);
    }
  }

  if (!response.ok) {
    if (payload && "error" in payload && payload.error) {
      throw new Error(String(payload.error));
    }
    throw new Error(`接口请求失败: ${response.status} ${response.statusText}`);
  }

  if (!payload) {
    throw new Error(`接口返回了空响应: ${response.status} ${response.statusText}`);
  }

  return payload;
}

export async function fetchProjects(): Promise<ProjectListPayload> {
  return fetchJson<ProjectListPayload>("/api/projects");
}

export async function createProject(body: CreateProjectRequest): Promise<CreateProjectResponse> {
  return fetchJson<CreateProjectResponse>("/api/projects", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

export async function importProject(body: ImportProjectRequest): Promise<CreateProjectResponse> {
  return fetchJson<CreateProjectResponse>("/api/projects/import", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

export async function selectProjectFolder(body: SelectFolderRequest = {}): Promise<SelectFolderResponse> {
  return fetchJson<SelectFolderResponse>("/api/dialogs/select-folder", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

export async function markProjectRecent(root: string): Promise<void> {
  await fetchJson<{ ok: true; root: string }>("/api/projects/recent", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ root }),
  });
}

export async function setActiveProject(root: string): Promise<void> {
  await fetchJson<{ ok: true; activeRoot: string }>("/api/projects/active", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ root }),
  });
}

export async function fetchProjectSummary(root: string): Promise<ProjectSummary> {
  return fetchJson<ProjectSummary>(`/api/project?root=${encodeURIComponent(root)}`);
}

export async function fetchWorkbenchSettings(root?: string): Promise<WorkbenchSettings> {
  const suffix = root ? `?root=${encodeURIComponent(root)}` : "";
  return fetchJson<WorkbenchSettings>(`/api/settings${suffix}`);
}

export async function saveWorkbenchSettings(body: WorkbenchSettingsUpdate): Promise<WorkbenchSettings> {
  return fetchJson<WorkbenchSettings>("/api/settings", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

export async function fetchPromptPackLibrary(root?: string): Promise<PromptPackLibraryResponse> {
  const suffix = root ? `?root=${encodeURIComponent(root)}` : "";
  return fetchJson<PromptPackLibraryResponse>(`/api/prompt-packs${suffix}`);
}

export async function savePromptPack(body: SavePromptPackRequest): Promise<PromptPackLibraryResponse> {
  return fetchJson<PromptPackLibraryResponse>("/api/prompt-packs", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

export async function migratePromptPacks(body: MigratePromptPackRequest): Promise<PromptPackLibraryResponse> {
  return fetchJson<PromptPackLibraryResponse>("/api/prompt-packs/migrate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

export async function exportPromptPack(body: ExportPromptPackRequest): Promise<PromptPackLibraryResponse> {
  return fetchJson<PromptPackLibraryResponse>("/api/prompt-packs/export", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

export async function dryRunIllustration(body: IllustrationDryRunRequest): Promise<IllustrationDryRunResult> {
  return fetchJson<IllustrationDryRunResult>("/api/illustration/dry-run", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

export async function generateIllustration(body: IllustrationGenerateRequest): Promise<IllustrationGenerateResult> {
  return fetchJson<IllustrationGenerateResult>("/api/illustration/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

export async function dryRunIllustrationForm(body: FormData): Promise<IllustrationDryRunResult> {
  return fetchJson<IllustrationDryRunResult>("/api/illustration/dry-run", {
    method: "POST",
    body,
  });
}

export async function generateIllustrationForm(body: FormData): Promise<IllustrationGenerateResult> {
  return fetchJson<IllustrationGenerateResult>("/api/illustration/generate", {
    method: "POST",
    body,
  });
}

export async function openLocalFolder(body: { root?: string; path: string; scope?: "project" | "workspace" }): Promise<{
  opened: boolean;
  path: string;
  scope: string;
}> {
  return fetchJson("/api/system/open-folder", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

export function buildProjectAssetUrl(root: string, filePath: string): string {
  if (!root || !filePath) {
    return "";
  }
  return withApiOrigin(`/api/assets?root=${encodeURIComponent(root)}&path=${encodeURIComponent(filePath)}`);
}

export function buildWorkbenchAssetUrl(filePath: string): string {
  if (!filePath) {
    return "";
  }
  return withApiOrigin(`/api/workbench-assets?path=${encodeURIComponent(filePath)}`);
}
