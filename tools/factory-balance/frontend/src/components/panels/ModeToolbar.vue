<script setup lang="ts">
import { UiButton } from "../../ui";

defineProps<{
  catalogMode: "progress" | "full";
  catalogLoading: boolean;
  progressLoading: boolean;
  progressStale: boolean;
  supplyMode: "raw" | "direct";
}>();

defineEmits<{
  switchCatalogMode: [mode: "progress" | "full"];
  "update:supplyMode": [value: "raw" | "direct"];
}>();
</script>

<template>
  <div class="mode-toolbar">
    <div class="mode-group">
      <span class="mode-label">数据源</span>
      <UiButton
        variant="toggle"
        size="sm"
        :pressed="catalogMode === 'progress'"
        :disabled="catalogLoading || progressLoading"
        @primary="$emit('switchCatalogMode', 'progress')"
      >
        仅当前进度<span v-if="progressStale" class="dirty"> · 需更新</span>
      </UiButton>
      <UiButton
        variant="toggle"
        size="sm"
        :pressed="catalogMode === 'full'"
        :disabled="catalogLoading || progressLoading"
        @primary="$emit('switchCatalogMode', 'full')"
      >
        {{ catalogLoading && catalogMode !== "full" ? "加载中…" : "完整全配方" }}
      </UiButton>
    </div>
    <div class="mode-group">
      <span class="mode-label">供给模式</span>
      <UiButton
        variant="toggle"
        size="sm"
        :pressed="supplyMode === 'raw'"
        @primary="$emit('update:supplyMode', 'raw')"
      >
        原料模式
      </UiButton>
      <UiButton
        variant="toggle"
        size="sm"
        :pressed="supplyMode === 'direct'"
        @primary="$emit('update:supplyMode', 'direct')"
      >
        直接产物
      </UiButton>
    </div>
  </div>
</template>

<style scoped>
.mode-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 16px;
  padding-bottom: 4px;
  border-bottom: 1px solid #21262d;
}

.mode-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.mode-label {
  font-size: 12px;
  color: #8b949e;
  flex-shrink: 0;
}

.dirty {
  color: #f0883e;
  font-weight: 700;
}
</style>
