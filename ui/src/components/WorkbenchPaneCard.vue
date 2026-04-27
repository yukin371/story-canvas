<template>
  <section :class="cardClass">
    <header v-if="title" class="workbench-pane-header">
      <strong>{{ title }}</strong>
    </header>
    <div class="workbench-pane-body">
      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    title: string;
    fill?: boolean;
    variant?: "default" | "sidebar";
  }>(),
  {
    fill: true,
    variant: "default",
  }
);

const cardClass = computed(() => [
  "workbench-pane",
  !props.title ? "workbench-pane-no-header" : "",
  props.fill ? "workbench-pane-fill" : "",
  props.variant === "sidebar" ? "workbench-sidebar-card" : "",
]);
</script>

<style scoped>
.workbench-pane {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  height: 100%;
  min-height: 0;
  min-width: 0;
  width: 100%;
  overflow: hidden;
}

.workbench-pane-no-header {
  grid-template-rows: minmax(0, 1fr);
}

.workbench-pane-header {
  display: flex;
  align-items: center;
  min-height: 32px;
  padding: 0 12px;
  border-bottom: 1px solid rgba(31, 35, 41, 0.08);
}

.workbench-pane-header strong {
  font-size: 14px;
  font-weight: 600;
}

.workbench-sidebar-card .workbench-pane-header {
  border-bottom-color: #d8e1ec;
}

.workbench-pane-body {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
  min-width: 0;
  height: 100%;
  padding: 0;
  overflow: hidden;
}

.workbench-pane-body > * {
  min-height: 0;
  min-width: 0;
}
</style>
