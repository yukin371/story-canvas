<template>
  <t-drawer
    :visible="visible"
    header="模板管理"
    :width="520"
    placement="right"
    :close-on-overlay-click="true"
    :destroy-on-close="false"
    :footer="false"
    class="template-editor-dialog"
    @update:visible="handleVisibleChange"
  >
    <div class="template-editor-dialog-body">
      <div class="template-editor-dialog-toolbar">
        <span class="workspace-plain-meta">{{ promptPackDraftStateLabel }}</span>
        <div class="template-editor-actions">
          <button class="template-editor-link" type="button" @click="emit('new-pack')">新建模板包</button>
          <button class="template-editor-link" type="button" @click="emit('copy-current')">
            {{ currentPackSourceLabel === "系统模板" ? "复制当前系统模板" : "编辑当前用户模板" }}
          </button>
        </div>
      </div>
      <div v-if="promptPackDraft" class="template-editor-stack">
        <div class="template-editor-grid">
          <div class="workspace-inline-field">
            <label>模板包名称</label>
            <t-input v-model="promptPackDraft.label" placeholder="例如：项目角色模板" />
          </div>
          <div class="workspace-inline-field">
            <label>文件名</label>
            <t-input :model-value="fileName" placeholder="例如：project-character-pack" @update:model-value="handleFileNameChange" />
          </div>
          <div class="workspace-inline-field template-editor-wide">
            <label>说明</label>
            <t-input v-model="promptPackDraft.description" placeholder="简短说明这个模板包适合什么场景。" />
          </div>
        </div>
        <label v-if="summaryExists" class="template-editor-checkbox">
          <input :checked="setAsDefault" type="checkbox" @change="handleSetAsDefaultChange" />
          <span>保存后设为当前项目默认模板包</span>
        </label>
        <div class="template-editor-section">
          <div class="template-editor-subhead">
            <strong>模板条目</strong>
            <button class="template-editor-link" type="button" @click="emit('add-template')">添加模板</button>
          </div>
          <div class="template-item-list">
            <button
              v-for="item in promptPackDraft.templates"
              :key="`${item.id || 'draft'}-${item.useCase}-${item.mode}-${item.label}`"
              type="button"
              class="template-item-button"
              :class="{ 'is-active': item === promptPackDraftTemplate }"
              @click="emit('update:templateId', item.id)"
            >
              {{ item.label || item.id || "未命名模板" }}
            </button>
          </div>
          <div v-if="promptPackDraftTemplate" class="template-editor-grid">
            <div class="workspace-inline-field">
              <label>模板 ID</label>
              <t-input v-model="promptPackDraftTemplate.id" placeholder="scene-standard" />
            </div>
            <div class="workspace-inline-field">
              <label>显示名称</label>
              <t-input v-model="promptPackDraftTemplate.label" placeholder="章节场景图" />
            </div>
            <div class="workspace-inline-field">
              <label>用途</label>
              <t-select v-model="promptPackDraftTemplate.useCase" :options="ILLUSTRATION_KNOWN_USE_CASE_OPTIONS" />
            </div>
            <div class="workspace-inline-field">
              <label>模式</label>
              <t-select
                v-model="promptPackDraftTemplate.mode"
                :options="[
                  { label: '文生图', value: 'text-to-image' },
                  { label: '图生图', value: 'image-to-image' },
                  { label: '重绘', value: 'inpaint' },
                ]"
              />
            </div>
            <div class="workspace-inline-field">
              <label>默认负向策略</label>
              <t-select
                v-model="promptPackDraftTemplate.defaultNegativePolicyRef"
                :options="promptPackDraftNegativePolicyOptions"
                clearable
                placeholder="可留空"
              />
            </div>
            <div class="workspace-inline-field">
              <label>默认商用策略</label>
              <t-select
                v-model="promptPackDraftTemplate.defaultCommercialPolicyRef"
                :options="promptPackDraftCommercialPolicyOptions"
                clearable
                placeholder="可留空"
              />
            </div>
            <div class="workspace-inline-field template-editor-wide">
              <label>模板正文</label>
              <t-textarea
                v-model="promptPackDraftTemplate.promptTemplate"
                :autosize="{ minRows: 6, maxRows: 10 }"
                placeholder="{subject}&#10;{styleModifiers}&#10;{userExtraPrompt}"
              />
            </div>
          </div>
          <div class="template-editor-actions">
            <button
              v-if="promptPackDraftTemplate"
              class="template-editor-link danger"
              type="button"
              @click="emit('remove-template', promptPackDraftTemplate)"
            >
              删除当前模板
            </button>
          </div>
        </div>
        <div class="template-editor-section">
          <div class="template-editor-subhead">
            <strong>修饰词</strong>
            <button class="template-editor-link" type="button" @click="emit('add-modifier')">添加修饰词</button>
          </div>
          <div v-if="promptPackDraft.modifierGroups.length === 0" class="workspace-plain-meta">当前模板包还没有修饰词。</div>
          <div v-else class="modifier-editor-list">
            <div
              v-for="(item, index) in promptPackDraft.modifierGroups"
              :key="`${item.id || 'modifier'}-${index}`"
              class="modifier-editor-row"
            >
              <div class="workspace-inline-field">
                <label>ID</label>
                <t-input v-model="item.id" placeholder="style-cinematic" />
              </div>
              <div class="workspace-inline-field">
                <label>名称</label>
                <t-input v-model="item.label" placeholder="电影感" />
              </div>
              <div class="workspace-inline-field">
                <label>分组</label>
                <t-input v-model="item.group" placeholder="style" />
              </div>
              <div class="workspace-inline-field modifier-editor-wide">
                <label>正向片段</label>
                <t-textarea
                  v-model="item.promptFragment"
                  :autosize="{ minRows: 2, maxRows: 4 }"
                  placeholder="cinematic framing, layered depth"
                />
              </div>
              <div class="workspace-inline-field modifier-editor-wide">
                <label>负向片段</label>
                <t-textarea
                  v-model="item.negativeFragment"
                  :autosize="{ minRows: 2, maxRows: 4 }"
                  placeholder="可留空"
                />
              </div>
              <button class="template-editor-link danger" type="button" @click="emit('remove-modifier', index)">删除</button>
            </div>
          </div>
        </div>
        <div class="template-editor-section">
          <div class="template-editor-subhead">
            <strong>负向策略</strong>
            <button class="template-editor-link" type="button" @click="emit('add-negative-policy')">添加负向策略</button>
          </div>
          <div v-if="promptPackDraft.policies.negativePolicies.length === 0" class="workspace-plain-meta">当前模板包还没有负向策略。</div>
          <div v-else class="modifier-editor-list">
            <div
              v-for="(item, index) in promptPackDraft.policies.negativePolicies"
              :key="`${item.id || 'negative'}-${index}`"
              class="modifier-editor-row"
            >
              <div class="workspace-inline-field">
                <label>ID</label>
                <t-input v-model="item.id" placeholder="default-safe" />
              </div>
              <div class="workspace-inline-field">
                <label>名称</label>
                <t-input v-model="item.label" placeholder="默认负向" />
              </div>
              <div class="workspace-inline-field modifier-editor-wide">
                <label>负向提示词</label>
                <t-textarea
                  v-model="item.negativePrompt"
                  :autosize="{ minRows: 3, maxRows: 6 }"
                  placeholder="blurry, low quality, broken anatomy"
                />
              </div>
              <button class="template-editor-link danger" type="button" @click="emit('remove-negative-policy', index)">删除</button>
            </div>
          </div>
        </div>
        <div class="template-editor-section">
          <div class="template-editor-subhead">
            <strong>商用策略</strong>
            <button class="template-editor-link" type="button" @click="emit('add-commercial-policy')">添加商用策略</button>
          </div>
          <div v-if="promptPackDraft.policies.commercialPolicies.length === 0" class="workspace-plain-meta">当前模板包还没有商用策略。</div>
          <div v-else class="modifier-editor-list">
            <div
              v-for="(item, index) in promptPackDraft.policies.commercialPolicies"
              :key="`${item.id || 'commercial'}-${index}`"
              class="modifier-editor-row"
            >
              <div class="workspace-inline-field">
                <label>ID</label>
                <t-input v-model="item.id" placeholder="commercial-default" />
              </div>
              <div class="workspace-inline-field">
                <label>名称</label>
                <t-input v-model="item.label" placeholder="商用默认" />
              </div>
              <div class="workspace-inline-field">
                <label>模式</label>
                <t-select
                  v-model="item.mode"
                  :options="[
                    { label: '个人', value: 'personal' },
                    { label: '商用', value: 'commercial' },
                  ]"
                />
              </div>
              <div class="workspace-inline-field modifier-editor-wide">
                <label>附加提示词</label>
                <t-textarea
                  v-model="item.extraPrompt"
                  :autosize="{ minRows: 2, maxRows: 4 }"
                  placeholder="brand-safe presentation"
                />
              </div>
              <div class="workspace-inline-field modifier-editor-wide">
                <label>限制词</label>
                <t-input
                  :model-value="(item.restrictions || []).join(', ')"
                  placeholder="用逗号分隔，例如：no-logo-imitation, no-trademark-style-copy"
                  @update:model-value="
                    item.restrictions = String($event || '')
                      .split(',')
                      .map((value) => value.trim())
                      .filter(Boolean)
                  "
                />
              </div>
              <button class="template-editor-link danger" type="button" @click="emit('remove-commercial-policy', index)">删除</button>
            </div>
          </div>
        </div>
        <p v-if="promptPackLibraryError" class="inline-error">{{ promptPackLibraryError }}</p>
        <div class="detail-actions compact-actions">
          <t-button variant="outline" :disabled="savingPromptPackLibrary" @click="emit('reset')">重置</t-button>
          <t-button theme="primary" :loading="savingPromptPackLibrary" @click="emit('save')">保存用户模板</t-button>
        </div>
      </div>
    </div>
  </t-drawer>
</template>

<script setup lang="ts">
import { ILLUSTRATION_KNOWN_USE_CASE_OPTIONS, type PromptPackDocument, type PromptPackTemplateDocument } from "@/api/storyCanvas";
import { TButton } from "@/tdesign/button";
import { TDrawer } from "@/tdesign/drawer";
import { TInput } from "@/tdesign/input";
import { TSelect } from "@/tdesign/select";
import { TTextarea } from "@/tdesign/textarea";

defineProps<{
  visible: boolean;
  summaryExists: boolean;
  fileName: string;
  setAsDefault: boolean;
  templateId: string;
  promptPackDraftStateLabel: string;
  currentPackSourceLabel: string;
  promptPackDraft: PromptPackDocument | null;
  promptPackDraftTemplate: PromptPackTemplateDocument | null;
  promptPackDraftNegativePolicyOptions: Array<{ label: string; value: string }>;
  promptPackDraftCommercialPolicyOptions: Array<{ label: string; value: string }>;
  promptPackLibraryError: string;
  savingPromptPackLibrary: boolean;
}>();

const emit = defineEmits<{
  (event: "update:visible", value: boolean): void;
  (event: "update:fileName", value: string): void;
  (event: "update:setAsDefault", value: boolean): void;
  (event: "update:templateId", value: string): void;
  (event: "new-pack"): void;
  (event: "copy-current"): void;
  (event: "add-template"): void;
  (event: "remove-template", value: PromptPackTemplateDocument): void;
  (event: "add-modifier"): void;
  (event: "remove-modifier", value: number): void;
  (event: "add-negative-policy"): void;
  (event: "remove-negative-policy", value: number): void;
  (event: "add-commercial-policy"): void;
  (event: "remove-commercial-policy", value: number): void;
  (event: "reset"): void;
  (event: "save"): void;
}>();

function handleVisibleChange(value: boolean) {
  emit("update:visible", value);
}

function handleFileNameChange(value: string | number) {
  emit("update:fileName", String(value || ""));
}

function handleSetAsDefaultChange(event: Event) {
  emit("update:setAsDefault", Boolean((event.target as HTMLInputElement | null)?.checked));
}
</script>

<style scoped>
.workspace-plain-meta,
.workspace-inline-field label {
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
.workspace-inline-field :deep(.t-textarea) {
  width: 100%;
  min-width: 0;
}

.template-item-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.template-item-button {
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

.template-item-button:hover {
  border-color: rgba(0, 82, 217, 0.35);
  background: #f7faff;
}

.template-item-button.is-active {
  border-color: var(--accent);
  background: rgba(0, 82, 217, 0.08);
  color: #003f9f;
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

@media (max-width: 1180px) {
  .template-editor-grid,
  .modifier-editor-row {
    grid-template-columns: 1fr;
  }
}
</style>
