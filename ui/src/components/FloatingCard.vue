<template>
  <Teleport to="body">
    <Transition name="floating-card">
      <div v-if="visible" class="floating-card-overlay" @click.self="handleClose">
        <div class="floating-card-shell" :style="{ width: width + 'px' }">
          <div class="floating-card-head">
            <strong class="floating-card-title">{{ title }}</strong>
            <button class="floating-card-close" type="button" aria-label="关闭" @click="handleClose">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M4 4L12 12M12 4L4 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
              </svg>
            </button>
          </div>
          <div class="floating-card-body">
            <slot />
          </div>
          <div v-if="$slots.footer" class="floating-card-foot">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    visible: boolean;
    title?: string;
    width?: number;
  }>(),
  { title: "", width: 560 }
);

const emit = defineEmits<{
  "update:visible": [value: boolean];
}>();

function handleClose() {
  emit("update:visible", false);
}
</script>

<style scoped>
.floating-card-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.25);
}

.floating-card-shell {
  display: grid;
  grid-template-rows: auto 1fr auto;
  max-height: 85vh;
  background: var(--bg-page, #fff);
  border: 1px solid var(--line, #dcdee2);
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15), 0 2px 8px rgba(0, 0, 0, 0.08);
}

.floating-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line, #dcdee2);
}

.floating-card-title {
  font-size: 14px;
}

.floating-card-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: var(--text-secondary, #8c8c8c);
  cursor: pointer;
  transition: background 120ms, color 120ms;
}

.floating-card-close:hover {
  background: var(--bg-grey, #f3f3f3);
  color: var(--text-primary, #1a1a1a);
}

.floating-card-body {
  min-height: 0;
  padding: 16px;
  overflow: auto;
}

.floating-card-foot {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 10px 16px;
  border-top: 1px solid var(--line, #dcdee2);
}

.floating-card-enter-active {
  transition: opacity 160ms ease;
}
.floating-card-enter-active .floating-card-shell {
  transition: transform 160ms ease, opacity 160ms ease;
}

.floating-card-enter-from {
  opacity: 0;
}
.floating-card-enter-from .floating-card-shell {
  transform: scale(0.96) translateY(8px);
  opacity: 0;
}

.floating-card-leave-active {
  transition: opacity 120ms ease;
}
.floating-card-leave-active .floating-card-shell {
  transition: transform 120ms ease, opacity 120ms ease;
}

.floating-card-leave-to {
  opacity: 0;
}
.floating-card-leave-to .floating-card-shell {
  transform: scale(0.97);
  opacity: 0;
}
</style>
