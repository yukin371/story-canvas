<template>
  <WorkbenchPaneCard :title="title" variant="sidebar">
    <div class="workbench-sidebar">
      <section v-if="$slots.top" class="workbench-sidebar-section workbench-sidebar-section-top">
        <slot name="top" />
      </section>

      <section v-if="$slots.middle" class="workbench-sidebar-section workbench-sidebar-section-middle">
        <slot name="middle" />
      </section>

      <section v-if="$slots.bottom" class="workbench-sidebar-section workbench-sidebar-section-bottom workbench-sidebar-section-fill">
        <slot name="bottom" />
      </section>
    </div>
  </WorkbenchPaneCard>
</template>

<script setup lang="ts">
import WorkbenchPaneCard from "@/components/WorkbenchPaneCard.vue";

defineProps<{
  title: string;
}>();
</script>

<style scoped>
.workbench-sidebar {
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  min-height: 0;
  min-width: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.workbench-sidebar-section {
  display: grid;
  gap: 10px;
  min-height: 0;
  min-width: 0;
  padding: 8px 10px;
  border-top: 1px solid #eef1f4;
  overflow: hidden;
}

.workbench-sidebar-section:first-child {
  padding-top: 8px;
  border-top: 0;
}

.workbench-sidebar-section-fill {
  grid-template-rows: auto minmax(0, 1fr);
}

.workbench-sidebar-section-middle :deep(.result-card),
.workbench-sidebar-section-middle :deep(.asset-preview-frame-compact) {
  max-height: 188px;
}

.workbench-sidebar-section-bottom {
  min-height: 0;
}
</style>
