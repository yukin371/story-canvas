<template>
  <div class="review-grid">
    <section class="review-column review-column-nav">
      <WorkbenchSidebarCard title="">
        <template #top>
          <div class="workspace-explorer">
            <div class="workspace-explorer-head">
              <strong class="workspace-explorer-label">项目</strong>
              <div class="workspace-section-actions">
                <button class="workspace-inline-button" type="button" @click="view.showProjectSetup.value = !view.showProjectSetup.value">项目</button>
                <button class="workspace-inline-button" type="button" @click="view.refreshProjects()">刷新</button>
              </div>
            </div>
            <select class="workspace-native-field workspace-native-select" :value="view.selectedRoot.value" @change="view.handleProjectSelect(($event.target as HTMLSelectElement).value)">
              <option value="">选择项目</option>
              <option v-for="item in view.explorerProjectOptions.value" :key="String(item.value)" :value="String(item.value)">
                {{ item.label }}
              </option>
            </select>
            <div v-if="view.selectedRoot.value" class="workspace-inline-switch">
              <button class="workspace-inline-button" type="button" @click="view.leaveProject()">退出项目</button>
            </div>
            <div v-if="view.showProjectSetup.value" class="workspace-project-create workspace-project-create-inline">
              <div class="workspace-project-switcher" role="tablist" aria-label="项目操作">
                <button
                  class="workspace-project-switcher-item"
                  :class="{ 'is-active': view.projectPanelMode.value === 'import' }"
                  type="button"
                  @click="view.projectPanelMode.value = 'import'"
                >
                  导入
                </button>
                <button
                  class="workspace-project-switcher-item"
                  :class="{ 'is-active': view.projectPanelMode.value === 'create' }"
                  type="button"
                  @click="view.projectPanelMode.value = 'create'"
                >
                  新建
                </button>
              </div>
              <template v-if="view.projectPanelMode.value === 'import'">
                <div class="workspace-project-import-row">
                  <input v-model="view.importProjectRootDraft.value" class="workspace-native-field" placeholder="选择已有项目根目录" />
                  <button
                    class="workspace-action-button"
                    type="button"
                    :disabled="view.selectingProjectFolder.value"
                    @click="view.handleSelectProjectFolder()"
                  >
                    {{ view.selectingProjectFolder.value ? "选择中..." : "选择目录" }}
                  </button>
                  <button
                    class="workspace-action-button"
                    type="button"
                    :disabled="view.creatingProject.value"
                    @click="view.handleImportProject()"
                  >
                    {{ view.creatingProject.value ? "导入中..." : "导入项目" }}
                  </button>
                </div>
              </template>
              <template v-else>
                <input v-model="view.projectTitleDraft.value" class="workspace-native-field" placeholder="项目标题" />
                <div class="workspace-project-create-row">
                  <input v-model="view.projectGenreDraft.value" class="workspace-native-field" placeholder="题材" />
                  <input v-model="view.projectDirectoryDraft.value" class="workspace-native-field" placeholder="目录名" />
                </div>
                <div class="detail-actions compact-actions">
                  <button
                    class="workspace-action-button is-primary"
                    type="button"
                    :disabled="view.creatingProject.value"
                    @click="view.handleCreateProject()"
                  >
                    {{ view.creatingProject.value ? "创建中..." : "创建项目" }}
                  </button>
                </div>
              </template>
            </div>
            <p v-if="view.sidebarMessage.value" class="inline-error">{{ view.sidebarMessage.value }}</p>
          </div>
        </template>

        <template #bottom>
          <div class="workspace-nav">
            <div v-if="!view.summary.value" class="empty-pane workspace-empty-compact">先选择一个项目。</div>

            <details
              class="workspace-tree-group"
              :open="view.sidebarGroupOpen.reviewChapters"
              @toggle="view.handleSidebarGroupToggle('reviewChapters', $event)"
            >
              <summary>章节</summary>
              <div v-if="view.chapterList.value.length === 0" class="workspace-tree-empty">当前没有可用章节。</div>
              <div v-else class="workspace-tree-list">
                <button
                  v-for="item in view.orderedChapterList.value"
                  :key="item.id"
                  class="workspace-tree-item"
                  :class="{ 'is-active': item.id === view.selectedChapter.value?.id }"
                  type="button"
                  draggable="true"
                  @dragstart="view.handleTreeDragStart('chapter', item.id)"
                  @dragover.prevent
                  @drop="view.handleTreeDrop('chapter', item.id)"
                  @click="view.selectChapter(item)"
                >
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.id }}</span>
                </button>
              </div>
            </details>

            <details
              class="workspace-tree-group"
              :open="view.sidebarGroupOpen.reviewEntities"
              @toggle="view.handleSidebarGroupToggle('reviewEntities', $event)"
            >
              <summary>角色卡</summary>
              <div v-if="view.entityList.value.length === 0" class="workspace-tree-empty">当前没有角色卡。</div>
              <div v-else class="workspace-tree-list">
                <div
                  v-for="item in view.orderedEntityList.value"
                  :key="item.id"
                  class="workspace-tree-item workspace-tree-item-action"
                  :class="{ 'is-active': item.id === view.selectedEntity.value?.id }"
                  draggable="true"
                  @dragstart="view.handleTreeDragStart('entity', item.id)"
                  @dragover.prevent
                  @drop="view.handleTreeDrop('entity', item.id)"
                  @click="view.selectEntity(item)"
                >
                  <div class="workspace-tree-item-copy">
                    <strong>{{ item.name }}</strong>
                    <span>{{ item.type || "entity" }}</span>
                  </div>
                  <button class="workspace-mini-action" type="button" @click.stop="view.openEntityIllustration(item.id)">设定图</button>
                </div>
              </div>
            </details>

            <details
              class="workspace-tree-group"
              :open="view.sidebarGroupOpen.reviewReference"
              @toggle="view.handleSidebarGroupToggle('reviewReference', $event)"
            >
              <summary>资料</summary>
              <div class="workspace-tree-list">
                <div class="workspace-tree-item workspace-tree-item-static">
                  <strong>世界设定</strong>
                  <span>{{ view.worldbookList.value.length }} 条</span>
                </div>
                <button
                  v-for="item in view.worldbookReferenceItems.value"
                  :key="item.id"
                  class="workspace-tree-item workspace-tree-item-child"
                  :class="{ 'is-active': item.id === view.selectedReference.value?.id }"
                  type="button"
                  @click="view.selectReference(item)"
                >
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.subtitle }}</span>
                </button>
                <div class="workspace-tree-item workspace-tree-item-static">
                  <strong>卷结构</strong>
                  <span>{{ view.volumeList.value.length }} 卷</span>
                </div>
                <button
                  v-for="item in view.volumeReferenceItems.value"
                  :key="item.id"
                  class="workspace-tree-item workspace-tree-item-child"
                  :class="{ 'is-active': item.id === view.selectedReference.value?.id }"
                  type="button"
                  @click="view.selectReference(item)"
                >
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.subtitle }}</span>
                </button>
                <div class="workspace-tree-item workspace-tree-item-static">
                  <strong>审查包</strong>
                  <span>{{ view.existingReviewPacketCount.value }} 份</span>
                </div>
                <button
                  v-for="item in view.reviewPacketReferenceItems.value"
                  :key="item.id"
                  class="workspace-tree-item workspace-tree-item-child"
                  :class="{ 'is-active': item.id === view.selectedReference.value?.id }"
                  type="button"
                  @click="view.selectReference(item)"
                >
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.exists ? item.filePath : '未生成' }}</span>
                </button>
              </div>
            </details>
          </div>
        </template>
      </WorkbenchSidebarCard>
    </section>

    <section class="review-column review-column-main">
      <WorkbenchPaneCard title="">
        <template v-if="view.detailMode.value === 'chapter' && view.selectedChapter.value">
          <div class="review-workspace">
            <section class="review-editor-pane">
              <article class="chapter-content">
                {{ view.selectedChapter.value.content || "当前章节还没有可展示正文。" }}
              </article>
            </section>

            <aside class="review-inspector-pane">
              <div class="focus-section focus-section-compact">
                <strong class="section-title">问题</strong>
                <div class="issue-list">
                  <div v-for="issue in view.visibleIssues.value" :key="issue" class="issue-chip">
                    {{ issue }}
                  </div>
                </div>
              </div>

              <div class="focus-section focus-section-compact">
                <strong class="section-title">动作</strong>
                <div class="action-stack compact-stack">
                  <article v-for="item in view.actionQueue.value" :key="item.title" class="action-item compact-item">
                    <div class="action-head">
                      <strong>{{ item.title }}</strong>
                      <span>{{ item.status }}</span>
                    </div>
                    <p>{{ item.detail }}</p>
                  </article>
                </div>
              </div>

              <div class="focus-section focus-section-compact">
                <strong class="section-title">协议</strong>
                <div class="protocol-inline">
                  <div v-for="entry in view.protocolEntries.value" :key="entry.label" class="fact-item compact-fact">
                    <span>{{ entry.label }}</span>
                    <strong>{{ entry.value }}</strong>
                  </div>
                </div>
              </div>

              <div v-if="view.selectedChapter.value" class="focus-section focus-section-compact">
                <ContextPanel :root="view.selectedRoot.value" :chapter-id="view.selectedChapter.value.id" />
              </div>
            </aside>
          </div>
        </template>

        <template v-else-if="view.detailMode.value === 'entity' && view.selectedEntity.value">
          <div class="detail-document">
            <header class="detail-document-head">
              <span>{{ view.selectedEntity.value.type || "entity" }}</span>
              <strong>{{ view.selectedEntity.value.name }}</strong>
              <button class="workspace-action-button" type="button" @click="view.openEntityIllustration(view.selectedEntity.value.id)">设定图</button>
            </header>
            <section class="detail-document-section">
              <strong class="section-title">角色卡</strong>
              <p>{{ view.selectedEntity.value.summary || "当前角色没有摘要。" }}</p>
            </section>
            <section class="detail-document-section">
              <strong class="section-title">外观</strong>
              <p>{{ view.selectedEntity.value.appearanceSummary || "当前角色没有外观摘要。" }}</p>
            </section>
            <section class="detail-document-section">
              <strong class="section-title">当前状态</strong>
              <pre>{{ formatDetailValue(view.selectedEntity.value.currentState || "暂无状态") }}</pre>
            </section>
            <section class="detail-document-section detail-document-grid">
              <div class="fact-item compact-fact">
                <span>别名</span>
                <strong>{{ (view.selectedEntity.value.aliases || []).join(" / ") || "-" }}</strong>
              </div>
              <div class="fact-item compact-fact">
                <span>Profile</span>
                <strong>{{ formatDetailValue(view.selectedEntity.value.profile || {}) }}</strong>
              </div>
              <div class="fact-item compact-fact">
                <span>Seed</span>
                <strong>{{ formatDetailValue(view.selectedEntity.value.seed || {}) }}</strong>
              </div>
            </section>
          </div>
        </template>

        <template v-else-if="view.detailMode.value === 'reference' && view.selectedReference.value">
          <div class="detail-document">
            <header class="detail-document-head">
              <span>{{ view.selectedReference.value.subtitle }}</span>
              <strong>{{ view.selectedReference.value.title }}</strong>
            </header>
            <section class="detail-document-section">
              <strong class="section-title">摘要</strong>
              <p>{{ view.selectedReference.value.detail }}</p>
            </section>
            <section v-if="view.selectedReference.value.meta?.length" class="detail-document-section detail-document-grid">
              <div v-for="entry in view.selectedReference.value.meta" :key="entry.label" class="fact-item compact-fact">
                <span>{{ entry.label }}</span>
                <strong>{{ entry.value }}</strong>
              </div>
            </section>
            <section v-if="view.selectedReference.value.chapters?.length" class="detail-document-section">
              <strong class="section-title">章节</strong>
              <div class="reference-chapter-list">
                <article v-for="chapter in view.selectedReference.value.chapters" :key="chapter.id" class="reference-chapter-item">
                  <strong>{{ chapter.title }}</strong>
                  <span>{{ chapter.id }} · {{ chapter.status || "未标记" }}</span>
                  <p>{{ chapter.summary || "暂无章节方向。" }}</p>
                </article>
              </div>
            </section>
            <section v-if="view.selectedReference.value.preview" class="detail-document-section">
              <strong class="section-title">预览</strong>
              <pre>{{ view.selectedReference.value.preview }}</pre>
            </section>
          </div>
        </template>

        <div v-else class="starter-panel">
          <div class="starter-hero">
            <strong>这里会显示当前章节的审查焦点。</strong>
            <p class="detail-copy">从左侧选择项目和章节。</p>
          </div>
        </div>
      </WorkbenchPaneCard>
    </section>
  </div>
</template>

<script setup lang="ts">
import ContextPanel from "@/components/workbench/ContextPanel.vue";
import WorkbenchPaneCard from "@/components/WorkbenchPaneCard.vue";
import WorkbenchSidebarCard from "@/components/WorkbenchSidebarCard.vue";

defineProps<{
  view: any;
}>();

function formatDetailValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value, null, 2);
}
</script>

<style scoped>
.review-grid {
  display: grid;
  grid-template-columns: var(--workbench-side-width) minmax(0, 1fr);
  gap: 0;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.review-column {
  display: grid;
  height: 100%;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
}

.review-column-nav {
  grid-template-rows: minmax(0, 1fr);
  width: var(--workbench-side-width);
  min-width: var(--workbench-side-width);
  max-width: var(--workbench-side-width);
  background: var(--surface-side);
}

.review-column-main {
  grid-template-rows: minmax(0, 1fr);
  min-width: 0;
  background: var(--surface);
}

.workspace-explorer {
  display: grid;
  gap: 8px;
}

.workspace-explorer-head,
.workspace-section-actions,
.action-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.workspace-explorer-label {
  color: var(--muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.workspace-nav {
  display: grid;
  gap: 6px;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  scrollbar-gutter: stable;
}

.workspace-tree-group {
  display: grid;
  gap: 2px;
}

.workspace-tree-group summary {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 0;
  color: var(--muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  list-style: none;
  user-select: none;
}

.workspace-tree-group summary::before {
  content: "";
  width: 0;
  height: 0;
  border-top: 4px solid transparent;
  border-bottom: 4px solid transparent;
  border-left: 5px solid currentColor;
  transform: rotate(0deg);
  transform-origin: 35% 50%;
  transition: transform 160ms ease;
}

.workspace-tree-group[open] summary::before {
  transform: rotate(90deg);
}

.workspace-tree-group summary::-webkit-details-marker {
  display: none;
}

.workspace-tree-list {
  display: grid;
  gap: 0;
}

.workspace-tree-item {
  display: grid;
  gap: 2px;
  width: 100%;
  padding: 6px 8px 6px 16px;
  border: 0;
  border-left: 2px solid transparent;
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: background 160ms ease, border-color 160ms ease;
}

.workspace-tree-item strong {
  font-size: 13px;
  font-weight: 500;
}

.workspace-tree-item strong,
.workspace-tree-item span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workspace-tree-item span,
.workspace-tree-empty,
.detail-copy {
  color: var(--muted);
  font-size: 11px;
}

.workspace-tree-item:hover,
.workspace-tree-item.is-active {
  border-left-color: rgba(0, 82, 217, 0.45);
  background: rgba(255, 255, 255, 0.58);
}

.workspace-tree-item-static {
  cursor: default;
  opacity: 0.8;
}

.workspace-tree-item-child {
  padding-left: 28px;
}

.workspace-tree-item-action {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
}

.workspace-tree-item-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.workspace-tree-empty {
  padding: 6px 8px 6px 16px;
}

.workspace-mini-action {
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--accent);
  font: inherit;
  cursor: pointer;
}

.workspace-section-actions {
  justify-content: flex-end;
}

.workspace-inline-button,
.workspace-action-button {
  border: 1px solid transparent;
  background: transparent;
  color: var(--muted);
  font: inherit;
  font-size: 12px;
  line-height: 1.35;
  cursor: pointer;
  transition: background 160ms ease, border-color 160ms ease, color 160ms ease, opacity 160ms ease;
}

.workspace-inline-button {
  padding: 0;
}

.workspace-inline-button:hover,
.workspace-action-button:hover {
  color: var(--text);
}

.workspace-native-field,
.workspace-native-select {
  width: 100%;
  min-width: 0;
  padding: 7px 10px;
  border: 1px solid rgba(31, 35, 41, 0.12);
  background: #ffffff;
  color: var(--text);
  font: inherit;
  font-size: 12px;
  line-height: 1.35;
  outline: none;
  transition: border-color 160ms ease, box-shadow 160ms ease, background 160ms ease;
}

.workspace-native-select {
  appearance: none;
}

.workspace-native-field::placeholder {
  color: rgba(75, 85, 99, 0.78);
}

.workspace-native-field:focus,
.workspace-native-select:focus {
  border-color: rgba(0, 82, 217, 0.42);
  box-shadow: 0 0 0 3px rgba(0, 82, 217, 0.08);
}

.workspace-action-button {
  padding: 7px 10px;
  border-color: rgba(31, 35, 41, 0.12);
  background: #ffffff;
  color: var(--text);
  white-space: nowrap;
}

.workspace-action-button:hover {
  border-color: rgba(0, 82, 217, 0.28);
  background: #f7faff;
}

.workspace-action-button.is-primary {
  border-color: transparent;
  background: var(--accent);
  color: #ffffff;
}

.workspace-action-button.is-primary:hover {
  border-color: transparent;
  background: #0047bb;
  color: #ffffff;
}

.workspace-inline-button:disabled,
.workspace-action-button:disabled {
  opacity: 0.6;
  cursor: default;
}

.workspace-project-create {
  display: grid;
  gap: 8px;
  padding: 2px 0 0;
}

.workspace-project-create-inline {
  border-top: 1px solid rgba(31, 35, 41, 0.08);
  padding-top: 8px;
}

.workspace-project-switcher {
  display: flex;
  align-items: center;
  gap: 4px;
}

.workspace-project-switcher-item {
  padding: 4px 10px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--muted);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.workspace-project-switcher-item:hover {
  background: rgba(255, 255, 255, 0.5);
  color: var(--text);
}

.workspace-project-switcher-item.is-active {
  border-color: var(--line);
  background: #ffffff;
  color: var(--text);
}

.workspace-inline-switch {
  display: flex;
  justify-content: flex-end;
}

.workspace-project-create-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.workspace-project-import-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 8px;
  align-items: center;
}

.workspace-empty-compact {
  min-height: 72px;
}

.empty-pane {
  display: grid;
  place-items: center;
  min-height: 120px;
  color: var(--muted);
  font-size: 13px;
}

.chapter-content {
  margin: 0;
  padding: 12px 16px 16px;
  color: var(--text);
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  overflow: auto;
}

.review-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.review-editor-pane,
.review-inspector-pane {
  min-height: 0;
}

.review-editor-pane {
  display: grid;
  min-height: 0;
  background: #ffffff;
}

.review-inspector-pane {
  display: grid;
  align-content: start;
  gap: 8px;
  min-width: 0;
  overflow: auto;
  padding: 8px 10px 10px;
  border-left: 1px solid rgba(31, 35, 41, 0.08);
  background: #fbfcfe;
}

.focus-section {
  display: grid;
  gap: 6px;
}

.focus-section-compact {
  padding-left: 10px;
  border-left: 2px solid #dbe2ea;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
}

.issue-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.issue-chip {
  padding: 3px 6px;
  border: 1px solid #dbe2ea;
  background: transparent;
  color: var(--muted);
  font-size: 12px;
}

.compact-stack,
.action-stack {
  display: grid;
  gap: 8px;
}

.action-item,
.compact-fact {
  display: grid;
  gap: 6px;
  padding: 6px 0 6px 10px;
  border-left: 2px solid #dbe2ea;
  background: transparent;
}

.action-item p {
  margin: 4px 0 0;
  line-height: 1.5;
  font-size: 12px;
}

.protocol-inline {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.compact-fact span {
  display: block;
  font-size: 12px;
  color: var(--muted);
}

.compact-fact strong {
  display: block;
  margin-top: 4px;
  line-height: 1.4;
  word-break: break-word;
}

.starter-panel {
  display: grid;
  align-content: start;
  gap: 16px;
  min-height: 100%;
  padding: 12px;
}

.starter-hero {
  display: grid;
  gap: 6px;
}

.starter-hero strong {
  font-size: 16px;
  font-weight: 600;
}

.detail-document {
  display: grid;
  align-content: start;
  gap: 14px;
  min-height: 100%;
  padding: 18px 22px 28px;
  overflow: auto;
  background: #ffffff;
}

.detail-document-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px 12px;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(31, 35, 41, 0.08);
}

.detail-document-head span {
  grid-column: 1 / -1;
  color: var(--muted);
  font-size: 12px;
}

.detail-document-head strong {
  min-width: 0;
  overflow-wrap: anywhere;
  font-size: 20px;
  font-weight: 650;
}

.detail-document-section {
  display: grid;
  gap: 8px;
  max-width: 920px;
}

.detail-document-section p,
.reference-chapter-item p {
  margin: 0;
  color: var(--text);
  line-height: 1.7;
  white-space: pre-wrap;
}

.detail-document-section pre {
  margin: 0;
  padding: 10px 12px;
  overflow: auto;
  border: 1px solid rgba(31, 35, 41, 0.08);
  background: #f7f9fc;
  color: var(--text);
  font: inherit;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.detail-document-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.reference-chapter-list {
  display: grid;
  gap: 8px;
}

.reference-chapter-item {
  display: grid;
  gap: 4px;
  padding: 8px 10px;
  border-left: 2px solid #dbe2ea;
  background: #fbfcfe;
}

.reference-chapter-item span {
  color: var(--muted);
  font-size: 12px;
}

.inline-error {
  margin: 0;
  color: #c93537;
  font-size: 12px;
}

@media (max-width: 1180px) {
  .review-grid,
  .protocol-inline,
  .detail-document-grid,
  .workspace-project-import-row,
  .workspace-project-create-row {
    grid-template-columns: 1fr;
  }

  .review-workspace {
    grid-template-columns: minmax(0, 1fr) 260px;
  }

  .review-grid {
    overflow: visible;
  }

  .review-column,
  .review-column-main,
  .review-editor-pane,
  .review-inspector-pane,
  .workspace-nav,
  .chapter-content {
    overflow: visible;
  }

  .review-column-nav {
    grid-template-rows: auto;
    width: auto;
    min-width: 0;
    max-width: none;
  }

  .review-workspace {
    height: auto;
  }

  .review-inspector-pane {
    padding: 8px 8px 10px;
  }

  .focus-section-compact {
    padding-left: 8px;
  }
}

@media (max-width: 1024px) {
  .review-workspace {
    grid-template-columns: 1fr;
  }

  .review-inspector-pane {
    border-left: 0;
    border-top: 1px solid rgba(31, 35, 41, 0.08);
    padding-top: 12px;
  }
}

@media (max-width: 900px) {
  .workspace-tree-item {
    padding-left: 12px;
  }

  .chapter-content {
    padding: 12px;
    font-size: 13px;
    line-height: 1.7;
  }
}
</style>
