<template>
  <div class="settings-shell">
    <WorkbenchPaneCard title="本地凭证" class="settings-pane">
      <div class="settings-pane-body">
        <p v-if="settingsError" class="inline-error">{{ settingsError }}</p>

        <div class="settings-meta-grid">
          <div class="fact-item">
            <span>状态</span>
            <strong>{{ credentialStatusLabel }}</strong>
          </div>
          <div class="fact-item">
            <span>来源</span>
            <strong>{{ credentialSourceLabel }}</strong>
          </div>
          <div class="fact-item">
            <span>回退</span>
            <strong>{{ fallbackStatusLabel }}</strong>
          </div>
        </div>

        <div class="provider-stack">
          <div
            v-for="item in providerDrafts"
            :key="item.id"
            class="provider-row"
            :class="{ 'is-dragging': draggingProviderId === item.id }"
            @dragover.prevent
            @drop="handleProviderDrop(item.id)"
          >
            <div class="provider-row-head">
              <div class="provider-row-head-main">
                <button
                  class="provider-drag-handle"
                  type="button"
                  draggable="true"
                  aria-label="拖拽调整优先级"
                  @dragstart="handleProviderDragStart(item.id)"
                  @dragend="handleProviderDragEnd"
                >
                  <span v-for="dot in 9" :key="dot" class="provider-drag-dot"></span>
                </button>
                <div class="provider-row-title">
                  <strong>{{ item.label || "未命名提供商" }}</strong>
                  <span>顺位 {{ item.priority }} · {{ item.enabled ? "启用" : "停用" }}</span>
                </div>
              </div>
              <div class="provider-row-actions">
                <t-button variant="text" size="small" theme="danger" @click="clearProviderKey(item.id)">
                  移除 Key
                </t-button>
              </div>
            </div>

            <t-form layout="vertical" class="compact-form provider-form">
              <div class="compact-form-grid form-grid-provider-top">
                <t-form-item label="名称">
                  <t-input v-model="item.label" placeholder="OpenAI 官方 / Gateway A" />
                </t-form-item>
                <t-form-item label="启用">
                  <t-switch v-model="item.enabled" />
                </t-form-item>
              </div>

              <div class="compact-form-grid form-grid-provider-cred">
                <t-form-item label="Base URL">
                  <t-input v-model="item.baseUrl" placeholder="官方 OpenAI 可留空，兼容服务填写完整 Base URL" />
                </t-form-item>
                <t-form-item label="Key">
                  <t-input
                    :model-value="item.apiKey"
                    type="password"
                    placeholder="sk-..."
                    @update:model-value="handleProviderKeyInput(item.id, String($event ?? ''))"
                  />
                </t-form-item>
                <div class="provider-inline-save">
                  <t-button theme="primary" :loading="savingSettings" @click="handleSaveProviders">
                    保存
                  </t-button>
                </div>
              </div>
            </t-form>
          </div>
        </div>

        <div class="detail-actions">
          <t-button variant="outline" @click="addProvider">新增提供商</t-button>
          <t-button variant="outline" :loading="loadingSettings" @click="reloadSettings">刷新</t-button>
        </div>

        <div class="settings-path-card">
          <span>本地配置文件</span>
          <strong>{{ configFile }}</strong>
        </div>

        <p v-if="credentialSourceLabel === '环境变量'" class="detail-copy">
          当前仍可回退到环境变量 key；但优先级排序与自动切换只对本地工作台配置生效。
        </p>

        <p class="detail-copy">
          这里编辑的是工作台私有凭证，不写入项目协议。清空某条 key 后保存，即会从本地配置里移除该密钥。
        </p>
      </div>
    </WorkbenchPaneCard>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type { LocalProviderProfile } from "@/api/storyCanvas";
import WorkbenchPaneCard from "@/components/WorkbenchPaneCard.vue";
import { useWorkspace } from "@/composables/useWorkspace";

type ProviderDraft = {
  id: string;
  label: string;
  baseUrl: string;
  enabled: boolean;
  priority: number;
  apiKey: string;
  clearApiKey: boolean;
};

const workspace = useWorkspace();

const settings = computed(() => workspace.settings.value);
const selectedRoot = computed(() => workspace.selectedRoot.value);
const settingsError = computed(() => workspace.settingsError.value);
const loadingSettings = computed(() => workspace.loadingSettings.value);
const savingSettings = computed(() => workspace.savingSettings.value);
const draggingProviderId = ref("");

const providerDrafts = ref<ProviderDraft[]>([]);
const providerSeed = ref(1);

const credentialStatusLabel = computed(() => {
  const localReadyCount =
    settings.value?.local.providers.filter((item) => item.enabled && item.hasApiKey).length || 0;
  if (localReadyCount > 0) {
    return `${localReadyCount} 条本地可用`;
  }
  if (settings.value?.local.apiKeySource === "env") {
    return "环境变量可用";
  }
  return "未配置";
});

const credentialSourceLabel = computed(() => {
  switch (settings.value?.local.apiKeySource) {
    case "local":
      return "本地工作台";
    case "env":
      return "环境变量";
    default:
      return "未配置";
  }
});

const fallbackStatusLabel = computed(() => {
  const count = settings.value?.local.fallbackCount || 0;
  return count > 0 ? `可切换 ${count} 条后备` : "无";
});

const configFile = computed(() => settings.value?.local.configFile || "-");

function buildProviderDraft(profile?: LocalProviderProfile): ProviderDraft {
  if (profile) {
    return {
      id: profile.id,
      label: profile.label,
      baseUrl: profile.baseUrl,
      enabled: profile.enabled,
      priority: profile.priority,
      apiKey: profile.apiKey,
      clearApiKey: false,
    };
  }
  const nextIndex = providerSeed.value;
  providerSeed.value += 1;
  return {
    id: `provider-${nextIndex}`,
    label: `Provider ${nextIndex}`,
    baseUrl: "",
    enabled: true,
    priority: providerDrafts.value.length + 1,
    apiKey: "",
    clearApiKey: false,
  };
}

function addProvider() {
  providerDrafts.value = [...providerDrafts.value, buildProviderDraft()];
  normalizeProviderPriority();
}

function handleProviderKeyInput(id: string, value: string) {
  providerDrafts.value = providerDrafts.value.map((item) =>
    item.id === id
      ? {
          ...item,
          apiKey: value,
          clearApiKey: false,
        }
      : item
  );
}

function clearProviderKey(id: string) {
  providerDrafts.value = providerDrafts.value.map((item) =>
    item.id === id
      ? {
          ...item,
          apiKey: "",
          clearApiKey: true,
        }
      : item
  );
}

function normalizeProviderPriority() {
  providerDrafts.value = providerDrafts.value.map((item, index) => ({
    ...item,
    priority: index + 1,
  }));
}

function handleProviderDragStart(id: string) {
  draggingProviderId.value = id;
}

function handleProviderDrop(targetId: string) {
  if (!draggingProviderId.value || draggingProviderId.value === targetId) {
    draggingProviderId.value = "";
    return;
  }
  const next = [...providerDrafts.value];
  const fromIndex = next.findIndex((item) => item.id === draggingProviderId.value);
  const toIndex = next.findIndex((item) => item.id === targetId);
  if (fromIndex < 0 || toIndex < 0) {
    draggingProviderId.value = "";
    return;
  }
  const [moved] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moved);
  providerDrafts.value = next;
  normalizeProviderPriority();
  draggingProviderId.value = "";
}

function handleProviderDragEnd() {
  draggingProviderId.value = "";
}

async function reloadSettings() {
  await workspace.refreshSettings(selectedRoot.value);
}

async function handleSaveProviders() {
  normalizeProviderPriority();
  await workspace.persistSettings({
    root: selectedRoot.value || undefined,
    providers: providerDrafts.value.map((item) => ({
      id: item.id,
      label: item.label.trim() || "未命名提供商",
      baseUrl: item.baseUrl.trim(),
      enabled: item.enabled,
      priority: item.priority,
      apiKey: item.apiKey.trim(),
      clearApiKey: item.clearApiKey,
    })),
  });
}

function syncFromSettings() {
  const profiles = settings.value?.local.providers || [];
  providerSeed.value = profiles.length + 1;
  providerDrafts.value = profiles.length > 0 ? profiles.map((item) => buildProviderDraft(item)) : [buildProviderDraft()];
}

watch(
  settings,
  () => {
    syncFromSettings();
  },
  { immediate: true }
);
</script>

<style scoped>
.settings-shell {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 0;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.settings-pane {
  padding: 0;
}

.settings-pane-body {
  min-height: 0;
  overflow: auto;
  padding: 8px 12px 12px;
}

.settings-meta-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.provider-stack {
  display: grid;
  gap: 10px;
}

.provider-row {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--line);
  background: var(--surface-soft);
}

.provider-row.is-dragging {
  opacity: 0.56;
}

.provider-row-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.provider-row-head-main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.provider-row-title {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.provider-row-title span {
  color: var(--muted);
  font-size: 12px;
}

.provider-drag-handle {
  display: grid;
  grid-template-columns: repeat(3, 4px);
  gap: 3px;
  width: 24px;
  min-width: 24px;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: grab;
}

.provider-drag-handle:active {
  cursor: grabbing;
}

.provider-drag-dot {
  width: 4px;
  height: 4px;
  border-radius: 999px;
  background: #9aa3b2;
}

.provider-row-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.provider-form {
  overflow: visible;
  padding-right: 0;
}

.form-grid-provider-top {
  grid-template-columns: minmax(260px, 1fr) 88px;
}

.form-grid-provider-cred {
  grid-template-columns: minmax(0, 1fr) minmax(320px, 1fr) 100px;
  align-items: end;
}

.provider-inline-save {
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
  min-height: 100%;
}

.provider-inline-save :deep(.t-button) {
  width: 100%;
}

.settings-path-card {
  display: grid;
  gap: 6px;
  padding: 10px 12px;
  border: 1px solid var(--line);
  background: var(--surface-soft);
}

.settings-path-card span {
  color: var(--muted);
}

.settings-path-card strong {
  line-height: 1.45;
  word-break: break-word;
}

@media (max-width: 1180px) {
  .settings-shell,
  .settings-meta-grid,
  .form-grid-provider-top,
  .form-grid-provider-cred {
    grid-template-columns: 1fr;
  }

  .settings-pane-body {
    overflow: visible;
  }
}
</style>
