<template>
  <div class="workbench-shell">
    <ReviewWorkbenchView
      v-if="workspaceMode === 'review'"
      v-model:workspace-mode="workspaceMode"
      @workspace-status="emit('workspace-status', $event)"
      @open-illustration-target="handleOpenIllustrationTarget"
    />
    <IllustrationWorkbenchView
      v-else
      v-model:workspace-mode="workspaceMode"
      :pending-target="pendingIllustrationTarget"
      @workspace-status="emit('workspace-status', $event)"
      @open-settings="emit('open-settings')"
      @consume-pending-target="pendingIllustrationTarget = null"
    />
  </div>
</template>

<script setup lang="ts">
import { defineAsyncComponent, ref } from "vue";

const ReviewWorkbenchView = defineAsyncComponent(() => import("@/views/workbench/ReviewWorkbenchView.vue"));
const IllustrationWorkbenchView = defineAsyncComponent(() => import("@/views/workbench/IllustrationWorkbenchView.vue"));

const workspaceMode = defineModel<"review" | "illustration">("workspaceMode", { required: true });
const pendingIllustrationTarget = ref<{ type: "chapter" | "entity"; id: string } | null>(null);

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
}>();

function handleOpenIllustrationTarget(payload: { type: "chapter" | "entity"; id: string }) {
  pendingIllustrationTarget.value = payload;
  workspaceMode.value = "illustration";
}
</script>

<style scoped>
.workbench-shell {
  display: grid;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}
</style>
