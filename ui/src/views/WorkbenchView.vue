<template>
  <div class="workbench-shell">
    <div v-if="workspaceMode === 'review'" class="review-grid">
      <section class="review-column review-column-nav">
        <WorkbenchSidebarCard title="">
          <template #top>
            <div class="workspace-explorer">
              <div class="workspace-explorer-head">
                <strong class="workspace-explorer-label">项目</strong>
                <div class="workspace-section-actions">
                  <t-button variant="text" size="small" @click="showProjectSetup = !showProjectSetup">项目</t-button>
                  <t-button variant="text" size="small" @click="refreshProjects">刷新</t-button>
                </div>
              </div>
              <t-select
                :model-value="selectedRoot"
                :options="explorerProjectOptions"
                placeholder="选择项目"
                clearable
                @update:model-value="handleProjectSelect(String($event ?? ''))"
              />
              <div v-if="selectedRoot" class="workspace-inline-switch">
                <t-button variant="text" size="small" @click="leaveProject">退出项目</t-button>
              </div>
              <div v-if="showProjectSetup" class="workspace-project-create workspace-project-create-inline">
                <div class="workspace-project-switcher" role="tablist" aria-label="项目操作">
                  <button
                    class="workspace-project-switcher-item"
                    :class="{ 'is-active': projectPanelMode === 'import' }"
                    type="button"
                    @click="projectPanelMode = 'import'"
                  >
                    导入
                  </button>
                  <button
                    class="workspace-project-switcher-item"
                    :class="{ 'is-active': projectPanelMode === 'create' }"
                    type="button"
                    @click="projectPanelMode = 'create'"
                  >
                    新建
                  </button>
                </div>
                <template v-if="projectPanelMode === 'import'">
                  <div class="workspace-project-import-row">
                    <t-input v-model="importProjectRootDraft" placeholder="选择已有项目根目录" />
                    <t-button variant="outline" size="small" :loading="selectingProjectFolder" @click="handleSelectProjectFolder">
                      选择目录
                    </t-button>
                    <t-button variant="outline" size="small" :loading="creatingProject" @click="handleImportProject">
                      导入项目
                    </t-button>
                  </div>
                </template>
                <template v-else>
                  <t-input v-model="projectTitleDraft" placeholder="项目标题" />
                  <div class="workspace-project-create-row">
                    <t-input v-model="projectGenreDraft" placeholder="题材" />
                    <t-input v-model="projectDirectoryDraft" placeholder="目录名" />
                  </div>
                  <div class="detail-actions compact-actions">
                    <t-button theme="primary" size="small" :loading="creatingProject" @click="handleCreateProject">
                      创建项目
                    </t-button>
                  </div>
                </template>
              </div>
              <p v-if="sidebarMessage" class="inline-error">{{ sidebarMessage }}</p>
            </div>
          </template>

          <template #bottom>
            <div class="workspace-nav">
              <div v-if="!summary" class="empty-pane workspace-empty-compact">先选择一个项目。</div>

              <details
                class="workspace-tree-group"
                :open="sidebarGroupOpen.reviewChapters"
                @toggle="handleSidebarGroupToggle('reviewChapters', $event)"
              >
                <summary>章节</summary>
                <div v-if="chapterList.length === 0" class="workspace-tree-empty">当前没有可用章节。</div>
                <div v-else class="workspace-tree-list">
                  <button
                    v-for="item in orderedChapterList"
                    :key="item.id"
                    class="workspace-tree-item"
                    :class="{ 'is-active': item.id === selectedChapter?.id }"
                    type="button"
                    draggable="true"
                    @dragstart="handleTreeDragStart('chapter', item.id)"
                    @dragover.prevent
                    @drop="handleTreeDrop('chapter', item.id)"
                    @click="selectedChapter = item"
                  >
                    <strong>{{ item.title }}</strong>
                    <span>{{ item.id }}</span>
                  </button>
                </div>
              </details>

              <details
                class="workspace-tree-group"
                :open="sidebarGroupOpen.reviewEntities"
                @toggle="handleSidebarGroupToggle('reviewEntities', $event)"
              >
                <summary>角色卡</summary>
                <div v-if="entityList.length === 0" class="workspace-tree-empty">当前没有角色卡。</div>
                <div v-else class="workspace-tree-list">
                  <div
                    v-for="item in orderedEntityList"
                    :key="item.id"
                    class="workspace-tree-item workspace-tree-item-action"
                    draggable="true"
                    @dragstart="handleTreeDragStart('entity', item.id)"
                    @dragover.prevent
                    @drop="handleTreeDrop('entity', item.id)"
                  >
                    <div class="workspace-tree-item-copy">
                      <strong>{{ item.name }}</strong>
                      <span>{{ item.type || "entity" }}</span>
                    </div>
                    <button class="workspace-mini-action" type="button" @click.stop="openEntityIllustration(item.id)">
                      设定图
                    </button>
                  </div>
                </div>
              </details>

              <details
                class="workspace-tree-group"
                :open="sidebarGroupOpen.reviewReference"
                @toggle="handleSidebarGroupToggle('reviewReference', $event)"
              >
                <summary>资料</summary>
                <div class="workspace-tree-list">
                  <div class="workspace-tree-item workspace-tree-item-static">
                    <strong>世界设定</strong>
                    <span>待接入</span>
                  </div>
                  <div class="workspace-tree-item workspace-tree-item-static">
                    <strong>卷结构</strong>
                    <span>待接入</span>
                  </div>
                  <div class="workspace-tree-item workspace-tree-item-static">
                    <strong>审查包</strong>
                    <span>待接入</span>
                  </div>
                </div>
              </details>
            </div>
          </template>
        </WorkbenchSidebarCard>
      </section>

      <section class="review-column review-column-main">
        <WorkbenchPaneCard title="">
            <template v-if="selectedChapter">
              <div class="review-workspace">
                <section class="review-editor-pane">
                  <article class="chapter-content">
                    {{ selectedChapter.content || "当前章节还没有可展示正文。" }}
                  </article>
                </section>

                <aside class="review-inspector-pane">
                  <div class="focus-section focus-section-compact">
                    <strong class="section-title">问题</strong>
                    <div class="issue-list">
                      <div v-for="issue in visibleIssues" :key="issue" class="issue-chip">
                        {{ issue }}
                      </div>
                    </div>
                  </div>

                  <div class="focus-section focus-section-compact">
                    <strong class="section-title">动作</strong>
                    <div class="action-stack compact-stack">
                      <article v-for="item in actionQueue" :key="item.title" class="action-item compact-item">
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
                      <div v-for="entry in protocolEntries" :key="entry.label" class="fact-item compact-fact">
                        <span>{{ entry.label }}</span>
                        <strong>{{ entry.value }}</strong>
                      </div>
                    </div>
                  </div>
                </aside>
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

    <div v-else class="illustration-grid-separated">
      <section class="illustration-column illustration-column-side">
        <WorkbenchSidebarCard title="">
          <template #top>
            <div class="workspace-explorer">
              <div class="workspace-explorer-head">
                <strong class="workspace-explorer-label">项目</strong>
                <div class="workspace-section-actions">
                  <t-button variant="text" size="small" @click="showProjectSetup = !showProjectSetup">项目</t-button>
                  <t-button variant="text" size="small" @click="refreshProjects">刷新</t-button>
                </div>
              </div>
              <t-select
                :model-value="selectedRoot"
                :options="explorerProjectOptions"
                placeholder="选择项目"
                clearable
                @update:model-value="handleProjectSelect(String($event ?? ''))"
              />
              <div v-if="selectedRoot" class="workspace-inline-switch">
                <t-button variant="text" size="small" @click="leaveProject">自由模式</t-button>
              </div>
              <div v-if="showProjectSetup" class="workspace-project-create workspace-project-create-inline">
                <div class="workspace-project-switcher" role="tablist" aria-label="项目操作">
                  <button
                    class="workspace-project-switcher-item"
                    :class="{ 'is-active': projectPanelMode === 'import' }"
                    type="button"
                    @click="projectPanelMode = 'import'"
                  >
                    导入
                  </button>
                  <button
                    class="workspace-project-switcher-item"
                    :class="{ 'is-active': projectPanelMode === 'create' }"
                    type="button"
                    @click="projectPanelMode = 'create'"
                  >
                    新建
                  </button>
                </div>
                <template v-if="projectPanelMode === 'import'">
                  <div class="workspace-project-import-row">
                    <t-input v-model="importProjectRootDraft" placeholder="选择已有项目根目录" />
                    <t-button variant="outline" size="small" :loading="selectingProjectFolder" @click="handleSelectProjectFolder">
                      选择目录
                    </t-button>
                    <t-button variant="outline" size="small" :loading="creatingProject" @click="handleImportProject">
                      导入项目
                    </t-button>
                  </div>
                </template>
                <template v-else>
                  <t-input v-model="projectTitleDraft" placeholder="项目标题" />
                  <div class="workspace-project-create-row">
                    <t-input v-model="projectGenreDraft" placeholder="题材" />
                    <t-input v-model="projectDirectoryDraft" placeholder="目录名" />
                  </div>
                  <div class="detail-actions compact-actions">
                    <t-button theme="primary" size="small" :loading="creatingProject" @click="handleCreateProject">
                      创建项目
                    </t-button>
                  </div>
                </template>
              </div>
              <p v-if="sidebarMessage" class="inline-error">{{ sidebarMessage }}</p>
              <div v-if="illustrationSetupWarning" class="settings-warning-card">
                <strong>生图配置未完成</strong>
                <p>{{ illustrationSetupWarning }}</p>
                <t-button size="small" theme="primary" @click="emit('open-settings')">去设置</t-button>
              </div>
            </div>
          </template>

          <template #middle>
            <div class="workspace-illustration-controls">
              <div class="workspace-parameter-grid">
                <t-form-item label="目标类型">
                  <t-radio-group v-model="targetType" size="small">
                    <t-radio-button value="entity">角色</t-radio-button>
                    <t-radio-button value="chapter">场景</t-radio-button>
                  </t-radio-group>
                </t-form-item>
                <t-form-item :label="isProjectBound ? (targetType === 'entity' ? '角色' : '章节') : '目标'">
                  <t-select v-if="isProjectBound" v-model="targetId" :options="targetOptions" size="small" />
                  <t-input
                    v-else
                    v-model="manualTargetName"
                    size="small"
                    :placeholder="targetType === 'entity' ? '例如：白发女剑修' : '例如：雨夜屋顶对峙'"
                  />
                </t-form-item>
                <t-form-item label="模式">
                  <t-radio-group v-model="mode" size="small">
                    <t-radio-button value="text-to-image">文生图</t-radio-button>
                    <t-radio-button value="image-to-image">图生图</t-radio-button>
                    <t-radio-button value="inpaint">重绘</t-radio-button>
                  </t-radio-group>
                </t-form-item>
                <t-form-item label="模板包">
                  <t-select v-model="promptPack" :options="promptPackOptions" size="small" />
                </t-form-item>
                <t-form-item label="用途">
                  <t-select v-model="useCase" :options="useCaseOptions" size="small" />
                </t-form-item>
                <t-form-item label="模板">
                  <t-select v-model="templateId" :options="templateOptions" size="small" />
                </t-form-item>
                <t-form-item label="文字设计">
                  <t-select v-model="textDesignMode" :options="ILLUSTRATION_TEXT_DESIGN_OPTIONS" size="small" />
                </t-form-item>
              </div>

              <div class="detail-actions compact-actions">
                <t-button variant="text" size="small" @click="syncFromProject">同步默认值</t-button>
              </div>
            </div>
          </template>

          <template #bottom>
            <div class="workspace-nav">
              <template v-if="summary">
                <details
                  class="workspace-tree-group"
                  :open="sidebarGroupOpen.illustrationEntities"
                  @toggle="handleSidebarGroupToggle('illustrationEntities', $event)"
                >
                  <summary>角色卡</summary>
                  <div v-if="entityList.length === 0" class="workspace-tree-empty">当前没有角色卡。</div>
                  <div v-else class="workspace-tree-list">
                    <div
                      v-for="item in orderedEntityList"
                      :key="item.id"
                      class="workspace-tree-item workspace-tree-item-action"
                      draggable="true"
                      @dragstart="handleTreeDragStart('entity', item.id)"
                      @dragover.prevent
                      @drop="handleTreeDrop('entity', item.id)"
                    >
                      <div class="workspace-tree-item-copy">
                        <strong>{{ item.name }}</strong>
                        <span>{{ item.type || "entity" }}</span>
                      </div>
                      <button class="workspace-mini-action" type="button" @click.stop="openEntityIllustration(item.id)">
                        设定图
                      </button>
                    </div>
                  </div>
                </details>

                <details
                  class="workspace-tree-group"
                  :open="sidebarGroupOpen.illustrationChapters"
                  @toggle="handleSidebarGroupToggle('illustrationChapters', $event)"
                >
                  <summary>章节插画</summary>
                  <div v-if="chapterList.length === 0" class="workspace-tree-empty">当前没有章节。</div>
                  <div v-else class="workspace-tree-list">
                    <button
                      v-for="item in orderedChapterList"
                      :key="item.id"
                      class="workspace-tree-item"
                      type="button"
                      draggable="true"
                      @dragstart="handleTreeDragStart('chapter', item.id)"
                      @dragover.prevent
                      @drop="handleTreeDrop('chapter', item.id)"
                      @click="openChapterIllustration(item.id)"
                    >
                      <strong>{{ item.title }}</strong>
                      <span>{{ item.id }}</span>
                    </button>
                  </div>
                </details>

                <details
                  class="workspace-tree-group"
                  :open="sidebarGroupOpen.illustrationHistory"
                  @toggle="handleSidebarGroupToggle('illustrationHistory', $event)"
                >
                  <summary>最近结果</summary>
                  <div v-if="illustrationHistory.length === 0" class="workspace-tree-empty">当前项目还没有插画记录。</div>
                  <div v-else class="workspace-tree-list">
                    <button
                      v-for="item in illustrationHistory"
                      :key="item.id"
                      class="workspace-tree-item"
                      type="button"
                      @click="applyHistoryItem(item.raw)"
                    >
                      <strong>{{ item.target }}</strong>
                      <span>{{ item.mode }}</span>
                    </button>
                  </div>
                </details>
              </template>
              <div v-else class="workspace-free-note">
                <strong>自由模式</strong>
                <p>不绑定作品也可直接生图。结果只保存到工作台本地缓存，不写回项目协议。</p>
              </div>
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
                          v-for="item in modifierOptions"
                          :key="item.id"
                          type="button"
                          class="modifier-token"
                          :class="{ 'is-active': modifierRefs.includes(item.id) }"
                          @click="toggleModifier(item.id)"
                        >
                          {{ item.label }}
                        </button>
                      </div>
                    </div>
                    <div class="template-panel">
                      <div class="modifier-token-list">
                        <button class="template-editor-link" type="button" @click="showAdvancedTemplateEditor = true">管理模板</button>
                      </div>
                    </div>
                  </div>
                </section>

                <section class="workspace-block">
                  <div class="workspace-block-head">
                    <strong class="workspace-block-title">提示词</strong>
                    <span class="workspace-plain-meta">{{ promptSeedTitle }}</span>
                  </div>
                  <div class="prompt-block-grid">
                    <div class="prompt-field">
                      <div class="prompt-field-head">
                        <label>正向提示词</label>
                        <button class="inline-link-button" type="button" @click="applySuggestedPrompt(true)">恢复基线</button>
                      </div>
                      <t-textarea
                        v-model="positivePrompt"
                        class="prompt-editor"
                        :autosize="{ minRows: 9, maxRows: 12 }"
                        placeholder="补充角色、动作、镜头、构图、环境和氛围。"
                      />
                    </div>
                    <div class="prompt-field">
                      <div class="prompt-field-head">
                        <label>负面提示词</label>
                        <button class="inline-link-button" type="button" @click="applySuggestedNegativePrompt(true)">恢复默认</button>
                      </div>
                      <t-textarea
                        v-model="negativePrompt"
                        :autosize="{ minRows: 5, maxRows: 7 }"
                        placeholder="例如：low quality, blurry, broken anatomy"
                      />
                    </div>
                  </div>
                </section>

                <section v-if="textDesignMode === 'designed'" class="workspace-block">
                  <div class="workspace-block-head">
                    <strong class="workspace-block-title">文字排版</strong>
                  </div>
                  <div class="prompt-block-grid">
                    <div class="prompt-field">
                      <div class="prompt-field-head">
                        <label>标题</label>
                      </div>
                      <t-input v-model="titleText" placeholder="可留空，例如：明灯照骨" />
                    </div>
                    <div class="prompt-field">
                      <div class="prompt-field-head">
                        <label>副标题</label>
                      </div>
                      <t-input v-model="subtitleText" placeholder="可留空，例如：卷一 · 雾港裂痕" />
                    </div>
                    <div class="prompt-field">
                      <div class="prompt-field-head">
                        <label>介绍</label>
                      </div>
                      <t-textarea
                        v-model="bodyText"
                        :autosize="{ minRows: 3, maxRows: 5 }"
                        placeholder="可留空，例如：一个被命案撕开的雨夜港城。"
                      />
                    </div>
                    <div class="prompt-field">
                      <div class="prompt-field-head">
                        <label>字体气质</label>
                      </div>
                      <t-input v-model="fontStyleHint" placeholder="例如：墨明风题字、民国报刊字、冷峻无衬线" />
                    </div>
                  </div>
                </section>

                <section v-if="mode === 'image-to-image' || mode === 'inpaint'" class="workspace-block">
                  <div class="workspace-block-head">
                    <strong class="workspace-block-title">参考图</strong>
                    <span class="workspace-plain-meta">可上传文件或复用已有路径</span>
                  </div>
                  <div class="asset-upload-grid">
                    <label class="asset-upload-field">
                      <span>源图</span>
                      <input type="file" accept="image/*" @change="handleInputImageChange" />
                      <div class="asset-preview-frame" :class="{ 'is-empty': !inputImageResolvedPreviewUrl }">
                        <img v-if="inputImageResolvedPreviewUrl" :src="inputImageResolvedPreviewUrl" alt="源图预览" />
                        <p v-else>未选择</p>
                      </div>
                      <div class="asset-upload-meta">
                        <strong>{{ inputImageDisplayName || "未选择" }}</strong>
                        <button
                          v-if="inputImageDisplayName"
                          class="inline-link-button"
                          type="button"
                          @click="clearInputAsset('input')"
                        >
                          清除
                        </button>
                      </div>
                    </label>

                    <label v-if="mode === 'inpaint'" class="asset-upload-field">
                      <span>蒙版</span>
                      <input type="file" accept="image/png,image/*" @change="handleMaskChange" />
                      <div class="asset-preview-frame asset-preview-frame-mask" :class="{ 'is-empty': !maskResolvedPreviewUrl }">
                        <img v-if="maskResolvedPreviewUrl" :src="maskResolvedPreviewUrl" alt="蒙版预览" />
                        <p v-else>未选择</p>
                      </div>
                      <div class="asset-upload-meta">
                        <strong>{{ maskDisplayName || "未选择" }}</strong>
                        <button
                          v-if="maskDisplayName"
                          class="inline-link-button"
                          type="button"
                          @click="clearInputAsset('mask')"
                        >
                          清除
                        </button>
                      </div>
                    </label>
                  </div>
                </section>

                <section class="workspace-block workspace-block-run">
                  <div class="workspace-block-head">
                    <strong class="workspace-block-title">预览</strong>
                    <span class="workspace-plain-meta">{{ currentTargetLabel }}</span>
                  </div>
                  <div class="workspace-inline-field">
                    <label>命名</label>
                    <t-input v-model="outputName" placeholder="留空使用默认命名" />
                  </div>
                  <div class="preview-grid">
                    <div class="preview-pane">
                      <label>合成正向词</label>
                      <t-textarea :model-value="resolvedPromptPreview" :autosize="{ minRows: 7, maxRows: 10 }" readonly />
                    </div>
                    <div class="preview-pane">
                      <label>合成负向词</label>
                      <t-textarea :model-value="resolvedNegativePreview" :autosize="{ minRows: 7, maxRows: 10 }" readonly />
                    </div>
                  </div>
                  <div class="run-status-row">
                    <span>模板：{{ currentTemplateLabel }}</span>
                    <span>修饰词：{{ modifierSummaryLabel }}</span>
                    <span>命名：{{ outputNameStateLabel }}</span>
                  </div>
                  <div class="detail-actions compact-actions">
                    <t-button theme="primary" :loading="submitting" @click="handleGenerate">生成</t-button>
                    <t-button variant="outline" :loading="submitting" @click="handleDryRun">试运行</t-button>
                  </div>
                </section>
              </div>

              <div class="illustration-form illustration-form-side illustration-template-side">
                <div v-if="illustrationSetupWarning" class="settings-warning-card illustration-settings-warning">
                  <strong>生成前需要先补齐配置</strong>
                  <p>{{ illustrationSetupWarning }}</p>
                </div>

                <div class="workspace-block illustration-result-block">
                  <div class="workspace-block-head">
                    <strong class="workspace-block-title">结果</strong>
                    <span class="workspace-plain-meta">{{ resultSummary?.mode || mode }}</span>
                  </div>
                  <div v-if="resultPreviewUrl" class="asset-preview-frame asset-preview-frame-result">
                    <img :src="resultPreviewUrl" alt="生成结果预览" />
                  </div>
                  <p v-else class="detail-copy">执行后显示结果。</p>
                </div>

                <div v-if="resultSummary" class="workspace-block result-block">
                  <div class="result-meta">
                    <span>{{ resultSummary.mode }}</span>
                    <span>{{ resultSummary.target }}</span>
                    <span>{{ currentPackLabel }}</span>
                  </div>
                  <strong class="result-path">{{ resultSummary.output }}</strong>
                  <p class="result-text">{{ resultSummary.text }}</p>
                  <div class="result-facts">
                    <span>{{ currentTemplateLabel }}</span>
                    <span>{{ modifierSummaryLabel }}</span>
                    <span>{{ negativePromptStateLabel }}</span>
                  </div>
                </div>
              </div>
            </div>
        </WorkbenchPaneCard>
      </section>
    </div>

    <PromptPackEditorDrawer
      v-if="workspaceMode === 'illustration' && showAdvancedTemplateEditor"
      v-model:visible="showAdvancedTemplateEditor"
      v-model:file-name="promptPackDraftFileName"
      v-model:set-as-default="promptPackSetAsDefault"
      v-model:template-id="promptPackDraftTemplateId"
      :summary-exists="Boolean(summary)"
      :prompt-pack-draft-state-label="promptPackDraftStateLabel"
      :current-pack-source-label="currentPackSourceLabel"
      :prompt-pack-draft="promptPackDraft"
      :prompt-pack-draft-template="promptPackDraftTemplate"
      :prompt-pack-draft-negative-policy-options="promptPackDraftNegativePolicyOptions"
      :prompt-pack-draft-commercial-policy-options="promptPackDraftCommercialPolicyOptions"
      :prompt-pack-library-error="promptPackLibraryError"
      :saving-prompt-pack-library="savingPromptPackLibrary"
      @new-pack="startNewPromptPackDraft"
      @copy-current="startDraftFromSelectedPack"
      @add-template="addPromptPackDraftTemplate"
      @remove-template="removePromptPackDraftTemplate"
      @add-modifier="addPromptPackDraftModifier"
      @remove-modifier="removePromptPackDraftModifier"
      @add-negative-policy="addPromptPackDraftNegativePolicy"
      @remove-negative-policy="removePromptPackDraftNegativePolicy"
      @add-commercial-policy="addPromptPackDraftCommercialPolicy"
      @remove-commercial-policy="removePromptPackDraftCommercialPolicy"
      @reset="resetPromptPackDraft"
      @save="handleSavePromptPackDraft"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";

import {
  buildWorkbenchAssetUrl,
  buildProjectAssetUrl,
  createProject,
  dryRunIllustration,
  dryRunIllustrationForm,
  fetchPromptPackLibrary,
  getIllustrationDefaultUseCase,
  getIllustrationTemplateOptions,
  getIllustrationUseCaseOptions,
  ILLUSTRATION_TEXT_DESIGN_OPTIONS,
  importProject,
  pickIllustrationTemplateId,
  pickIllustrationUseCase,
  selectProjectFolder,
  savePromptPack,
  type ChapterRecord,
  type EntityRecord,
  type IllustrationDryRunResult,
  type IllustrationGenerateResult,
  type IllustrationRecord,
  type IllustrationTargetType,
  type IllustrationTextDesignMode,
  type IllustrationTemplateSummary,
  type PromptPackCommercialPolicyDocument,
  type PromptPackDocument,
  type PromptPackLibraryResponse,
  type PromptPackModifierDocument,
  type PromptPackNegativePolicyDocument,
  type PromptPackTemplateDocument,
  type ProjectOption,
  generateIllustration,
  generateIllustrationForm,
} from "@/api/storyCanvas";
import WorkbenchPaneCard from "@/components/WorkbenchPaneCard.vue";
import WorkbenchSidebarCard from "@/components/WorkbenchSidebarCard.vue";
import { useWorkspace } from "@/composables/useWorkspace";
import { TCard, TTag } from "@/tdesign/display";
import {
  TButton,
  TForm,
  TFormItem,
  TInput,
  TInputNumber,
  TRadioButton,
  TRadioGroup,
  TSelect,
  TSwitch,
  TTextarea,
} from "@/tdesign/forms";
import { TTable } from "@/tdesign/table";

const PromptPackEditorDrawer = defineAsyncComponent(() => import("@/components/PromptPackEditorDrawer.vue"));

type ActionItem = {
  title: string;
  detail: string;
  status: string;
};

type ProtocolEntry = {
  label: string;
  value: string;
};

type IllustrationHistoryRow = {
  id: string;
  title: string;
  target: string;
  mode: string;
  updatedAt: string;
  raw: IllustrationRecord;
};

type PromptPackTemplateOption = IllustrationTemplateSummary;

type PromptModifierOption = {
  id: string;
  group: string;
  label: string;
  negativeFragment?: string;
};

type PromptNegativePolicy = {
  id: string;
  label: string;
  negativePrompt: string;
};

type PromptPackSourceGroup = {
  key: string;
  label: string;
  packs: Array<{
    id: string;
    name: string;
    label: string;
    source?: string;
  }>;
};

type TreeDragKind = "chapter" | "entity";
type SidebarGroupKey =
  | "reviewChapters"
  | "reviewEntities"
  | "reviewReference"
  | "illustrationEntities"
  | "illustrationChapters"
  | "illustrationHistory";

const workspace = useWorkspace();
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

const summary = computed(() => workspace.summary.value);
const settings = computed(() => workspace.settings.value);
const workspaceError = computed(() => workspace.error.value);
const selectedRoot = computed(() => workspace.selectedRoot.value);
const isProjectBound = computed(() => Boolean(summary.value?.project.root));

const workspaceMode = defineModel<"review" | "illustration">("workspaceMode", { required: true });
const selectedChapter = ref<ChapterRecord | null>(null);
const viewportWidth = ref(typeof window === "undefined" ? 1440 : window.innerWidth);
const isTabletLayout = computed(() => viewportWidth.value <= 1180);
const isMobileLayout = computed(() => viewportWidth.value <= 900);
const showAdvancedTemplateEditor = ref(false);

const projectPanelMode = ref<"import" | "create">("import");
const showProjectSetup = ref(false);
const creatingProject = ref(false);
const selectingProjectFolder = ref(false);
const projectTitleDraft = ref("");
const projectGenreDraft = ref("");
const projectDirectoryDraft = ref("");
const importProjectRootDraft = ref("");

const mode = ref<"text-to-image" | "image-to-image" | "inpaint">("text-to-image");
const targetType = ref<"chapter" | "entity">("chapter");
const targetId = ref("");
const manualTargetName = ref("");
const useCase = ref(getIllustrationDefaultUseCase(targetType.value));
const textDesignMode = ref<IllustrationTextDesignMode>("none");
const titleText = ref("");
const subtitleText = ref("");
const bodyText = ref("");
const fontStyleHint = ref("");
const promptPack = ref("default");
const templateId = ref("");
const modifierRefs = ref<string[]>([]);
const commercialMode = ref<"personal" | "commercial">("personal");
const responseModel = ref("gpt-5.4");
const size = ref("1024x1024");
const quality = ref("high");
const batchCount = ref(1);
const outputName = ref("");
const positivePrompt = ref("");
const negativePrompt = ref("");

const inputImageFile = ref<File | null>(null);
const maskFile = ref<File | null>(null);
const inputImagePath = ref("");
const maskPath = ref("");
const inputImagePreviewUrl = ref("");
const maskPreviewUrl = ref("");

const dryRunResult = ref<IllustrationDryRunResult | null>(null);
const generateResult = ref<IllustrationGenerateResult | null>(null);
const activePreviewRecord = ref<IllustrationRecord | null>(null);
const submitting = ref(false);
const errorMessage = ref("");
const promptPackLibrary = ref<PromptPackLibraryResponse | null>(null);
const loadingPromptPackLibrary = ref(false);
const savingPromptPackLibrary = ref(false);
const promptPackLibraryError = ref("");
const promptPackDraft = ref<PromptPackDocument | null>(null);
const promptPackDraftFileName = ref("");
const promptPackDraftTemplateId = ref("");
const promptPackDraftMode = ref<"new" | "copy" | "edit">("new");
const promptPackSetAsDefault = ref(false);
const syncedProjectRoot = ref("");
const lastAutoPrompt = ref("");
const lastAutoNegativePrompt = ref("");

const chapterOrderIds = ref<string[]>([]);
const entityOrderIds = ref<string[]>([]);
const dragState = ref<{ kind: TreeDragKind; id: string } | null>(null);
const sidebarGroupOpen = reactive<Record<SidebarGroupKey, boolean>>({
  reviewChapters: true,
  reviewEntities: true,
  reviewReference: false,
  illustrationEntities: true,
  illustrationChapters: true,
  illustrationHistory: false,
});

function updateViewportWidth() {
  viewportWidth.value = window.innerWidth;
}

const responseModelOptions = [
  { label: "gpt-5.4", value: "gpt-5.4" },
  { label: "gpt-5.5", value: "gpt-5.5" },
];
const sizeOptions = [
  { label: "1024 x 1024", value: "1024x1024" },
  { label: "1536 x 1024", value: "1536x1024" },
  { label: "1024 x 1536", value: "1024x1536" },
];
const qualityOptions = [
  { label: "auto", value: "auto" },
  { label: "medium", value: "medium" },
  { label: "high", value: "high" },
];
const commercialModeOptions = [
  { label: "个人", value: "personal" },
  { label: "商用", value: "commercial" },
];

const chapterList = computed(() => summary.value?.chapters || []);
const entityList = computed(() => summary.value?.entities || []);
const sidebarMessage = computed(() => errorMessage.value || workspaceError.value);
const explorerProjectOptions = computed(() => {
  const seen = new Set<string>();
  const options = workspace.projects.value
    .filter((item) => {
      if (seen.has(item.root)) {
        return false;
      }
      seen.add(item.root);
      return true;
    })
    .map((item) => ({
      label: buildProjectOptionLabel(item),
      value: item.root,
    }));
  return options;
});

const orderedChapterList = computed(() => applyTreeOrder(chapterList.value, chapterOrderIds.value));
const orderedEntityList = computed(() => applyTreeOrder(entityList.value, entityOrderIds.value));

const visibleIssues = computed(() => {
  if (!selectedChapter.value) {
    return [];
  }
  return selectedChapter.value.issues.length > 0 ? selectedChapter.value.issues : ["暂无高优先级问题"];
});

const protocolEntries = computed<ProtocolEntry[]>(() => {
  const project = summary.value?.project;
  return [
    ...flattenProtocolEntries(project?.positioning).slice(0, 2),
    ...flattenProtocolEntries(project?.storyContract).slice(0, 1),
    ...flattenProtocolEntries(project?.commercialPositioning).slice(0, 1),
  ].slice(0, 4);
});

const actionQueue = computed<ActionItem[]>(() => {
  if (!selectedChapter.value) {
    return [];
  }
  const issues =
    selectedChapter.value.issues.length > 0
      ? selectedChapter.value.issues.slice(0, 2).map((issue, index) => ({
          title: `修复项 ${index + 1}`,
          detail: issue,
          status: index === 0 ? "优先" : "排队",
        }))
      : [
          {
            title: "继续复检",
            detail: "当前没有暴露高优先级问题，可以转向下一轮复检。",
            status: "观察",
          },
        ];

  return issues;
});

const targetOptions = computed(() => {
  if (targetType.value === "entity") {
    return (summary.value?.entities || []).map((item) => ({
      label: item.appearanceSummary ? `${item.name} · ${item.appearanceSummary}` : item.name,
      value: item.id,
    }));
  }
  return (summary.value?.chapters || []).map((item) => ({
    label: `${item.title} · ${item.id}`,
    value: item.id,
  }));
});

const illustrationHistory = computed<IllustrationHistoryRow[]>(() =>
  [...(summary.value?.illustrations || [])]
    .reverse()
    .map((item) => ({
      id: item.id || `${item.generatedAt || "history"}-${item.targetRef?.targetId || item.chapterId || item.entityId || "item"}`,
      title: item.revisedPrompt || item.promptText || "illustration",
      target: item.targetRef?.targetId || item.chapterId || item.entityId || "-",
      mode: item.mode || "text-to-image",
      updatedAt: item.generatedAt || "-",
      raw: item,
    }))
);

const availablePromptPacks = computed(
  () =>
    promptPackLibrary.value?.availablePromptPacks ||
    summary.value?.illustrationConfig.availablePromptPacks ||
    settings.value?.workspaceIllustration.availablePromptPacks ||
    []
);
const promptPackDocuments = computed(() => promptPackLibrary.value?.packs || []);
const promptPackSourceGroups = computed<PromptPackSourceGroup[]>(() => {
  const systemPacks = availablePromptPacks.value.filter((item) => String(item.source || "").trim() === "builtin");
  const userPacks = availablePromptPacks.value.filter((item) => String(item.source || "").trim() !== "builtin");
  return [
    {
      key: "system",
      label: "系统模板",
      packs: systemPacks,
    },
    {
      key: "user",
      label: "用户模板",
      packs: userPacks,
    },
  ].filter((group) => group.packs.length > 0);
});
const selectedPromptPack = computed(() => {
  return availablePromptPacks.value.find((item) => item.name === promptPack.value) || availablePromptPacks.value[0];
});
const selectedPromptPackDocument = computed<PromptPackDocument | null>(() => {
  const selected = selectedPromptPack.value;
  if (!selected) {
    return null;
  }
  return promptPackDocuments.value.find((item) => item.id === selected.id || item.name === selected.name) || null;
});
const packTemplates = computed<PromptPackTemplateOption[]>(() => (selectedPromptPack.value?.templates || []) as PromptPackTemplateOption[]);
const modifierOptions = computed<PromptModifierOption[]>(() => (selectedPromptPack.value?.modifierGroups || []) as PromptModifierOption[]);
const negativePolicies = computed<PromptNegativePolicy[]>(() => (selectedPromptPack.value?.negativePolicies || []) as PromptNegativePolicy[]);
const selectedTemplate = computed<PromptPackTemplateOption | null>(() => {
  return packTemplates.value.find((item) => item.id === templateId.value) || null;
});
const selectedEntity = computed<EntityRecord | null>(() => {
  if (targetType.value !== "entity") {
    return null;
  }
  return (summary.value?.entities || []).find((item) => item.id === targetId.value) || null;
});

const promptPackOptions = computed(() =>
  availablePromptPacks.value.map((item) => ({
    label: item.label,
    value: item.name,
  }))
);
const useCaseOptions = computed(() => getIllustrationUseCaseOptions(packTemplates.value, targetType.value, mode.value));
const templateOptions = computed(() => getIllustrationTemplateOptions(packTemplates.value, mode.value, useCase.value));

const currentTemplateLabel = computed(() => {
  return templateOptions.value.find((item) => item.value === templateId.value)?.label || templateId.value || "-";
});
const currentPackLabel = computed(() => selectedPromptPack.value?.label || promptPack.value || "-");
const currentModeLabel = computed(() => {
  if (mode.value === "image-to-image") {
    return "图生图";
  }
  if (mode.value === "inpaint") {
    return "重绘";
  }
  return "文生图";
});
const currentPackSourceLabel = computed(() => {
  const source = String(selectedPromptPack.value?.source || "").trim();
  return source === "builtin" ? "系统模板" : source ? "用户模板" : "-";
});
const modifierSummaryLabel = computed(() => {
  const labels = modifierOptions.value
    .filter((item) => modifierRefs.value.includes(item.id))
    .map((item) => item.label);
  return labels.length > 0 ? labels.join(" / ") : "未选择";
});
const promptPackDraftTemplate = computed<PromptPackTemplateDocument | null>(() => {
  if (!promptPackDraft.value) {
    return null;
  }
  return promptPackDraft.value.templates.find((item) => item.id === promptPackDraftTemplateId.value) || promptPackDraft.value.templates[0] || null;
});
const promptPackDraftNegativePolicyOptions = computed(() =>
  (promptPackDraft.value?.policies.negativePolicies || []).map((item) => ({
    label: item.label || item.id || "未命名负向策略",
    value: item.id,
  }))
);
const promptPackDraftCommercialPolicyOptions = computed(() =>
  (promptPackDraft.value?.policies.commercialPolicies || []).map((item) => ({
    label: item.label || item.id || "未命名商用策略",
    value: item.id,
  }))
);
const promptPackLibraryDir = computed(
  () =>
    promptPackLibrary.value?.userPromptPackDir ||
    summary.value?.illustrationConfig.promptPackDir ||
    settings.value?.workspaceIllustration.promptPackDir ||
    ""
);
const promptPackDraftStateLabel = computed(() => {
  if (!promptPackDraft.value) {
    return "未打开编辑器";
  }
  if (promptPackDraftMode.value === "edit") {
    return "编辑用户模板";
  }
  if (promptPackDraftMode.value === "copy") {
    return "复制系统模板";
  }
  return "新建用户模板";
});
const negativePromptStateLabel = computed(() => (negativePrompt.value.trim() ? "已填写" : "未填写"));
const resolvedPromptPreview = computed(() => {
  const generatedPrompt = generateResult.value?.illustration.promptSnapshot?.resolvedPrompt;
  const dryRunPrompt = typeof dryRunResult.value?.promptSnapshot?.resolvedPrompt === "string" ? dryRunResult.value.promptSnapshot.resolvedPrompt : "";
  return generatedPrompt || dryRunPrompt || positivePrompt.value.trim() || "";
});
const resolvedNegativePreview = computed(() => {
  const generatedNegative = generateResult.value?.illustration.policySnapshot?.negativePrompt;
  const dryRunNegative = typeof dryRunResult.value?.policySnapshot?.negativePrompt === "string" ? dryRunResult.value.policySnapshot.negativePrompt : "";
  return generatedNegative || dryRunNegative || negativePrompt.value.trim() || "";
});
const outputNameStateLabel = computed(() => (outputName.value.trim() ? outputName.value.trim() : "默认命名"));

const currentProjectRoot = computed(() => summary.value?.project.root || "");
const inputImageDisplayName = computed(() => inputImageFile.value?.name || inputImagePath.value || "");
const maskDisplayName = computed(() => maskFile.value?.name || maskPath.value || "");
const inputImageResolvedPreviewUrl = computed(() => {
  if (inputImagePreviewUrl.value) {
    return inputImagePreviewUrl.value;
  }
  if (!currentProjectRoot.value || !inputImagePath.value) {
    return "";
  }
  return buildProjectAssetUrl(currentProjectRoot.value, inputImagePath.value);
});
const maskResolvedPreviewUrl = computed(() => {
  if (maskPreviewUrl.value) {
    return maskPreviewUrl.value;
  }
  if (!currentProjectRoot.value || !maskPath.value) {
    return "";
  }
  return buildProjectAssetUrl(currentProjectRoot.value, maskPath.value);
});

const latestHistoryRecord = computed<IllustrationRecord | null>(() => illustrationHistory.value[0]?.raw || null);
const previewRecord = computed(
  () => generateResult.value?.illustration || activePreviewRecord.value || latestHistoryRecord.value
);
const resultPreviewUrl = computed(() => {
  const filePath = previewRecord.value?.filePath || "";
  const scope = generateResult.value?.scope || (currentProjectRoot.value ? "project" : "workspace");
  const root = generateResult.value?.summary?.project.root || currentProjectRoot.value;
  if (!filePath) {
    return "";
  }
  if (scope === "workspace" || !root) {
    return buildWorkbenchAssetUrl(filePath);
  }
  return buildProjectAssetUrl(root, filePath);
});

const resultSummary = computed(() => {
  if (previewRecord.value) {
    const item = previewRecord.value;
    return {
      mode: item.mode || "-",
      target: (item as IllustrationRecord & { targetLabel?: string }).targetLabel || item.targetRef?.targetId || item.chapterId || item.entityId || "-",
      output: item.filePath || "-",
      text: item.revisedPrompt || item.promptSnapshot?.resolvedPrompt || item.promptText || "-",
      batchCount: item.batch?.count || 1,
    };
  }
  if (dryRunResult.value) {
    const payload = dryRunResult.value.payload as {
      mode?: string;
      targetId?: string;
      promptText?: string;
      batch?: {
        count?: number;
      };
    };
    return {
      mode: payload.mode || "-",
      target: String((dryRunResult.value as IllustrationDryRunResult & { targetLabel?: string }).targetLabel || payload.targetId || "-"),
      output: dryRunResult.value.outputFile,
      text: payload.promptText || "-",
      batchCount: payload.batch?.count || 1,
    };
  }
  return null;
});
const currentTargetLabel = computed(() => {
  if (!summary.value) {
    return manualTargetName.value.trim() || (targetType.value === "entity" ? "自由角色" : "自由场景");
  }
  if (targetType.value === "entity") {
    return selectedEntity.value?.name || targetId.value || "-";
  }
  return chapterList.value.find((item) => item.id === targetId.value)?.title || targetId.value || "-";
});

const promptSeedTitle = computed(() => (targetType.value === "entity" ? "角色卡外貌基线" : "场景提示基线"));
const promptSeedHint = computed(() => {
  if (targetType.value === "entity") {
    if (!summary.value) {
      return "当前未绑定项目，按自由角色模式处理；建议把外貌、服装和气质直接写进正面提示词。";
    }
    const entity = selectedEntity.value;
    if (!entity) {
      return "选择角色后，会优先回填角色卡里的外貌、状态和人物简介。";
    }
    return entity.appearanceSummary || entity.summary || "当前角色卡还没有明确外貌描述，请在下方手动补充。";
  }
  if (!summary.value) {
    return "当前未绑定项目，按自由场景模式处理；请直接填写人物、动作、镜头、环境和氛围。";
  }
  return "章节模式不再自动注入正文；请手动填写出场角色、动作、镜头、环境和氛围。";
});

const defaultNegativePrompt = computed(() => {
  const policyRef = selectedTemplate.value?.defaultNegativePolicyRef || "";
  const base = negativePolicies.value.find((item) => item.id === policyRef)?.negativePrompt || "";
  const modifierNegative = modifierOptions.value
    .filter((item) => modifierRefs.value.includes(item.id) && item.negativeFragment)
    .map((item) => item.negativeFragment?.trim() || "")
    .filter(Boolean)
    .join(", ");
  return [base.trim(), modifierNegative].filter(Boolean).join(", ");
});

const illustrationSetupWarning = computed(() => {
  if (!settings.value?.local.apiKeyConfigured) {
    return "缺少提供商 API key。请先进入设置页保存本地 key，或通过环境变量提供。";
  }
  if (!summary.value) {
    return "";
  }
  const adapterName = summary.value.illustrationConfig.adapterName || "";
  if (!adapterName) {
    return "当前项目没有服务商配置。";
  }
  if (adapterName !== "openai") {
    return `当前工作台只支持 openai adapter，当前为 ${adapterName}。`;
  }
  return "";
});

function refreshProjects() {
  void workspace.refreshProjects();
}

function expandChapterSidebarGroups() {
  sidebarGroupOpen.reviewChapters = true;
  sidebarGroupOpen.illustrationChapters = true;
}

onMounted(() => {
  updateViewportWidth();
  window.addEventListener("resize", updateViewportWidth);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", updateViewportWidth);
});

function handleProjectSelect(value: string) {
  showProjectSetup.value = false;
  expandChapterSidebarGroups();
  void workspace.selectProject(value);
}

function leaveProject() {
  showProjectSetup.value = false;
  syncedProjectRoot.value = "";
  resetResultPanels();
  clearInputImageSelection();
  clearMaskSelection();
  inputImagePath.value = "";
  maskPath.value = "";
  void workspace.selectProject("");
}

async function handleCreateProject() {
  const title = projectTitleDraft.value.trim();
  if (!title) {
    errorMessage.value = "请先填写项目标题。";
    return;
  }
  creatingProject.value = true;
  errorMessage.value = "";
  try {
    const payload = await createProject({
      title,
      genre: projectGenreDraft.value.trim(),
      directoryName: projectDirectoryDraft.value.trim() || undefined,
    });
    showProjectSetup.value = false;
    projectTitleDraft.value = "";
    projectGenreDraft.value = "";
    projectDirectoryDraft.value = "";
    await workspace.refreshProjects();
    expandChapterSidebarGroups();
    await workspace.selectProject(payload.project.project.root);
    workspaceMode.value = "illustration";
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    creatingProject.value = false;
  }
}

async function handleImportProject() {
  const root = importProjectRootDraft.value.trim();
  if (!root) {
    errorMessage.value = "请先填写要导入的项目路径。";
    return;
  }
  creatingProject.value = true;
  errorMessage.value = "";
  try {
    const payload = await importProject({ root });
    importProjectRootDraft.value = "";
    showProjectSetup.value = false;
    await workspace.refreshProjects();
    expandChapterSidebarGroups();
    await workspace.selectProject(payload.project.project.root);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    creatingProject.value = false;
  }
}

async function handleSelectProjectFolder() {
  selectingProjectFolder.value = true;
  errorMessage.value = "";
  try {
    const payload = await selectProjectFolder({
      initialPath: importProjectRootDraft.value.trim() || selectedRoot.value || undefined,
    });
    importProjectRootDraft.value = payload.path;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    selectingProjectFolder.value = false;
  }
}

function handleTreeDragStart(kind: TreeDragKind, id: string) {
  dragState.value = { kind, id };
}

function handleTreeDrop(kind: TreeDragKind, targetId: string) {
  if (!dragState.value || dragState.value.kind !== kind || dragState.value.id === targetId) {
    return;
  }
  if (kind === "chapter") {
    chapterOrderIds.value = moveTreeItem(chapterOrderIds.value, dragState.value.id, targetId);
  } else {
    entityOrderIds.value = moveTreeItem(entityOrderIds.value, dragState.value.id, targetId);
  }
  dragState.value = null;
}

function handleSidebarGroupToggle(key: SidebarGroupKey, event: Event) {
  sidebarGroupOpen[key] = (event.currentTarget as HTMLDetailsElement).open;
}

function openEntityIllustration(entityId: string) {
  workspaceMode.value = "illustration";
  targetType.value = "entity";
  targetId.value = entityId;
  applySuggestedPrompt(true);
  applySuggestedNegativePrompt(true);
}

function openChapterIllustration(chapterId: string) {
  workspaceMode.value = "illustration";
  targetType.value = "chapter";
  targetId.value = chapterId;
  applySuggestedPrompt(true);
  applySuggestedNegativePrompt(true);
}

function resetResultPanels() {
  dryRunResult.value = null;
  generateResult.value = null;
  activePreviewRecord.value = null;
}
function clonePromptPackDocument(pack: PromptPackDocument | null): PromptPackDocument | null {
  if (!pack) {
    return null;
  }
  return JSON.parse(JSON.stringify(pack)) as PromptPackDocument;
}

function slugifyPromptPackFileName(value: string): string {
  return (
    value
      .trim()
      .replace(/[\\/]+/g, "-")
      .replace(/[<>:"|?*\u0000-\u001f]+/g, "-")
      .replace(/\s+/g, "-")
      .replace(/-{2,}/g, "-")
      .replace(/^-+|-+$/g, "") || "custom-pack"
  );
}

function basePromptPackFileName(pack: PromptPackDocument | null): string {
  const sourceFile = String(pack?.sourceFile || "").trim();
  if (sourceFile) {
    const match = sourceFile.split(/[\\/]/).pop() || "";
    return match.replace(/\.yaml$/i, "");
  }
  return slugifyPromptPackFileName(String(pack?.name || pack?.label || pack?.id || "custom-pack"));
}

function createDraftTemplate(useCase = getIllustrationDefaultUseCase(targetType.value)): PromptPackTemplateDocument {
  const draftId = `draft-${useCase}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
  return {
    id: draftId,
    label: "",
    useCase,
    mode: mode.value,
    complexity: "standard",
    promptTemplate: "{subject}\n{styleModifiers}\n{userExtraPrompt}",
    defaultNegativePolicyRef: "",
    defaultCommercialPolicyRef: "",
  };
}

function createDraftModifier(): PromptPackModifierDocument {
  const draftId = `draft-modifier-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
  return {
    id: draftId,
    group: "style",
    label: "",
    promptFragment: "",
    negativeFragment: "",
    commercialTags: [],
  };
}

function createDraftNegativePolicy(): PromptPackNegativePolicyDocument {
  const draftId = `draft-negative-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
  return {
    id: draftId,
    label: "",
    negativePrompt: "",
  };
}

function createDraftCommercialPolicy(): PromptPackCommercialPolicyDocument {
  const draftId = `draft-commercial-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
  return {
    id: draftId,
    label: "",
    mode: "personal",
    extraPrompt: "",
    restrictions: [],
  };
}

function createEmptyPromptPackDraft(): PromptPackDocument {
  return {
    id: "",
    version: "project",
    label: "",
    description: "",
    supports: {
      modes: [mode.value],
      commercial: true,
    },
    templates: [createDraftTemplate()],
    modifierGroups: [],
    policies: {
      negativePolicies: [],
      commercialPolicies: [],
    },
  };
}

function applyPromptPackDraft(pack: PromptPackDocument, draftMode: "new" | "copy" | "edit", fileName = "") {
  promptPackDraft.value = clonePromptPackDocument(pack);
  promptPackDraftMode.value = draftMode;
  promptPackDraftFileName.value = slugifyPromptPackFileName(fileName || basePromptPackFileName(pack));
  promptPackDraftTemplateId.value = promptPackDraft.value?.templates[0]?.id || "";
  const defaultPackName = summary.value?.illustrationConfig.promptPackName || settings.value?.workspaceIllustration.promptPackName || "";
  promptPackSetAsDefault.value = draftMode !== "new" && defaultPackName === (pack.name || "");
}

async function refreshPromptPackLibrary(root = summary.value?.project.root || "") {
  loadingPromptPackLibrary.value = true;
  promptPackLibraryError.value = "";
  try {
    promptPackLibrary.value = await fetchPromptPackLibrary(root || undefined);
  } catch (error) {
    promptPackLibraryError.value = error instanceof Error ? error.message : String(error);
  } finally {
    loadingPromptPackLibrary.value = false;
  }
}

function startNewPromptPackDraft() {
  applyPromptPackDraft(createEmptyPromptPackDraft(), "new", `自定义-${targetType.value === "entity" ? "角色" : "场景"}-${mode.value}`);
}

function startDraftFromSelectedPack() {
  const source = selectedPromptPackDocument.value;
  if (!source) {
    startNewPromptPackDraft();
    return;
  }
  const draft = clonePromptPackDocument(source) || createEmptyPromptPackDraft();
  const isBuiltin = String(source.source || "").trim() === "builtin";
  if (isBuiltin) {
    draft.id = "";
    draft.name = "";
    draft.version = "project";
    draft.source = "";
    draft.sourceFile = "";
    draft.writable = true;
  }
  applyPromptPackDraft(
    draft,
    isBuiltin ? "copy" : "edit",
    isBuiltin ? `${basePromptPackFileName(source)}-custom` : basePromptPackFileName(source)
  );
}

function resetPromptPackDraft() {
  if (selectedPromptPackDocument.value) {
    startDraftFromSelectedPack();
    return;
  }
  startNewPromptPackDraft();
}

function addPromptPackDraftTemplate() {
  if (!promptPackDraft.value) {
    startNewPromptPackDraft();
  }
  const nextTemplate = createDraftTemplate();
  promptPackDraft.value?.templates.push(nextTemplate);
  promptPackDraftTemplateId.value = nextTemplate.id;
}

function removePromptPackDraftTemplate(templateToRemove: PromptPackTemplateDocument) {
  if (!promptPackDraft.value) {
    return;
  }
  promptPackDraft.value.templates = promptPackDraft.value.templates.filter((item) => item !== templateToRemove);
  if (promptPackDraft.value.templates.length === 0) {
    promptPackDraft.value.templates.push(createDraftTemplate());
  }
  promptPackDraftTemplateId.value = promptPackDraft.value.templates[0]?.id || "";
}

function addPromptPackDraftModifier() {
  if (!promptPackDraft.value) {
    startNewPromptPackDraft();
  }
  promptPackDraft.value?.modifierGroups.push(createDraftModifier());
}

function removePromptPackDraftModifier(index: number) {
  promptPackDraft.value?.modifierGroups.splice(index, 1);
}

function addPromptPackDraftNegativePolicy() {
  if (!promptPackDraft.value) {
    startNewPromptPackDraft();
  }
  promptPackDraft.value?.policies.negativePolicies.push(createDraftNegativePolicy());
}

function removePromptPackDraftNegativePolicy(index: number) {
  promptPackDraft.value?.policies.negativePolicies.splice(index, 1);
}

function addPromptPackDraftCommercialPolicy() {
  if (!promptPackDraft.value) {
    startNewPromptPackDraft();
  }
  promptPackDraft.value?.policies.commercialPolicies.push(createDraftCommercialPolicy());
}

function removePromptPackDraftCommercialPolicy(index: number) {
  promptPackDraft.value?.policies.commercialPolicies.splice(index, 1);
}

function normalizePromptPackDraftForSave(pack: PromptPackDocument): PromptPackDocument {
  const cloned = clonePromptPackDocument(pack) || createEmptyPromptPackDraft();
  cloned.label = cloned.label.trim();
  cloned.description = cloned.description.trim();
  cloned.templates = cloned.templates.map((item) => ({
    ...item,
    id: item.id.trim(),
    label: item.label.trim(),
    useCase: item.useCase.trim(),
    mode: item.mode.trim(),
    complexity: item.complexity.trim() || "standard",
    promptTemplate: item.promptTemplate,
    defaultNegativePolicyRef: item.defaultNegativePolicyRef?.trim() || "",
    defaultCommercialPolicyRef: item.defaultCommercialPolicyRef?.trim() || "",
  }));
  cloned.modifierGroups = cloned.modifierGroups.map((item) => ({
    ...item,
    id: item.id.trim(),
    group: item.group.trim() || "style",
    label: item.label.trim(),
    promptFragment: item.promptFragment,
    negativeFragment: item.negativeFragment?.trim() || "",
    commercialTags: item.commercialTags || [],
  }));
  cloned.policies = {
    negativePolicies: (cloned.policies.negativePolicies || []).map((item) => ({
      ...item,
      id: item.id.trim(),
      label: item.label.trim(),
      negativePrompt: item.negativePrompt,
    })),
    commercialPolicies: (cloned.policies.commercialPolicies || []).map((item) => ({
      ...item,
      id: item.id.trim(),
      label: item.label.trim(),
      mode: item.mode.trim() || "personal",
      extraPrompt: item.extraPrompt,
      restrictions: item.restrictions || [],
    })),
  };
  return cloned;
}

async function handleSavePromptPackDraft() {
  if (!promptPackDraft.value) {
    startNewPromptPackDraft();
    return;
  }
  const fileName = slugifyPromptPackFileName(promptPackDraftFileName.value);
  if (!promptPackDraft.value.label.trim()) {
    promptPackLibraryError.value = "请先填写模板包名称。";
    return;
  }
  if (!fileName) {
    promptPackLibraryError.value = "请先填写文件名。";
    return;
  }
  if (!promptPackDraft.value.templates.some((item) => item.id.trim() && item.useCase.trim() && item.promptTemplate.trim())) {
    promptPackLibraryError.value = "至少保留一个有效模板。";
    return;
  }
  promptPackLibraryError.value = "";
  savingPromptPackLibrary.value = true;
  try {
    const payload = await savePromptPack({
      root: summary.value?.project.root || undefined,
      fileName,
      setAsDefault: Boolean(summary.value?.project.root) && promptPackSetAsDefault.value,
      pack: normalizePromptPackDraftForSave(promptPackDraft.value),
    });
    promptPackLibrary.value = payload;
    const savedPackName = payload.savedPack?.name || "";
    if (savedPackName) {
      promptPack.value = savedPackName;
    }
    await Promise.all([
      workspace.refreshSettings(summary.value?.project.root || ""),
      summary.value?.project.root ? workspace.refreshSummary() : Promise.resolve(),
    ]);
    if (payload.savedPack) {
      applyPromptPackDraft(payload.savedPack, "edit");
    }
  } catch (error) {
    promptPackLibraryError.value = error instanceof Error ? error.message : String(error);
  } finally {
    savingPromptPackLibrary.value = false;
  }
}

function syncFromProject() {
  const projectSummary = summary.value;
  const config = projectSummary?.illustrationConfig || settings.value?.workspaceIllustration;
  if (!config) {
    return;
  }
  syncedProjectRoot.value = projectSummary?.project.root || "";
  responseModel.value = config.responseModel || "gpt-5.4";
  size.value = config.defaultSize || "1024x1024";
  quality.value = config.quality || "auto";
  batchCount.value = parseInt(config.defaultBatchCount || "1", 10) || 1;
  outputName.value = "";
  promptPack.value = config.promptPackName || "default";
  commercialMode.value = config.commercialMode || "personal";
  modifierRefs.value = [...(config.defaultModifierRefs || [])];
  mode.value = "text-to-image";
  textDesignMode.value = "none";
  titleText.value = "";
  subtitleText.value = "";
  bodyText.value = "";
  fontStyleHint.value = "";
  clearInputImageSelection();
  clearMaskSelection();
  inputImagePath.value = "";
  maskPath.value = "";
  resetResultPanels();
  errorMessage.value = "";

  if (projectSummary?.entities.length) {
    targetType.value = "entity";
    targetId.value = projectSummary.entities[0].id;
  } else if (projectSummary?.project.activeChapterId) {
    targetType.value = "chapter";
    targetId.value = projectSummary.project.activeChapterId;
  } else if (projectSummary?.chapters.length) {
    targetType.value = "chapter";
    targetId.value = projectSummary.chapters[0].id;
  } else {
    targetId.value = "";
  }
  if (!projectSummary) {
    manualTargetName.value = targetType.value === "entity" ? "自由角色" : "自由场景";
  }

  useCase.value = pickIllustrationUseCase(
    packTemplates.value,
    targetType.value,
    mode.value,
    getIllustrationDefaultUseCase(targetType.value)
  );
  const nextTemplate =
    (config.defaultTemplateByUseCase?.[useCase.value] || "") &&
    packTemplates.value.some((item) => item.id === config.defaultTemplateByUseCase?.[useCase.value])
      ? String(config.defaultTemplateByUseCase?.[useCase.value] || "")
      : "";
  templateId.value = pickIllustrationTemplateId(packTemplates.value, mode.value, useCase.value, nextTemplate);
  applySuggestedPrompt(true);
  applySuggestedNegativePrompt(true);
}

function buildIllustrationRequest() {
  const boundRoot = summary.value?.project.root || "";
  const isFreeMode = !boundRoot;
  if (!isFreeMode && !targetId.value) {
    throw new Error("请选择目标章节或角色。");
  }
  if (isFreeMode && !manualTargetName.value.trim()) {
    throw new Error("自由模式下请先填写目标。");
  }
  if (!positivePrompt.value.trim()) {
    throw new Error("请先填写正面提示词。");
  }
  if ((mode.value === "image-to-image" || mode.value === "inpaint") && !inputImageFile.value && !inputImagePath.value.trim()) {
    throw new Error("图生图 / 重绘模式需要提供源图。");
  }
  if (mode.value === "inpaint" && !maskFile.value && !maskPath.value.trim()) {
    throw new Error("重绘模式需要提供 mask。");
  }
  return {
    root: boundRoot || undefined,
    mode: mode.value,
    targetType: targetType.value,
    useCase: useCase.value || undefined,
    textDesignMode: textDesignMode.value,
    titleText: textDesignMode.value === "designed" ? titleText.value.trim() || undefined : undefined,
    subtitleText: textDesignMode.value === "designed" ? subtitleText.value.trim() || undefined : undefined,
    bodyText: textDesignMode.value === "designed" ? bodyText.value.trim() || undefined : undefined,
    fontStyleHint: textDesignMode.value === "designed" ? fontStyleHint.value.trim() || undefined : undefined,
    manualTargetName: isFreeMode ? manualTargetName.value.trim() : undefined,
    chapterId: !isFreeMode && targetType.value === "chapter" ? targetId.value : undefined,
    entityId: !isFreeMode && targetType.value === "entity" ? targetId.value : undefined,
    promptText: positivePrompt.value.trim(),
    extraPrompt: positivePrompt.value.trim(),
    negativePrompt: negativePrompt.value.trim() || undefined,
    promptPack: promptPack.value || undefined,
    templateId: templateId.value || undefined,
    modifierRefs: [...modifierRefs.value],
    commercialMode: commercialMode.value,
    size: size.value,
    quality: quality.value,
    batchCount: batchCount.value,
    baseUrl: boundRoot ? summary.value?.illustrationConfig.baseUrl || undefined : settings.value?.workspaceIllustration.baseUrl || undefined,
    responseModel: responseModel.value,
    outputName: outputName.value.trim() || undefined,
    inputImages: mode.value === "image-to-image" || mode.value === "inpaint" ? [inputImagePath.value.trim()] : [],
    maskPath: mode.value === "inpaint" ? maskPath.value.trim() || undefined : undefined,
  };
}

function buildIllustrationFormData() {
  const request = buildIllustrationRequest();
  const body = new FormData();
  const usesInputImage = mode.value === "image-to-image" || mode.value === "inpaint";
  const usesMask = mode.value === "inpaint";
  if (request.root) {
    body.append("root", request.root);
  }
  if (request.targetType) {
    body.append("targetType", request.targetType);
  }
  if (request.manualTargetName) {
    body.append("manualTargetName", request.manualTargetName);
  }
  if (request.textDesignMode) {
    body.append("textDesignMode", request.textDesignMode);
  }
  if (request.titleText) {
    body.append("titleText", request.titleText);
  }
  if (request.subtitleText) {
    body.append("subtitleText", request.subtitleText);
  }
  if (request.bodyText) {
    body.append("bodyText", request.bodyText);
  }
  if (request.fontStyleHint) {
    body.append("fontStyleHint", request.fontStyleHint);
  }
  body.append("mode", request.mode);
  if (request.chapterId) {
    body.append("chapterId", request.chapterId);
  }
  if (request.entityId) {
    body.append("entityId", request.entityId);
  }
  if (request.promptText) {
    body.append("promptText", request.promptText);
    body.append("extraPrompt", request.promptText);
  }
  if (request.negativePrompt) {
    body.append("negativePrompt", request.negativePrompt);
  }
  if (request.promptPack) {
    body.append("promptPack", request.promptPack);
  }
  if (request.useCase) {
    body.append("useCase", request.useCase);
  }
  if (request.templateId) {
    body.append("templateId", request.templateId);
  }
  for (const item of request.modifierRefs || []) {
    body.append("modifierRefs", item);
  }
  if (request.commercialMode) {
    body.append("commercialMode", request.commercialMode);
  }
  if (request.size) {
    body.append("size", request.size);
  }
  if (request.quality) {
    body.append("quality", request.quality);
  }
  if (request.batchCount && request.batchCount > 1) {
    body.append("batchCount", String(request.batchCount));
  }
  if (request.responseModel) {
    body.append("responseModel", request.responseModel);
  }
  if (request.baseUrl) {
    body.append("baseUrl", request.baseUrl);
  }
  if (request.outputName) {
    body.append("outputName", request.outputName);
  }
  if (usesInputImage) {
    if (inputImageFile.value) {
      body.append("inputImageFile", inputImageFile.value);
    } else if (request.inputImages?.[0]) {
      body.append("inputImagePath", request.inputImages[0]);
    }
  }
  if (usesMask) {
    if (maskFile.value) {
      body.append("maskFile", maskFile.value);
    } else if (request.maskPath) {
      body.append("maskPath", request.maskPath);
    }
  }
  return body;
}

function applyHistoryItem(item: IllustrationRecord) {
  workspaceMode.value = "illustration";
  const nextTargetType = item.targetRef?.type === "entity" || item.entityId ? "entity" : "chapter";
  const nextPromptPack = resolveHistoryPromptPack(item) || promptPack.value;
  targetType.value = nextTargetType;
  targetId.value = item.targetRef?.targetId || item.chapterId || item.entityId || "";
  mode.value = item.mode === "image-to-image" || item.mode === "inpaint" ? item.mode : "text-to-image";
  promptPack.value = nextPromptPack;
  useCase.value = resolveHistoryUseCase(item, nextPromptPack, nextTargetType);
  templateId.value = item.templateId || item.promptSnapshot?.templateRef || "";
  modifierRefs.value = [...(item.promptSnapshot?.modifierRefs || item.modifierRefs || [])];
  commercialMode.value = item.commercialMode || item.policySnapshot?.commercialMode || "personal";
  textDesignMode.value = item.promptSnapshot?.textDesign?.mode === "designed" ? "designed" : "none";
  titleText.value = item.promptSnapshot?.textDesign?.titleText || "";
  subtitleText.value = item.promptSnapshot?.textDesign?.subtitleText || "";
  bodyText.value = item.promptSnapshot?.textDesign?.bodyText || "";
  fontStyleHint.value = item.promptSnapshot?.textDesign?.fontStyleHint || "";
  batchCount.value = item.batch?.count || 1;
  outputName.value = item.filePath?.split(/[\\/]/).pop() || "";
  positivePrompt.value = item.promptSnapshot?.userExtraPrompt || item.promptText || "";
  negativePrompt.value = item.policySnapshot?.negativePrompt || "";
  lastAutoPrompt.value = "";
  lastAutoNegativePrompt.value = "";
  clearInputImageSelection();
  clearMaskSelection();
  inputImagePath.value = item.inputImages?.[0] || "";
  maskPath.value = item.maskPath || "";
  errorMessage.value = "";
  dryRunResult.value = null;
  generateResult.value = null;
  activePreviewRecord.value = item;
}

function resolveHistoryPromptPack(item: IllustrationRecord): string {
  const packId = item.promptSnapshot?.packRef?.packId || item.promptPackRef?.packId;
  if (!packId) {
    return "";
  }
  const match = availablePromptPacks.value.find((pack) => pack.id === packId || pack.name === packId);
  return match?.name || "";
}

function resolveHistoryUseCase(item: IllustrationRecord, packName: string, target: IllustrationTargetType): string {
  if (item.useCase) {
    return item.useCase;
  }
  const templateRef = item.templateId || item.promptSnapshot?.templateRef || "";
  if (templateRef) {
    const pack = availablePromptPacks.value.find((entry) => entry.name === packName);
    const matchedTemplate = pack?.templates.find((template) => template.id === templateRef);
    if (matchedTemplate?.useCase) {
      return matchedTemplate.useCase;
    }
  }
  return getIllustrationDefaultUseCase(target);
}

function toggleModifier(modifierId: string) {
  if (modifierRefs.value.includes(modifierId)) {
    modifierRefs.value = modifierRefs.value.filter((item) => item !== modifierId);
    return;
  }
  modifierRefs.value = [...modifierRefs.value, modifierId];
}

function buildEntityPromptSeed(entity: EntityRecord | null): string {
  if (!entity) {
    return "";
  }
  const currentStateText =
    typeof entity.currentState === "string"
      ? entity.currentState
      : entity.currentState && typeof entity.currentState === "object"
        ? Object.values(entity.currentState)
            .map((item) => String(item ?? "").trim())
            .filter(Boolean)
            .join("；")
        : "";
  const fragments = [entity.appearanceSummary || "", currentStateText, entity.summary || ""]
    .map((item) => item.trim())
    .filter(Boolean);
  return fragments.slice(0, 3).join("；");
}

function applySuggestedPrompt(force = false) {
  const nextPrompt = targetType.value === "entity" ? buildEntityPromptSeed(selectedEntity.value) : "";
  if (!force && positivePrompt.value.trim() && positivePrompt.value !== lastAutoPrompt.value) {
    return;
  }
  positivePrompt.value = nextPrompt;
  lastAutoPrompt.value = nextPrompt;
}

function applySuggestedNegativePrompt(force = false) {
  const nextPrompt = defaultNegativePrompt.value.trim();
  if (!force && negativePrompt.value.trim() && negativePrompt.value !== lastAutoNegativePrompt.value) {
    return;
  }
  negativePrompt.value = nextPrompt;
  lastAutoNegativePrompt.value = nextPrompt;
}

async function handleDryRun() {
  errorMessage.value = "";
  submitting.value = true;
  try {
    const request = buildIllustrationRequest();
    const form = buildIllustrationFormData();
    const useMultipart =
      (mode.value === "image-to-image" || mode.value === "inpaint") &&
      (Boolean(inputImageFile.value) || Boolean(maskFile.value));
    activePreviewRecord.value = null;
    generateResult.value = null;
    dryRunResult.value = useMultipart ? await dryRunIllustrationForm(form) : await dryRunIllustration(request);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    submitting.value = false;
  }
}

async function handleGenerate() {
  errorMessage.value = "";
  if (illustrationSetupWarning.value) {
    errorMessage.value = illustrationSetupWarning.value;
    return;
  }
  submitting.value = true;
  try {
    const request = buildIllustrationRequest();
    const form = buildIllustrationFormData();
    const useMultipart =
      (mode.value === "image-to-image" || mode.value === "inpaint") &&
      (Boolean(inputImageFile.value) || Boolean(maskFile.value));
    activePreviewRecord.value = null;
    dryRunResult.value = null;
    generateResult.value = useMultipart ? await generateIllustrationForm(form) : await generateIllustration(request);
    await workspace.refreshSummary();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    submitting.value = false;
  }
}

function revokePreviewUrl(url: string) {
  if (url.startsWith("blob:")) {
    URL.revokeObjectURL(url);
  }
}

function clearInputImageSelection() {
  revokePreviewUrl(inputImagePreviewUrl.value);
  inputImagePreviewUrl.value = "";
  inputImageFile.value = null;
}

function clearMaskSelection() {
  revokePreviewUrl(maskPreviewUrl.value);
  maskPreviewUrl.value = "";
  maskFile.value = null;
}

function handleInputImageChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0] || null;
  clearInputImageSelection();
  if (!file) {
    return;
  }
  inputImageFile.value = file;
  inputImagePath.value = "";
  inputImagePreviewUrl.value = URL.createObjectURL(file);
}

function handleMaskChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0] || null;
  clearMaskSelection();
  if (!file) {
    return;
  }
  maskFile.value = file;
  maskPath.value = "";
  maskPreviewUrl.value = URL.createObjectURL(file);
}

function clearInputAsset(kind: "input" | "mask") {
  if (kind === "input") {
    clearInputImageSelection();
    inputImagePath.value = "";
    return;
  }
  clearMaskSelection();
  maskPath.value = "";
}

watch(
  chapterList,
  (items) => {
    chapterOrderIds.value = syncTreeOrder(chapterOrderIds.value, items.map((item) => item.id));
    if (items.length === 0) {
      selectedChapter.value = null;
      return;
    }
    if (!selectedChapter.value || !items.some((item) => item.id === selectedChapter.value?.id)) {
      selectedChapter.value = applyTreeOrder(items, chapterOrderIds.value)[0] || null;
    }
  },
  { immediate: true }
);

watch(
  () =>
    [
      workspaceMode.value,
      selectedChapter.value?.title || "",
      selectedChapter.value?.reviewScore || 0,
      selectedChapter.value?.wordCount || 0,
      targetType.value,
      currentTargetLabel.value,
      currentPackLabel.value,
      currentModeLabel.value,
      size.value,
      batchCount.value,
    ] as const,
  ([currentMode, chapterTitle, reviewScore, wordCount, currentTargetType, targetLabel, packLabel, modeLabel, currentSize, currentBatch]) => {
    if (currentMode === "review") {
      emit("workspace-status", {
        contextLabel: "章节",
        contextValue: chapterTitle || "未选择章节",
        detailLabel: "评分",
        detailValue: chapterTitle ? `${reviewScore} 分` : "-",
        auxLabel: "字数",
        auxValue: chapterTitle ? `${wordCount} 字` : "-",
      });
      return;
    }
    emit("workspace-status", {
      contextLabel: currentTargetType === "entity" ? "角色" : "场景",
      contextValue: targetLabel || "未选择目标",
      detailLabel: "模板包",
      detailValue: packLabel || "-",
      auxLabel: "出图",
      auxValue: `${modeLabel} · ${currentSize} · x${currentBatch}`,
    });
  },
  { immediate: true }
);

watch(
  entityList,
  (items) => {
    entityOrderIds.value = syncTreeOrder(entityOrderIds.value, items.map((item) => item.id));
  },
  { immediate: true }
);

watch(
  () => [targetType.value, targetOptions.value] as const,
  ([kind, options]) => {
    if (!summary.value) {
      targetId.value = "";
      if (!manualTargetName.value.trim()) {
        manualTargetName.value = kind === "entity" ? "自由角色" : "自由场景";
      }
      return;
    }
    if (options.length === 0) {
      targetId.value = "";
      return;
    }
    if (!options.some((item) => item.value === targetId.value)) {
      if (kind === "chapter") {
        targetId.value = summary.value?.project.activeChapterId || String(options[0].value);
      } else {
        targetId.value = String(options[0].value);
      }
    }
  },
  { immediate: true }
);

watch(
  () => [targetType.value, targetId.value, selectedEntity.value?.id || "", summary.value?.project.root || ""] as const,
  () => {
    applySuggestedPrompt(false);
  },
  { immediate: true }
);

watch(
  () => [packTemplates.value, targetType.value, mode.value, useCase.value] as const,
  ([templates, kind, currentMode, currentUseCase]) => {
    const nextUseCase = pickIllustrationUseCase(templates, kind, currentMode, currentUseCase);
    if (nextUseCase !== useCase.value) {
      useCase.value = nextUseCase;
      return;
    }
    const nextTemplateId = pickIllustrationTemplateId(templates, currentMode, nextUseCase, templateId.value);
    if (nextTemplateId !== templateId.value) {
      templateId.value = nextTemplateId;
    }
    modifierRefs.value = modifierRefs.value.filter((item) => modifierOptions.value.some((option) => option.id === item));
  },
  { immediate: true, deep: true }
);

watch(
  () => [templateId.value, modifierRefs.value.join("|")] as const,
  () => {
    applySuggestedNegativePrompt(false);
  },
  { immediate: true }
);

watch(
  () => workspace.error.value,
  (value) => {
    if (value) {
      errorMessage.value = value;
    }
  }
);

watch(
  () => summary.value?.project.root || "",
  (root) => {
    void refreshPromptPackLibrary(root);
  },
  { immediate: true }
);

watch(
  selectedPromptPackDocument,
  (pack) => {
    if (!pack) {
      if (!promptPackDraft.value) {
        startNewPromptPackDraft();
      }
      return;
    }
    if (!promptPackDraft.value || promptPackDraftMode.value === "edit") {
      applyPromptPackDraft(pack, String(pack.source || "").trim() === "builtin" ? "copy" : "edit");
    }
  },
  { immediate: true }
);

watch(
  isMobileLayout,
  (mobile) => {
    if (mobile) {
      sidebarGroupOpen.reviewEntities = false;
      sidebarGroupOpen.reviewReference = false;
      sidebarGroupOpen.illustrationHistory = false;
    }
  },
  { immediate: true }
);

watch(
  () => [summary.value?.project.root || "", settings.value?.workspaceIllustration.promptPackName || ""] as const,
  ([root]) => {
    if (root === syncedProjectRoot.value && (root || !settings.value?.workspaceIllustration)) {
      return;
    }
    syncedProjectRoot.value = root;
    syncFromProject();
  },
  { immediate: true }
);

function buildProjectOptionLabel(item: ProjectOption): string {
  const sourceLabel = item.source === "recent" ? "最近" : "项目";
  return item.genre ? `${item.title} · ${item.genre} · ${sourceLabel}` : `${item.title} · ${sourceLabel}`;
}

function syncTreeOrder(current: string[], latest: string[]): string[] {
  const latestSet = new Set(latest);
  const kept = current.filter((item) => latestSet.has(item));
  const keptSet = new Set(kept);
  const appended = latest.filter((item) => !keptSet.has(item));
  return [...kept, ...appended];
}

function moveTreeItem(ids: string[], draggedId: string, targetId: string): string[] {
  const next = [...ids];
  const fromIndex = next.indexOf(draggedId);
  const toIndex = next.indexOf(targetId);
  if (fromIndex < 0 || toIndex < 0) {
    return ids;
  }
  next.splice(fromIndex, 1);
  next.splice(toIndex, 0, draggedId);
  return next;
}

function applyTreeOrder<T extends { id: string }>(items: T[], orderIds: string[]): T[] {
  const lookup = new Map(items.map((item) => [item.id, item]));
  const ordered = orderIds.map((id) => lookup.get(id)).filter((item): item is T => Boolean(item));
  const seen = new Set(ordered.map((item) => item.id));
  const extra = items.filter((item) => !seen.has(item.id));
  return [...ordered, ...extra];
}

function flattenProtocolEntries(source: Record<string, unknown> | undefined, prefix = "", depth = 0): ProtocolEntry[] {
  if (!source || typeof source !== "object") {
    return [];
  }

  return Object.entries(source).flatMap(([rawKey, rawValue]) => {
    if (rawValue === null || rawValue === undefined || rawValue === "") {
      return [];
    }

    const label = prefix ? `${prefix} / ${formatKey(rawKey)}` : formatKey(rawKey);

    if (!Array.isArray(rawValue) && typeof rawValue === "object" && depth < 1) {
      return flattenProtocolEntries(rawValue as Record<string, unknown>, label, depth + 1);
    }

    return [{ label, value: formatValue(rawValue) }];
  });
}

function formatKey(value: string): string {
  return value
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/[_-]+/g, " ")
    .trim();
}

function formatValue(value: unknown): string {
  if (Array.isArray(value)) {
    return value
      .map((item) => formatValue(item))
      .filter(Boolean)
      .join(" / ");
  }
  if (typeof value === "object" && value !== null) {
    return JSON.stringify(value, null, 0);
  }
  return String(value);
}
</script>

<style scoped>
.workbench-shell {
  display: grid;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.review-grid,
.illustration-grid-separated {
  display: grid;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.review-grid {
  grid-template-columns: var(--workbench-side-width) minmax(0, 1fr);
  gap: 0;
}

.illustration-grid-separated {
  grid-template-columns: var(--workbench-side-width) minmax(0, 1fr);
  gap: 0;
}

.review-column,
.illustration-column {
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

.review-column-main,
.illustration-column-editor {
  grid-template-rows: minmax(0, 1fr);
  min-width: 0;
  background: var(--surface);
}

.illustration-column-side {
  grid-template-rows: minmax(0, 1fr);
  width: var(--workbench-side-width);
  min-width: var(--workbench-side-width);
  max-width: var(--workbench-side-width);
  background: var(--surface-side);
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
  display: flex;
  align-items: center;
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
.workspace-parameter-grid :deep(.t-select),
.workspace-parameter-grid :deep(.t-input-number) {
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
.section-row,
.action-head,
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

.workspace-tree-item-static {
  cursor: default;
  opacity: 0.8;
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
.inline-link-button {
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

.focus-summary,
.detail-copy,
.result-text {
  color: var(--muted);
}

.focus-summary {
  margin: 0;
  line-height: 1.55;
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

.section-title,
.result-path {
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
.action-stack,
.compact-list,
.fact-list {
  display: grid;
  gap: 8px;
}

.action-item,
.result-card,
.prompt-seed-panel,
.compact-fact {
  display: grid;
  gap: 6px;
  padding: 6px 0 6px 10px;
  border-left: 2px solid #dbe2ea;
  background: transparent;
}

.action-item p,
.result-text {
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
.illustration-template-workspace :deep(.t-input-number),
.illustration-template-workspace :deep(.t-radio-button),
.illustration-template-side :deep(.t-input__wrap),
.illustration-template-side :deep(.t-textarea__inner),
.illustration-template-side :deep(.t-select__wrap),
.illustration-template-side :deep(.t-input-number),
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
.template-source-label,
.template-panel-label,
.run-status-row,
.preview-pane label,
.workspace-inline-field label,
.prompt-field-head label,
.prompt-field-head button,
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
.workspace-inline-field :deep(.t-input-number),
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

.template-source-stack,
.template-source-group,
.template-panel,
.prompt-field,
.preview-pane {
  display: grid;
  gap: 8px;
}

.template-source-group {
  padding-top: 8px;
  border-top: 1px solid rgba(31, 35, 41, 0.06);
}

.template-source-group:first-child {
  padding-top: 0;
  border-top: 0;
}

.template-pack-row,
.template-item-list,
.modifier-token-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.template-pack-button,
.template-item-button,
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

.template-pack-button:hover,
.template-item-button:hover,
.modifier-token:hover {
  border-color: rgba(0, 82, 217, 0.35);
  background: #f7faff;
}

.template-pack-button.is-active,
.template-item-button.is-active,
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

.template-editor-stack,
.template-editor-section,
.modifier-editor-list {
  display: grid;
  gap: 10px;
}

.template-editor-dialog-body {
  display: grid;
  gap: 12px;
  max-height: 70vh;
  overflow: auto;
}

.template-editor-dialog-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.template-editor-subhead,
.template-editor-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.template-editor-subhead {
  align-items: flex-start;
}

.template-editor-grid,
.modifier-editor-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 12px;
}

.template-editor-wide,
.modifier-editor-wide {
  grid-column: 1 / -1;
}

.template-editor-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: 12px;
}

.template-editor-checkbox input {
  margin: 0;
}

.template-editor-link {
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--accent);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.template-editor-link.danger {
  color: #b42318;
}

.modifier-editor-row {
  padding: 10px 0;
  border-top: 1px solid rgba(31, 35, 41, 0.06);
}

.modifier-editor-row:first-child {
  padding-top: 0;
  border-top: 0;
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

.prompt-seed-panel {
  gap: 4px;
}

.prompt-seed-panel strong {
  font-size: 12px;
  font-weight: 600;
}

.prompt-seed-panel p {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}

.prompt-editor {
  min-height: 100%;
}

.modifier-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.modifier-chip {
  margin: 0;
  padding: 8px 10px;
  border: 1px solid var(--line);
  background: transparent;
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

@media (max-width: 1440px) {
  .illustration-grid-separated {
    grid-template-columns: var(--workbench-side-width) minmax(0, 1fr);
  }
}

@media (max-width: 1180px) {
  .workbench-shell {
    min-height: 100%;
    overflow: visible;
  }

  .review-grid,
  .illustration-grid-separated,
  .protocol-inline,
  .workspace-project-import-row,
  .workspace-project-create-row,
  .modifier-grid,
  .template-panel-grid,
  .prompt-block-grid,
  .preview-grid,
  .template-editor-grid,
  .modifier-editor-row {
    grid-template-columns: 1fr;
  }

  .illustration-editor-layout {
    grid-template-columns: minmax(0, 1fr) minmax(260px, 0.78fr);
  }

  .review-workspace {
    grid-template-columns: minmax(0, 1fr) 260px;
  }

  .review-grid,
  .illustration-grid-separated {
    overflow: visible;
  }

  .illustration-column-side,
  .review-column-nav {
    grid-template-rows: auto;
    width: auto;
    min-width: 0;
    max-width: none;
  }

  .review-column,
  .illustration-column,
  .review-column-main,
  .illustration-column-editor,
  .review-editor-pane,
  .review-inspector-pane,
  .review-sections,
  .illustration-form,
  .workspace-nav,
  .chapter-content {
    overflow: visible;
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
  .illustration-editor-layout,
  .review-workspace {
    grid-template-columns: 1fr;
  }

  .review-inspector-pane {
    border-left: 0;
    border-top: 1px solid rgba(31, 35, 41, 0.08);
    padding-top: 12px;
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
  .workbench-shell {
    padding-bottom: 12px;
  }

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

  .chapter-content {
    padding: 12px;
    font-size: 13px;
    line-height: 1.7;
  }

  .workspace-block,
  .workbench-sidebar-section {
    padding-left: 8px;
    padding-right: 8px;
  }

  .template-editor-actions,
  .template-editor-meta,
  .workspace-block-head,
  .run-status-row {
    flex-wrap: wrap;
  }
}
</style>
