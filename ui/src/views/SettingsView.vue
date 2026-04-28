<template>
  <div class="settings-shell">
    <WorkbenchPaneCard title="本地凭证" class="settings-pane">
      <div class="settings-pane-body">
        <p v-if="settingsError" class="inline-error">{{ settingsError }}</p>

        <p class="detail-copy provider-fallback-hint">
          多个启用的提供商按顺位依次尝试，失败后自动切换下一个。
        </p>

        <div class="provider-stack">
          <div
            v-for="item in providerDrafts"
            :key="item.id"
            class="provider-row"
            :class="{
              'is-dragging': draggingProviderId === item.id,
              'is-drop-target': dropTargetId === item.id,
            }"
            @dragover.prevent="handleProviderDragOver(item.id, $event)"
            @dragleave="handleProviderDragLeave"
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
                  <strong>#{{ item.priority }} · {{ item.label || "未命名提供商" }}</strong>
                  <span>{{ item.enabled ? "启用" : "停用" }}</span>
                </div>
              </div>
              <div class="provider-row-actions">
                <t-button variant="text" size="small" @click="moveProvider(item.id, -1)">上移</t-button>
                <t-button variant="text" size="small" @click="moveProvider(item.id, 1)">下移</t-button>
                <t-button variant="text" size="small" theme="danger" @click="clearProviderKey(item.id)">
                  移除 Key
                </t-button>
              </div>
            </div>

            <t-form layout="inline" class="provider-form">
              <div class="form-grid-provider-row">
                <t-form-item label="名称">
                  <t-input v-model="item.label" placeholder="OpenAI 官方 / Gateway A" />
                </t-form-item>
                <t-form-item label="Base URL">
                  <t-input v-model="item.baseUrl" placeholder="官方可留空" />
                </t-form-item>
                <t-form-item label="Key">
                  <t-input
                    :model-value="item.apiKey"
                    type="password"
                    placeholder="sk-..."
                    @update:model-value="handleProviderKeyInput(item.id, String($event ?? ''))"
                  />
                </t-form-item>
                <t-form-item class="provider-enable-field">
                  <t-switch v-model="item.enabled" />
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

        <p v-if="settings?.local?.apiKeySource === 'env'" class="detail-copy">
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
const dropTargetId = ref("");

const providerDrafts = ref<ProviderDraft[]>([]);
const providerSeed = ref(1);

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

function handleProviderDragOver(targetId: string, event: DragEvent) {
  if (!draggingProviderId.value || draggingProviderId.value === targetId) {
    return;
  }
  dropTargetId.value = targetId;
}

function handleProviderDragLeave() {
  dropTargetId.value = "";
}

function handleProviderDrop(targetId: string) {
  if (!draggingProviderId.value || draggingProviderId.value === targetId) {
    draggingProviderId.value = "";
    dropTargetId.value = "";
    return;
  }
  const next = [...providerDrafts.value];
  const fromIndex = next.findIndex((item) => item.id === draggingProviderId.value);
  const toIndex = next.findIndex((item) => item.id === targetId);
  if (fromIndex < 0 || toIndex < 0) {
    draggingProviderId.value = "";
    dropTargetId.value = "";
    return;
  }
  const [moved] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moved);
  providerDrafts.value = next;
  normalizeProviderPriority();
  draggingProviderId.value = "";
  dropTargetId.value = "";
}

function handleProviderDragEnd() {
  draggingProviderId.value = "";
  dropTargetId.value = "";
}

function moveProvider(id: string, direction: -1 | 1) {
  const currentIndex = providerDrafts.value.findIndex((item) => item.id === id);
  const nextIndex = currentIndex + direction;
  if (currentIndex < 0 || nextIndex < 0 || nextIndex >= providerDrafts.value.length) {
    return;
  }
  const next = [...providerDrafts.value];
  const [moved] = next.splice(currentIndex, 1);
  next.splice(nextIndex, 0, moved);
  providerDrafts.value = next;
  normalizeProviderPriority();
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
  gap: 6px;
}

.provider-row {
  display: grid;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid var(--line);
  background: var(--surface-soft);
  border-radius: 4px;
  transition: border-color 160ms ease, box-shadow 160ms ease;
}

.provider-row.is-dragging {
  opacity: 0.5;
  transform: scale(0.98);
}

.provider-row.is-drop-target {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent);
}

.provider-row-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.provider-row-head-main {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.provider-row-title {
  display: flex;
  align-items: baseline;
  gap: 8px;
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
  gap: 2px;
  flex-wrap: wrap;
}

.provider-form {
  overflow: visible;
  padding-right: 0;
}

.form-grid-provider-row {
  display: grid;
  grid-template-columns: minmax(100px, 1fr) minmax(100px, 1.3fr) minmax(100px, 1fr) 48px 72px;
  gap: 8px;
  align-items: end;
}

.provider-enable-field :deep(.t-form__label) {
  display: none;
}

.provider-enable-field {
  display: flex;
  align-items: flex-end;
  justify-content: center;
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
  .settings-shell {
    grid-template-columns: 1fr;
  }

  .settings-pane-body {
    overflow: visible;
  }

  .form-grid-provider-row {
    grid-template-columns: minmax(80px, 1fr) minmax(80px, 1.3fr) minmax(80px, 1fr) 48px 72px;
  }
}

@media (max-width: 768px) {
  .form-grid-provider-row {
    grid-template-columns: 1fr 1fr;
  }

  .provider-enable-field {
    justify-content: flex-start;
  }
}
</style>
