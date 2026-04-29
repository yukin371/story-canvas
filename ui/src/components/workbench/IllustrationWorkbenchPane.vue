<template>
  <div class="illustration-grid-separated">
    <section class="illustration-column illustration-column-side">
      <WorkbenchSidebarCard title="">
        <template #top>
          <div class="workspace-explorer">
            <div class="workspace-explorer-head">
              <strong class="workspace-explorer-label">项目</strong>
              <div class="workspace-section-actions">
                <t-button variant="text" size="small" @click="view.showProjectSetup.value = !view.showProjectSetup.value">项目</t-button>
                <t-button variant="text" size="small" @click="view.refreshProjects()">刷新</t-button>
              </div>
            </div>
            <t-select
              :model-value="view.selectedRoot.value"
              :options="view.explorerProjectOptions.value"
              placeholder="选择项目"
              clearable
              @update:model-value="view.handleProjectSelect(String($event ?? ''))"
            />
            <div v-if="view.selectedRoot.value" class="workspace-inline-switch">
              <t-button variant="text" size="small" @click="view.leaveProject()">自由模式</t-button>
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
                  <t-input v-model="view.importProjectRootDraft.value" placeholder="选择已有项目根目录" />
                  <t-button variant="outline" size="small" :loading="view.selectingProjectFolder.value" @click="view.handleSelectProjectFolder()">
                    选择目录
                  </t-button>
                  <t-button variant="outline" size="small" :loading="view.creatingProject.value" @click="view.handleImportProject()">
                    导入项目
                  </t-button>
                </div>
              </template>
              <template v-else>
                <t-input v-model="view.projectTitleDraft.value" placeholder="项目标题" />
                <div class="workspace-project-create-row">
                  <t-input v-model="view.projectGenreDraft.value" placeholder="题材" />
                  <t-input v-model="view.projectDirectoryDraft.value" placeholder="目录名" />
                </div>
                <div class="detail-actions compact-actions">
                  <t-button theme="primary" size="small" :loading="view.creatingProject.value" @click="view.handleCreateProject()">
                    创建项目
                  </t-button>
                </div>
              </template>
            </div>
            <p v-if="view.sidebarMessage.value" class="inline-error">{{ view.sidebarMessage.value }}</p>
            <div v-if="view.illustrationSetupWarning.value" class="settings-warning-card">
              <strong>生图配置未完成</strong>
              <p>{{ view.illustrationSetupWarning.value }}</p>
              <t-button size="small" theme="primary" @click="view.openSettings()">去设置</t-button>
            </div>
          </div>
        </template>

        <template #middle>
          <div class="workspace-illustration-controls">
            <div class="workspace-parameter-grid">
              <t-form-item label="目标类型">
                <t-radio-group v-model="view.targetType.value" size="small">
                  <t-radio-button value="entity">角色</t-radio-button>
                  <t-radio-button value="chapter">场景</t-radio-button>
                </t-radio-group>
              </t-form-item>
              <t-form-item :label="view.isProjectBound.value ? (view.targetType.value === 'entity' ? '角色' : '章节') : '目标'">
                <t-select v-if="view.isProjectBound.value" v-model="view.targetId.value" :options="view.targetOptions.value" size="small" />
                <t-input
                  v-else
                  v-model="view.manualTargetName.value"
                  size="small"
                  :placeholder="view.targetType.value === 'entity' ? '例如：白发女剑修' : '例如：雨夜屋顶对峙'"
                />
              </t-form-item>
              <t-form-item label="模式">
                <t-radio-group v-model="view.mode.value" size="small">
                  <t-radio-button value="text-to-image">文生图</t-radio-button>
                  <t-radio-button value="image-to-image">图生图</t-radio-button>
                  <t-radio-button value="inpaint">重绘</t-radio-button>
                </t-radio-group>
              </t-form-item>
              <t-form-item label="模板包">
                <t-select v-model="view.promptPack.value" :options="view.promptPackOptions.value" size="small" />
              </t-form-item>
              <t-form-item label="用途">
                <t-select v-model="view.useCase.value" :options="view.useCaseOptions.value" size="small" />
              </t-form-item>
              <t-form-item label="模板">
                <t-select v-model="view.templateId.value" :options="view.templateOptions.value" size="small" />
              </t-form-item>
              <t-form-item label="文字设计">
                <t-select v-model="view.textDesignMode.value" :options="view.illustrationTextDesignOptions" size="small" />
              </t-form-item>
            </div>

            <div class="detail-actions compact-actions">
              <t-button variant="text" size="small" @click="view.syncFromProject()">同步默认值</t-button>
            </div>
          </div>
        </template>

        <template #bottom>
          <div class="workspace-nav">
            <template v-if="view.summary.value">
              <details
                class="workspace-tree-group"
                :open="view.sidebarGroupOpen.illustrationEntities"
                @toggle="view.handleSidebarGroupToggle('illustrationEntities', $event)"
              >
                <summary>角色卡</summary>
                <div v-if="view.entityList.value.length === 0" class="workspace-tree-empty">当前没有角色卡。</div>
                <div v-else class="workspace-tree-list">
                  <div
                    v-for="item in view.orderedEntityList.value"
                    :key="item.id"
                    class="workspace-tree-item workspace-tree-item-action"
                    draggable="true"
                    @dragstart="view.handleTreeDragStart('entity', item.id)"
                    @dragover.prevent
                    @drop="view.handleTreeDrop('entity', item.id)"
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
                :open="view.sidebarGroupOpen.illustrationChapters"
                @toggle="view.handleSidebarGroupToggle('illustrationChapters', $event)"
              >
                <summary>章节插画</summary>
                <div v-if="view.chapterList.value.length === 0" class="workspace-tree-empty">当前没有章节。</div>
                <div v-else class="workspace-tree-list">
                  <button
                    v-for="item in view.orderedChapterList.value"
                    :key="item.id"
                    class="workspace-tree-item"
                    type="button"
                    draggable="true"
                    @dragstart="view.handleTreeDragStart('chapter', item.id)"
                    @dragover.prevent
                    @drop="view.handleTreeDrop('chapter', item.id)"
                    @click="view.openChapterIllustration(item.id)"
                  >
                    <strong>{{ item.title }}</strong>
                    <span>{{ item.id }}</span>
                  </button>
                </div>
              </details>
            </template>
            <div v-else class="workspace-free-note">
              <strong>自由模式</strong>
              <p>不绑定作品也可直接生图。结果只保存到工作台本地缓存，不写回项目协议。</p>
            </div>
            <details
              class="workspace-tree-group"
              :open="view.sidebarGroupOpen.illustrationHistory"
              @toggle="view.handleSidebarGroupToggle('illustrationHistory', $event)"
            >
              <summary>最近结果</summary>
              <div v-if="view.illustrationHistory.value.length === 0" class="workspace-tree-empty">{{ view.historyEmptyCopy.value }}</div>
              <div v-else class="workspace-tree-list">
                <button
                  v-for="item in view.illustrationHistory.value"
                  :key="item.id"
                  class="workspace-tree-item"
                  type="button"
                  @click="view.applyHistoryItem(item)"
                >
                  <strong>{{ item.target }}</strong>
                  <span>{{ item.sourceLabel }} · {{ item.mode }}</span>
                </button>
              </div>
            </details>
          </div>
        </template>
      </WorkbenchSidebarCard>
    </section>

    <section class="illustration-column illustration-column-editor">
      <WorkbenchPaneCard title="">
        <div class="illustration-editor-layout">
          <div class="illustration-form illustration-form-main illustration-template-workspace">
            <section class="workspace-block">
              <div class="template-panel-grid">
                <div class="template-panel">
                  <span class="template-panel-label">修饰词</span>
                  <div class="modifier-token-list">
                    <button
                      v-for="item in view.modifierOptions.value"
                      :key="item.id"
                      type="button"
                      class="modifier-token"
                      :class="{ 'is-active': view.modifierRefs.value.includes(item.id) }"
                      @click="view.toggleModifier(item.id)"
                    >
                      {{ item.label }}
                    </button>
                  </div>
                </div>
                <div class="template-panel">
                  <div class="modifier-token-list">
                    <button class="template-editor-link" type="button" @click="view.showAdvancedTemplateEditor.value = true">管理模板</button>
                  </div>
                </div>
              </div>
            </section>

            <section class="workspace-block">
              <div class="workspace-block-head">
                <strong class="workspace-block-title">提示词</strong>
                <span class="workspace-plain-meta">{{ view.promptSeedTitle.value }}</span>
              </div>
              <div class="prompt-block-grid">
                <div class="prompt-field">
                  <div class="prompt-field-head">
                    <label>正向提示词</label>
                    <button class="inline-link-button" type="button" @click="view.applySuggestedPrompt(true)">恢复基线</button>
                  </div>
                  <t-textarea
                    v-model="view.positivePrompt.value"
                    class="prompt-editor"
                    :autosize="{ minRows: 9, maxRows: 12 }"
                    placeholder="补充角色、动作、镜头、构图、环境和氛围。"
                  />
                </div>
                <div class="prompt-field">
                  <div class="prompt-field-head">
                    <label>负面提示词</label>
                    <button class="inline-link-button" type="button" @click="view.applySuggestedNegativePrompt(true)">恢复默认</button>
                  </div>
                  <t-textarea
                    v-model="view.negativePrompt.value"
                    :autosize="{ minRows: 5, maxRows: 7 }"
                    placeholder="例如：low quality, blurry, broken anatomy"
                  />
                </div>
              </div>
            </section>

            <section v-if="view.textDesignMode.value === 'designed'" class="workspace-block">
              <div class="workspace-block-head">
                <strong class="workspace-block-title">文字排版</strong>
              </div>
              <div class="prompt-block-grid">
                <div class="prompt-field">
                  <div class="prompt-field-head">
                    <label>标题</label>
                  </div>
                  <t-input v-model="view.titleText.value" placeholder="可留空，例如：明灯照骨" />
                </div>
                <div class="prompt-field">
                  <div class="prompt-field-head">
                    <label>副标题</label>
                  </div>
                  <t-input v-model="view.subtitleText.value" placeholder="可留空，例如：卷一 · 雾港裂痕" />
                </div>
                <div class="prompt-field">
                  <div class="prompt-field-head">
                    <label>介绍</label>
                  </div>
                  <t-textarea
                    v-model="view.bodyText.value"
                    :autosize="{ minRows: 3, maxRows: 5 }"
                    placeholder="可留空，例如：一个被命案撕开的雨夜港城。"
                  />
                </div>
                <div class="prompt-field">
                  <div class="prompt-field-head">
                    <label>字体气质</label>
                  </div>
                  <t-input v-model="view.fontStyleHint.value" placeholder="例如：墨明风题字、民国报刊字、冷峻无衬线" />
                </div>
              </div>
            </section>

            <section v-if="view.mode.value === 'image-to-image' || view.mode.value === 'inpaint'" class="workspace-block">
              <div class="workspace-block-head">
                <strong class="workspace-block-title">参考图</strong>
                <span class="workspace-plain-meta">可上传文件或复用已有路径</span>
              </div>
              <div class="asset-upload-grid">
                <label class="asset-upload-field">
                  <span>源图</span>
                  <input type="file" accept="image/*" @change="view.handleInputImageChange($event)" />
                  <div class="asset-preview-frame" :class="{ 'is-empty': !view.inputImageResolvedPreviewUrl.value }">
                    <img v-if="view.inputImageResolvedPreviewUrl.value" :src="view.inputImageResolvedPreviewUrl.value" alt="源图预览" />
                    <p v-else>未选择</p>
                  </div>
                  <div class="asset-upload-meta">
                    <strong>{{ view.inputImageDisplayName.value || "未选择" }}</strong>
                    <button v-if="view.inputImageDisplayName.value" class="inline-link-button" type="button" @click="view.clearInputAsset('input')">
                      清除
                    </button>
                  </div>
                </label>

                <label v-if="view.mode.value === 'inpaint'" class="asset-upload-field">
                  <span>蒙版</span>
                  <input type="file" accept="image/png,image/*" @change="view.handleMaskChange($event)" />
                  <div class="asset-preview-frame asset-preview-frame-mask" :class="{ 'is-empty': !view.maskResolvedPreviewUrl.value }">
                    <img v-if="view.maskResolvedPreviewUrl.value" :src="view.maskResolvedPreviewUrl.value" alt="蒙版预览" />
                    <p v-else>未选择</p>
                  </div>
                  <div class="asset-upload-meta">
                    <strong>{{ view.maskDisplayName.value || "未选择" }}</strong>
                    <button v-if="view.maskDisplayName.value" class="inline-link-button" type="button" @click="view.clearInputAsset('mask')">
                      清除
                    </button>
                  </div>
                </label>
              </div>
            </section>

            <section class="workspace-block workspace-block-run">
              <div class="workspace-block-head">
                <strong class="workspace-block-title">预览</strong>
                <span class="workspace-plain-meta">{{ view.currentTargetLabel.value }}</span>
              </div>
              <div class="workspace-inline-field">
                <label>命名</label>
                <t-input v-model="view.outputName.value" placeholder="留空使用默认命名" />
              </div>
              <div class="preview-grid">
                <div class="preview-pane">
                  <label>合成正向词</label>
                  <t-textarea :model-value="view.resolvedPromptPreview.value" :autosize="{ minRows: 7, maxRows: 10 }" readonly />
                </div>
                <div class="preview-pane">
                  <label>合成负向词</label>
                  <t-textarea :model-value="view.resolvedNegativePreview.value" :autosize="{ minRows: 7, maxRows: 10 }" readonly />
                </div>
              </div>
              <div class="run-status-row">
                <span>模板：{{ view.currentTemplateLabel.value }}</span>
                <span>修饰词：{{ view.modifierSummaryLabel.value }}</span>
                <span>命名：{{ view.outputNameStateLabel.value }}</span>
              </div>
              <div class="detail-actions compact-actions">
                <t-button theme="primary" :loading="view.submitting.value" @click="view.handleGenerate()">生成</t-button>
                <t-button variant="outline" :loading="view.submitting.value" @click="view.handleDryRun()">试运行</t-button>
              </div>
            </section>
          </div>

          <div class="illustration-form illustration-form-side illustration-template-side">
            <div v-if="view.illustrationSetupWarning.value" class="settings-warning-card illustration-settings-warning">
              <strong>生成前需要先补齐配置</strong>
              <p>{{ view.illustrationSetupWarning.value }}</p>
            </div>

            <div class="workspace-block illustration-result-block">
              <div class="workspace-block-head">
                <strong class="workspace-block-title">结果</strong>
                <span class="workspace-plain-meta">{{ view.resultSourceLabel.value }}</span>
              </div>
              <button
                v-if="view.resultPreviewUrl.value"
                class="asset-preview-frame asset-preview-frame-result asset-preview-trigger"
                type="button"
                @click="view.openResultLightbox()"
              >
                <img :src="view.resultPreviewUrl.value" alt="生成结果预览" />
                <span class="asset-preview-zoom-hint">点击放大查看</span>
              </button>
              <p v-else class="detail-copy">执行后显示结果。</p>
              <div v-if="view.primaryResultExportItem.value" class="result-export-actions">
                <div class="result-export-actions-main">
                  <a
                    class="result-export-link result-export-link-primary"
                    :href="view.primaryResultExportItem.value.href"
                    :download="view.primaryResultExportItem.value.downloadName"
                    target="_blank"
                    rel="noreferrer"
                  >
                    导出主图
                  </a>
                  <t-button variant="outline" size="small" @click="view.handleOpenResultFolder()">打开文件夹</t-button>
                </div>
                <span class="workspace-plain-meta">{{ view.resultSummary.value?.mode || view.mode.value }}</span>
              </div>
            </div>

            <div v-if="view.resultSummary.value" class="workspace-block result-block">
              <div class="result-meta">
                <span>{{ view.resultSummary.value.mode }}</span>
                <span>{{ view.resultSummary.value.target }}</span>
                <span>{{ view.resultPackLabel.value }}</span>
              </div>
              <strong class="result-path">{{ view.resultSummary.value.output }}</strong>
              <p v-if="view.resultArtifactFolder.value" class="result-folder">{{ view.resultArtifactFolder.value }}</p>
              <p class="result-text">{{ view.resultSummary.value.text }}</p>
              <div class="result-facts">
                <span>{{ view.resultTemplateLabel.value }}</span>
                <span>{{ view.resultModifierLabel.value }}</span>
                <span>{{ view.negativePromptStateLabel.value }}</span>
              </div>
              <div v-if="view.resultExportItems.value.length > 1" class="result-export-list">
                <a
                  v-for="item in view.resultExportItems.value"
                  :key="item.id"
                  class="result-export-link"
                  :href="item.href"
                  :download="item.downloadName"
                  target="_blank"
                  rel="noreferrer"
                >
                  {{ item.label }}
                </a>
              </div>
            </div>
          </div>
        </div>
      </WorkbenchPaneCard>
    </section>

    <PromptPackEditorDrawer
      v-if="view.showAdvancedTemplateEditor.value"
      v-model:visible="view.showAdvancedTemplateEditor.value"
      v-model:file-name="view.promptPackDraftFileName.value"
      v-model:set-as-default="view.promptPackSetAsDefault.value"
      v-model:template-id="view.promptPackDraftTemplateId.value"
      :summary-exists="Boolean(view.summary.value)"
      :prompt-pack-draft-state-label="view.promptPackDraftStateLabel.value"
      :current-pack-source-label="view.currentPackSourceLabel.value"
      :prompt-pack-draft="view.promptPackDraft.value"
      :prompt-pack-draft-template="view.promptPackDraftTemplate.value"
      :prompt-pack-draft-negative-policy-options="view.promptPackDraftNegativePolicyOptions.value"
      :prompt-pack-draft-commercial-policy-options="view.promptPackDraftCommercialPolicyOptions.value"
      :prompt-pack-library-error="view.promptPackLibraryError.value"
      :saving-prompt-pack-library="view.savingPromptPackLibrary.value"
      @new-pack="view.startNewPromptPackDraft()"
      @copy-current="view.startDraftFromSelectedPack()"
      @add-template="view.addPromptPackDraftTemplate()"
      @remove-template="view.removePromptPackDraftTemplate"
      @add-modifier="view.addPromptPackDraftModifier()"
      @remove-modifier="view.removePromptPackDraftModifier"
      @add-negative-policy="view.addPromptPackDraftNegativePolicy()"
      @remove-negative-policy="view.removePromptPackDraftNegativePolicy"
      @add-commercial-policy="view.addPromptPackDraftCommercialPolicy()"
      @remove-commercial-policy="view.removePromptPackDraftCommercialPolicy"
      @reset="view.resetPromptPackDraft()"
      @save="view.handleSavePromptPackDraft()"
    />

    <div
      v-if="view.resultLightboxVisible.value && view.resultPreviewUrl.value"
      class="result-lightbox"
      role="dialog"
      aria-modal="true"
      @click.self="view.closeResultLightbox()"
    >
      <div class="result-lightbox-panel">
        <div class="result-lightbox-head">
          <strong>{{ view.resultSummary.value?.target || "生成结果" }}</strong>
          <button class="result-lightbox-close" type="button" @click="view.closeResultLightbox()">关闭</button>
        </div>
        <div class="result-lightbox-stage">
          <img :src="view.resultPreviewUrl.value" alt="生成结果放大预览" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineAsyncComponent } from "vue";

import WorkbenchPaneCard from "@/components/WorkbenchPaneCard.vue";
import WorkbenchSidebarCard from "@/components/WorkbenchSidebarCard.vue";
import { TButton } from "@/tdesign/button";
import { TFormItem } from "@/tdesign/form";
import { TInput } from "@/tdesign/input";
import { TRadioButton, TRadioGroup } from "@/tdesign/radio";
import { TSelect } from "@/tdesign/select";
import { TTextarea } from "@/tdesign/textarea";

defineProps<{
  view: any;
}>();

const PromptPackEditorDrawer = defineAsyncComponent(() => import("@/components/PromptPackEditorDrawer.vue"));
</script>

<style scoped>
.illustration-grid-separated {
  display: grid;
  grid-template-columns: var(--workbench-side-width) minmax(0, 1fr);
  gap: 0;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.illustration-column {
  display: grid;
  height: 100%;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
}

.illustration-column-side {
  grid-template-rows: minmax(0, 1fr);
  width: var(--workbench-side-width);
  min-width: var(--workbench-side-width);
  max-width: var(--workbench-side-width);
  background: var(--surface-side);
}

.illustration-column-editor {
  grid-template-rows: minmax(0, 1fr);
  min-width: 0;
  background: var(--surface);
}

.workspace-explorer {
  display: grid;
  gap: 8px;
}

.workspace-illustration-controls {
  display: grid;
  gap: 10px;
}

.workspace-parameter-grid {
  display: grid;
  gap: 4px;
}

.workspace-parameter-grid :deep(.t-form__item) {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  align-items: center;
  gap: 8px;
  margin-bottom: 0;
}

.workspace-parameter-grid :deep(.t-form__label) {
  padding-right: 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.2;
}

.workspace-parameter-grid :deep(.t-form__label > label) {
  display: block;
  white-space: nowrap;
}

.workspace-parameter-grid :deep(.t-form__controls),
.workspace-parameter-grid :deep(.t-form__controls-content),
.workspace-parameter-grid :deep(.t-select) {
  min-width: 0;
  width: 100%;
}

.workspace-parameter-grid :deep(.t-radio-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.workspace-parameter-grid :deep(.t-radio-button) {
  min-width: 0;
}

.workspace-explorer-head,
.workspace-section-actions,
.result-meta,
.result-facts {
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

.workspace-free-note {
  display: grid;
  gap: 6px;
  padding: 8px 0 0;
}

.workspace-free-note p {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}

.result-export-actions,
.result-export-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.result-export-actions-main {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.result-export-actions {
  justify-content: space-between;
  margin-top: 10px;
}

.result-export-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid var(--border);
  color: var(--text);
  background: var(--surface-elevated);
  font-size: 12px;
  font-weight: 600;
  text-decoration: none;
}

.result-export-link:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.result-export-link-primary {
  background: color-mix(in srgb, var(--accent) 16%, var(--surface-elevated));
  border-color: color-mix(in srgb, var(--accent) 30%, var(--border));
}

.result-folder {
  margin: 6px 0 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.4;
  word-break: break-all;
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
.workspace-tree-empty {
  color: var(--muted);
  font-size: 11px;
}

.workspace-tree-item:hover,
.workspace-tree-item.is-active {
  border-left-color: rgba(0, 82, 217, 0.45);
  background: rgba(255, 255, 255, 0.58);
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

.workspace-mini-action,
.inline-link-button,
.template-editor-link {
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--accent);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.workspace-section-actions {
  justify-content: flex-end;
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

.detail-copy,
.result-text {
  color: var(--muted);
}

.illustration-editor-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.85fr);
  gap: 0;
  min-height: 0;
  flex: 1;
}

.illustration-form {
  min-height: 0;
  overflow: auto;
  padding: 10px;
}

.illustration-form-main,
.illustration-form-side {
  display: grid;
  align-content: start;
  gap: 12px;
}

.illustration-template-workspace,
.illustration-template-side {
  gap: 10px;
}

.illustration-template-workspace :deep(.t-input__wrap),
.illustration-template-workspace :deep(.t-textarea__inner),
.illustration-template-workspace :deep(.t-select__wrap),
.illustration-template-workspace :deep(.t-radio-button),
.illustration-template-side :deep(.t-input__wrap),
.illustration-template-side :deep(.t-textarea__inner),
.illustration-template-side :deep(.t-select__wrap),
.illustration-template-side :deep(.t-radio-button) {
  border-radius: 2px !important;
}

.workspace-block {
  display: grid;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.84);
}

.workspace-block-run {
  gap: 12px;
}

.workspace-block-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(31, 35, 41, 0.08);
}

.workspace-block-title {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.workspace-plain-meta,
.template-panel-label,
.run-status-row,
.preview-pane label,
.workspace-inline-field label,
.prompt-field-head label,
.asset-upload-field > span {
  color: var(--muted);
  font-size: 12px;
}

.workspace-inline-field {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.workspace-inline-field :deep(.t-select),
.workspace-inline-field :deep(.t-input),
.workspace-inline-field :deep(.t-radio-group) {
  width: 100%;
  min-width: 0;
}

.workspace-inline-field :deep(.t-radio-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.template-panel,
.prompt-field,
.preview-pane {
  display: grid;
  gap: 8px;
}

.modifier-token-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.modifier-token {
  padding: 5px 10px;
  border: 1px solid var(--line);
  border-radius: 2px;
  background: #fff;
  color: var(--text);
  font: inherit;
  font-size: 12px;
  line-height: 1.4;
  cursor: pointer;
}

.modifier-token:hover {
  border-color: rgba(0, 82, 217, 0.35);
  background: #f7faff;
}

.modifier-token.is-active {
  border-color: var(--accent);
  background: rgba(0, 82, 217, 0.08);
  color: #003f9f;
}

.template-panel-grid,
.prompt-block-grid,
.preview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.prompt-field-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.prompt-editor,
.preview-pane :deep(.t-textarea) {
  min-height: 100%;
}

.run-status-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  padding-top: 2px;
  border-top: 1px solid rgba(31, 35, 41, 0.06);
}

.result-block {
  gap: 6px;
}

.asset-upload-grid {
  display: grid;
  gap: 10px;
}

.asset-upload-field {
  display: grid;
  gap: 8px;
  font-size: 12px;
  color: var(--muted);
}

.asset-upload-field input[type="file"] {
  width: 100%;
  font: inherit;
}

.asset-upload-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 18px;
}

.asset-upload-meta strong,
.result-path {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.asset-upload-meta strong {
  flex: 1;
  font-size: 12px;
  color: var(--text);
}

.asset-preview-frame {
  display: grid;
  place-items: center;
  min-height: 152px;
  border: 1px solid var(--line);
  background: #f7f9fb;
  overflow: hidden;
}

.asset-preview-frame img {
  display: block;
  width: 100%;
  height: 100%;
  max-height: 340px;
  object-fit: contain;
  background: #f2f4f7;
}

.asset-preview-frame p {
  margin: 0;
  padding: 0 16px;
  text-align: center;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}

.asset-preview-frame-mask img {
  min-height: 152px;
}

.asset-preview-frame-result {
  min-height: 220px;
  background: #eef3f8;
}

.asset-preview-trigger {
  position: relative;
  width: 100%;
  border: 0;
  cursor: zoom-in;
  text-align: left;
}

.asset-preview-zoom-hint {
  position: absolute;
  right: 12px;
  bottom: 12px;
  padding: 4px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--sidebar-bg) 72%, transparent);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.result-meta {
  justify-content: flex-start;
  color: var(--muted);
  font-size: 12px;
}

.result-facts {
  justify-content: flex-start;
  flex-wrap: wrap;
  color: var(--muted);
  font-size: 12px;
}

.result-text {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.compact-actions {
  padding-top: 2px;
}

.inline-error {
  margin: 0;
  color: #c93537;
}

.settings-warning-card {
  display: grid;
  gap: 6px;
  padding: 10px 12px;
  border: 1px solid #efd29d;
  background: #fffaf0;
}

.settings-warning-card strong {
  color: #8f5a00;
}

.settings-warning-card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.5;
}

.result-lightbox {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: grid;
  place-items: center;
  padding: 24px;
  background: color-mix(in srgb, #08111d 82%, transparent);
  backdrop-filter: blur(8px);
}

.result-lightbox-panel {
  display: grid;
  gap: 12px;
  width: min(96vw, 1440px);
  max-height: 92vh;
  padding: 16px;
  border: 1px solid color-mix(in srgb, var(--accent) 20%, var(--border));
  border-radius: 20px;
  background: color-mix(in srgb, var(--surface) 92%, #08111d);
  box-shadow: 0 28px 90px rgba(3, 10, 18, 0.42);
}

.result-lightbox-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.result-lightbox-close {
  min-height: 32px;
  padding: 0 12px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--surface-elevated);
  color: var(--text);
  cursor: pointer;
}

.result-lightbox-stage {
  display: grid;
  place-items: center;
  min-height: 0;
  overflow: auto;
}

.result-lightbox-stage img {
  display: block;
  max-width: 100%;
  max-height: calc(92vh - 88px);
  object-fit: contain;
  border-radius: 14px;
}

@media (max-width: 1440px) {
  .illustration-grid-separated {
    grid-template-columns: var(--workbench-side-width) minmax(0, 1fr);
  }
}

@media (max-width: 1180px) {
  .illustration-grid-separated,
  .workspace-project-import-row,
  .workspace-project-create-row,
  .template-panel-grid,
  .prompt-block-grid,
  .preview-grid {
    grid-template-columns: 1fr;
  }

  .illustration-editor-layout {
    grid-template-columns: minmax(0, 1fr) minmax(260px, 0.78fr);
  }

  .illustration-grid-separated {
    overflow: visible;
  }

  .illustration-column,
  .illustration-column-editor,
  .illustration-form,
  .workspace-nav {
    overflow: visible;
  }

  .illustration-column-side {
    grid-template-rows: auto;
    width: auto;
    min-width: 0;
    max-width: none;
  }
}

@media (max-width: 1024px) {
  .illustration-editor-layout {
    grid-template-columns: 1fr;
  }

  .illustration-form-side {
    order: -1;
  }

  .illustration-result-block,
  .result-block,
  .illustration-settings-warning {
    order: -1;
  }
}

@media (max-width: 900px) {
  .workspace-parameter-grid :deep(.t-form__item) {
    grid-template-columns: 1fr;
    gap: 6px;
  }

  .workspace-parameter-grid :deep(.t-form__label) {
    font-size: 11px;
  }

  .workspace-tree-item {
    padding-left: 12px;
  }

  .workspace-block,
  :deep(.workbench-sidebar-section) {
    padding-left: 8px;
    padding-right: 8px;
  }

  .workspace-block-head,
  .run-status-row {
    flex-wrap: wrap;
  }
}
</style>
