<script setup lang="ts">
import { reactive, watch } from "vue";
import type { RecipeAssignmentPreview, RecipeKind } from "../../api/client";

const kindLabels: Record<RecipeKind, string> = {
  extraction: "世界抽取",
  manufacturing: "制造配方",
  smelting: "冶炼配方",
  chemistry: "化工配方",
  refining: "炼油配方",
  logistics: "物流配方",
  energy: "能源配方",
};

function kindLabel(kind: RecipeKind): string {
  return kindLabels[kind] ?? kind;
}

const props = defineProps<{
  items: RecipeAssignmentPreview[];
}>();

const emit = defineEmits<{
  (e: "confirm", assignments: Record<string, string>): void;
  (e: "cancel"): void;
}>();

const selections = reactive<Record<string, string>>({});

watch(
  () => props.items,
  (items) => {
    Object.keys(selections).forEach((k) => delete selections[k]);
    for (const item of items) {
      selections[item.item] = item.default_recipe;
    }
  },
  { immediate: true }
);

function confirm(): void {
  emit("confirm", { ...selections });
}

function cancel(): void {
  emit("cancel");
}
</script>

<template>
  <div class="recipe-modal-backdrop" @click.self="cancel">
    <div class="recipe-modal">
      <h3>存在多个可用配方/来源，请选择</h3>
      <div class="recipe-modal-list">
        <div v-for="entry in items" :key="entry.item" class="recipe-entry">
          <div class="recipe-entry-title">{{ entry.label }}</div>
          <div class="recipe-options">
            <label
              v-for="opt in entry.options"
              :key="opt.recipe_name"
              class="recipe-option"
              :class="{ active: selections[entry.item] === opt.recipe_name }"
            >
              <input
                v-model="selections[entry.item]"
                type="radio"
                :value="opt.recipe_name"
              />
              <span class="recipe-option-kind" :class="`kind-${opt.kind}`">
                {{ kindLabel(opt.kind) }}
              </span>
              <span class="recipe-option-label">{{ opt.label }}</span>
              <span class="recipe-option-line">{{ opt.line }}</span>
            </label>
          </div>
        </div>
      </div>
      <div class="recipe-modal-actions">
        <button class="btn-secondary" @click="cancel">取消</button>
        <button class="btn-primary" @click="confirm">确认并计算</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.recipe-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.recipe-modal {
  background: var(--panel-bg, #1e1e1e);
  color: var(--text, #eee);
  border-radius: 8px;
  padding: 20px;
  max-width: 640px;
  width: 90vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.recipe-modal h3 {
  margin: 0 0 16px;
  font-size: 18px;
}

.recipe-modal-list {
  overflow-y: auto;
  flex: 1;
  margin-bottom: 16px;
}

.recipe-entry {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.recipe-entry-title {
  font-weight: 600;
  margin-bottom: 8px;
}

.recipe-options {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.recipe-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid transparent;
}

.recipe-option:hover {
  background: rgba(255, 255, 255, 0.05);
}

.recipe-option.active {
  border-color: var(--accent, #42b983);
  background: rgba(66, 185, 131, 0.1);
}

.recipe-option input {
  margin: 0;
}

.recipe-option-kind {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
}

.kind-craft {
  background: #2c3e50;
}

.kind-extract {
  background: #2e4a2e;
}

.recipe-option-label {
  font-weight: 500;
}

.recipe-option-line {
  color: #aaa;
  font-size: 13px;
  margin-left: auto;
}

.recipe-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-primary,
.btn-secondary {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
}

.btn-primary {
  background: var(--accent, #42b983);
  color: #fff;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text, #eee);
}
</style>
