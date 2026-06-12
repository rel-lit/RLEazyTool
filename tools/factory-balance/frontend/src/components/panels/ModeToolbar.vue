<script setup lang="ts">
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
      <button
        type="button"
        class="sub-btn"
        :class="{ on: catalogMode === 'progress' }"
        :disabled="catalogLoading || progressLoading"
        @click="$emit('switchCatalogMode', 'progress')"
      >
        仅当前进度<span v-if="progressStale" class="dirty"> · 需更新</span>
      </button>
      <button
        type="button"
        class="sub-btn"
        :class="{ on: catalogMode === 'full' }"
        :disabled="catalogLoading || progressLoading"
        @click="$emit('switchCatalogMode', 'full')"
      >
        {{ catalogLoading && catalogMode !== "full" ? "加载中…" : "完整全配方" }}
      </button>
    </div>
    <div class="mode-group">
      <span class="mode-label">供给模式</span>
      <button
        type="button"
        class="sub-btn"
        :class="{ on: supplyMode === 'raw' }"
        @click="$emit('update:supplyMode', 'raw')"
      >
        原料模式
      </button>
      <button
        type="button"
        class="sub-btn"
        :class="{ on: supplyMode === 'direct' }"
        @click="$emit('update:supplyMode', 'direct')"
      >
        直接产物
      </button>
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

.sub-btn {
  flex-shrink: 0;
  background: #21262d;
  border: 1px solid #30363d;
  color: #8b949e;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
  white-space: nowrap;
  cursor: pointer;
}

.sub-btn.on {
  background: #1f3d5c;
  border-color: #388bfd;
  color: #58a6ff;
}

.sub-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.dirty {
  color: #f0883e;
  font-weight: 700;
}
</style>
