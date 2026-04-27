import { computed, reactive } from "vue";

import {
  fetchProjectSummary,
  fetchProjects,
  fetchWorkbenchSettings,
  markProjectRecent,
  saveWorkbenchSettings,
  type ProjectOption,
  type ProjectListPayload,
  type ProjectSummary,
  type WorkbenchSettings,
  type WorkbenchSettingsUpdate,
} from "@/api/storyCanvas";

type WorkspaceState = {
  loading: boolean;
  loadingSummary: boolean;
  loadingSettings: boolean;
  savingSettings: boolean;
  error: string;
  settingsError: string;
  recentProjects: ProjectOption[];
  libraryProjects: ProjectOption[];
  projectRegistryFile: string;
  selectedRoot: string;
  summary: ProjectSummary | null;
  settings: WorkbenchSettings | null;
};

const state = reactive<WorkspaceState>({
  loading: false,
  loadingSummary: false,
  loadingSettings: false,
  savingSettings: false,
  error: "",
  settingsError: "",
  recentProjects: [],
  libraryProjects: [],
  projectRegistryFile: "",
  selectedRoot: "",
  summary: null,
  settings: null,
});

function allProjectsFromState(): ProjectOption[] {
  const merged = [...state.recentProjects, ...state.libraryProjects];
  const seen = new Set<string>();
  return merged.filter((item) => {
    if (seen.has(item.root)) {
      return false;
    }
    seen.add(item.root);
    return true;
  });
}

async function refreshProjects() {
  state.loading = true;
  state.error = "";
  try {
    const payload: ProjectListPayload = await fetchProjects();
    state.recentProjects = payload.recentProjects;
    state.libraryProjects = payload.libraryProjects;
    state.projectRegistryFile = payload.registryFile;
    const projects = allProjectsFromState();
    if (state.selectedRoot && projects.some((item) => item.root === state.selectedRoot)) {
      await Promise.all([refreshSummary(), refreshSettings(state.selectedRoot)]);
    } else {
      state.selectedRoot = "";
      state.summary = null;
      await refreshSettings("");
    }
  } catch (error) {
    state.error = error instanceof Error ? error.message : String(error);
  } finally {
    state.loading = false;
  }
}

async function refreshSummary() {
  if (!state.selectedRoot) {
    state.summary = null;
    return;
  }
  state.loadingSummary = true;
  state.error = "";
  try {
    state.summary = await fetchProjectSummary(state.selectedRoot);
  } catch (error) {
    state.error = error instanceof Error ? error.message : String(error);
  } finally {
    state.loadingSummary = false;
  }
}

async function refreshSettings(root = state.selectedRoot) {
  state.loadingSettings = true;
  state.settingsError = "";
  try {
    state.settings = await fetchWorkbenchSettings(root || undefined);
  } catch (error) {
    state.settingsError = error instanceof Error ? error.message : String(error);
  } finally {
    state.loadingSettings = false;
  }
}

async function selectProject(root: string) {
  state.selectedRoot = root;
  if (root) {
    try {
      await markProjectRecent(root);
    } catch {
      // ignore recent-mark failure; the project can still be opened
    }
  }
  await Promise.all([refreshSummary(), refreshSettings(root)]);
  if (root) {
    await refreshProjects();
  }
}

async function persistSettings(payload: WorkbenchSettingsUpdate) {
  state.savingSettings = true;
  state.settingsError = "";
  try {
    state.settings = await saveWorkbenchSettings(payload);
    if (state.selectedRoot) {
      await refreshSummary();
    }
  } catch (error) {
    state.settingsError = error instanceof Error ? error.message : String(error);
    throw error;
  } finally {
    state.savingSettings = false;
  }
}

export function useWorkspace() {
  return {
    state,
    projects: computed(() => allProjectsFromState()),
    recentProjects: computed(() => state.recentProjects),
    libraryProjects: computed(() => state.libraryProjects),
    projectRegistryFile: computed(() => state.projectRegistryFile),
    summary: computed(() => state.summary),
    settings: computed(() => state.settings),
    selectedRoot: computed(() => state.selectedRoot),
    error: computed(() => state.error),
    settingsError: computed(() => state.settingsError),
    loadingSettings: computed(() => state.loadingSettings),
    savingSettings: computed(() => state.savingSettings),
    refreshProjects,
    refreshSummary,
    refreshSettings,
    persistSettings,
    selectProject,
  };
}
