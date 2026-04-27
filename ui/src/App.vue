<template>
  <t-layout class="app-shell">
    <t-aside class="activitybar">
      <div class="activitybar-top">
        <button
          class="activitybar-button brand-button"
          type="button"
          aria-label="Story Canvas"
          title="Story Canvas"
        >
          <span>SC</span>
        </button>
      </div>

      <div class="activitybar-nav">
        <button
          class="activitybar-button"
          :class="{ 'is-active': activePage === 'review' }"
          type="button"
          aria-label="审查工作区"
          title="审查"
          @click="setActivePage('review')"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 5.5A1.5 1.5 0 0 1 5.5 4h13A1.5 1.5 0 0 1 20 5.5v13a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 18.5Zm3 2v3h10v-3Zm0 5v4h4v-4Zm6 0v4h4v-4Z" />
          </svg>
        </button>
        <button
          class="activitybar-button"
          :class="{ 'is-active': activePage === 'illustration' }"
          type="button"
          aria-label="插画工作区"
          title="插画"
          @click="setActivePage('illustration')"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path
              d="M6 4h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Zm0 2v8.1l2.8-2.8a1 1 0 0 1 1.4 0l2 2 3.8-3.8a1 1 0 0 1 1.4 0L18 10.1V6Zm0 10v2h12v-5.07l-3.5-3.5-3.8 3.8a1 1 0 0 1-1.4 0l-2-2L6 16Zm3-7.75a1.25 1.25 0 1 0 0-2.5 1.25 1.25 0 0 0 0 2.5Z"
            />
          </svg>
        </button>
      </div>

      <div class="activitybar-footer">
        <button
          class="activitybar-button"
          :class="{ 'is-active': activePage === 'settings' }"
          type="button"
          aria-label="设置"
          title="设置"
          @click="setActivePage('settings')"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path
              d="M19.14 12.94a7.43 7.43 0 0 0 .05-.94 7.43 7.43 0 0 0-.05-.94l2.03-1.58a.48.48 0 0 0 .11-.62l-1.92-3.32a.49.49 0 0 0-.59-.22l-2.39.96a7.18 7.18 0 0 0-1.63-.94l-.36-2.54a.48.48 0 0 0-.48-.4h-3.84a.48.48 0 0 0-.48.4l-.36 2.54c-.58.22-1.12.53-1.63.94l-2.39-.96a.49.49 0 0 0-.59.22L2.72 8.86a.48.48 0 0 0 .11.62l2.03 1.58a7.43 7.43 0 0 0-.05.94 7.43 7.43 0 0 0 .05.94l-2.03 1.58a.48.48 0 0 0-.11.62l1.92 3.32a.49.49 0 0 0 .59.22l2.39-.96c.51.41 1.05.72 1.63.94l.36 2.54a.48.48 0 0 0 .48.4h3.84a.48.48 0 0 0 .48-.4l.36-2.54c.58-.22 1.12-.53 1.63-.94l2.39.96a.49.49 0 0 0 .59-.22l1.92-3.32a.48.48 0 0 0-.11-.62l-2.03-1.58ZM12 15.25A3.25 3.25 0 1 1 12 8.75a3.25 3.25 0 0 1 0 6.5Z"
            />
          </svg>
        </button>
      </div>
    </t-aside>

    <t-layout class="main-layout">
      <t-content class="page-content">
        <SettingsView v-if="activePage === 'settings'" />
        <WorkbenchView
          v-else
          :workspace-mode="workbenchMode"
          @update:workspace-mode="setActivePage"
          @open-settings="openSettings"
          @workspace-status="setWorkbenchStatus"
        />
      </t-content>
      <footer class="statusbar">
        <div class="statusbar-item">
          <span>项目</span>
          <strong>{{ currentProjectTitle }}</strong>
        </div>
        <div class="statusbar-item">
          <span>{{ currentContextLabel }}</span>
          <strong>{{ currentContextValue }}</strong>
        </div>
        <div class="statusbar-item">
          <span>题材</span>
          <strong>{{ currentGenre }}</strong>
        </div>
        <div class="statusbar-spacer"></div>
        <div class="statusbar-item statusbar-item-right">
          <span>{{ currentDetailLabel }}</span>
          <strong>{{ currentDetailValue }}</strong>
        </div>
        <div class="statusbar-item statusbar-item-right">
          <span>{{ currentAuxLabel }}</span>
          <strong>{{ currentAuxValue }}</strong>
        </div>
      </footer>
    </t-layout>
  </t-layout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import SettingsView from "@/views/SettingsView.vue";
import WorkbenchView from "@/views/WorkbenchView.vue";
import { useWorkspace } from "@/composables/useWorkspace";

type WorkbenchStatus = {
  contextLabel: string;
  contextValue: string;
  detailLabel: string;
  detailValue: string;
  auxLabel: string;
  auxValue: string;
};

const workspace = useWorkspace();
const activePage = ref<"review" | "illustration" | "settings">("review");
const workbenchStatus = ref<WorkbenchStatus | null>(null);

const summary = computed(() => workspace.summary.value);
const currentProjectTitle = computed(() => {
  if (summary.value?.project.title) {
    return summary.value.project.title;
  }
  if (activePage.value === "settings") {
    return "工作台";
  }
  return activePage.value === "illustration" ? "自由模式" : "未选择项目";
});
const currentContextLabel = computed(() => {
  if (activePage.value === "settings") {
    return "页面";
  }
  return workbenchStatus.value?.contextLabel || (activePage.value === "review" ? "章节" : "范围");
});
const currentContextValue = computed(() => {
  if (activePage.value === "settings") {
    return "设置";
  }
  return workbenchStatus.value?.contextValue || (activePage.value === "illustration" ? "自由模式" : "未选择章节");
});
const currentGenre = computed(() => summary.value?.project.genre || "-");
const currentDetailLabel = computed(() => {
  if (activePage.value === "settings") {
    return "状态";
  }
  return workbenchStatus.value?.detailLabel || "-";
});
const currentDetailValue = computed(() => {
  if (activePage.value === "settings") {
    return "本地配置";
  }
  return workbenchStatus.value?.detailValue || "-";
});
const currentAuxLabel = computed(() => {
  if (activePage.value === "settings") {
    return "范围";
  }
  return workbenchStatus.value?.auxLabel || "-";
});
const currentAuxValue = computed(() => {
  if (activePage.value === "settings") {
    return summary.value?.project.title || "-";
  }
  return workbenchStatus.value?.auxValue || "-";
});
const workbenchMode = computed<"review" | "illustration">(() =>
  activePage.value === "illustration" ? "illustration" : "review"
);

function setActivePage(value: "review" | "illustration" | "settings") {
  activePage.value = value;
}

function openSettings() {
  activePage.value = "settings";
}

function setWorkbenchStatus(payload: WorkbenchStatus) {
  workbenchStatus.value = payload;
}

onMounted(() => {
  document.title = "Story Canvas - 工作台";
  void workspace.refreshProjects();
});
</script>

<style scoped>
.app-shell {
  height: 100vh;
  overflow: hidden;
  background: var(--bg);
}

.activitybar {
  display: flex;
  flex: 0 0 56px;
  flex-direction: column;
  gap: 12px;
  height: 100vh;
  width: 56px;
  min-width: 56px;
  max-width: 56px;
  padding: 10px 8px;
  overflow: hidden;
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  border-right: 1px solid var(--sidebar-line);
}

.activitybar-top,
.activitybar-nav,
.activitybar-footer {
  display: grid;
  justify-items: center;
  gap: 8px;
}

.activitybar-nav {
  padding-top: 8px;
  border-top: 1px solid var(--sidebar-line);
}

.activitybar-footer {
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px solid var(--sidebar-line);
}

.activitybar-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  padding: 0;
  border: 1px solid transparent;
  border-radius: 4px;
  background: transparent;
  color: var(--sidebar-text);
  cursor: pointer;
  transition: background 160ms ease, border-color 160ms ease, color 160ms ease;
}

.activitybar-button svg {
  width: 18px;
  height: 18px;
  fill: currentColor;
}

.activitybar-button:hover,
.activitybar-button.is-active {
  border-color: rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.brand-button {
  border-color: rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.06);
  color: #ffffff;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.main-layout {
  display: grid;
  min-width: 0;
  height: 100vh;
  overflow: hidden;
  grid-template-rows: minmax(0, 1fr) auto;
}

.page-content {
  min-height: 0;
  height: 100%;
  padding: 0;
  overflow: hidden;
}

.statusbar {
  display: flex;
  align-items: center;
  gap: 16px;
  min-height: 28px;
  padding: 0 18px;
  border-top: 1px solid var(--line);
  background: #eef2f7;
  color: #4b5563;
  font-size: 12px;
  overflow: hidden;
}

.statusbar-item {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.statusbar-item-right {
  justify-content: flex-end;
}

.statusbar-spacer {
  flex: 1;
  min-width: 12px;
}

.statusbar-item strong {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text);
  font-weight: 600;
}

@media (max-width: 1180px) {
  .app-shell,
  .main-layout,
  .page-content {
    height: auto;
  }

  .app-shell,
  .main-layout,
  .page-content {
    overflow: visible;
  }

  .activitybar {
    height: auto;
  }

  .statusbar {
    flex-wrap: wrap;
    padding: 6px 16px;
  }

  .statusbar-item strong {
    max-width: none;
  }
}

@media (max-width: 900px) {
  .app-shell {
    display: grid;
    grid-template-rows: auto minmax(0, 1fr);
    min-height: 100vh;
  }

  .activitybar {
    flex-direction: row;
    align-items: center;
    width: 100%;
    min-width: 0;
    max-width: none;
    height: auto;
    padding: 8px 10px;
    border-right: 0;
    border-bottom: 1px solid var(--sidebar-line);
  }

  .activitybar-top,
  .activitybar-nav,
  .activitybar-footer {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .activitybar-nav {
    margin-left: 10px;
    padding-top: 0;
    padding-left: 10px;
    border-top: 0;
    border-left: 1px solid var(--sidebar-line);
  }

  .activitybar-footer {
    margin-top: 0;
    margin-left: auto;
    padding-top: 0;
    padding-left: 10px;
    border-top: 0;
    border-left: 1px solid var(--sidebar-line);
  }

  .main-layout {
    min-height: 0;
  }

  .statusbar {
    gap: 8px 12px;
    padding: 8px 12px;
  }
}
</style>
