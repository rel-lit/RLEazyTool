<script setup lang="ts">
import type { FactorioStatus, SaveInfo } from "../../api/client";
import { UiButton } from "../../ui";

defineProps<{
  factorioStatus: FactorioStatus | null;
  saves: SaveInfo[];
  selectedSave: string;
  progressLoading: boolean;
  purgeLoading: boolean;
  progressMsg: string;
  progressWarnings: string[];
  progressStale: boolean;
  activeSaveKey: string | null;
}>();

defineEmits<{
  "update:selectedSave": [value: string];
  import: [];
  purge: [];
}>();
</script>

<template>
  <section class="progress-section">
    <h2>存档进度</h2>
    <p v-if="factorioStatus" class="hint">
      数据目录：{{ factorioStatus.user_data_dir }}<br />
      存档数量：{{ factorioStatus.save_count }}<br />
      游戏：{{ factorioStatus.executable ?? "未检测到" }}
      <span v-if="factorioStatus.executable_source">（{{ factorioStatus.executable_source }}）</span>
    </p>
    <p v-if="progressStale && activeSaveKey" class="stale-banner">
      存档「{{ activeSaveKey }}」已在游戏中更新，当前列表仍为上次导入的进度。请点击下方按钮重新导入。
    </p>
    <select
      class="ui-select"
      :value="selectedSave"
      @change="$emit('update:selectedSave', ($event.target as HTMLSelectElement).value)"
    >
      <option v-if="!saves.length" value="">（未找到本地 .zip 存档）</option>
      <option v-for="s in saves" :key="s.path" :value="s.name">
        {{ s.name }}{{ s.is_last_played ? " · 最近" : "" }}{{ s.needs_reimport ? " · 需更新" : "" }}
      </option>
    </select>
    <UiButton
      variant="secondary"
      block
      class="import-main"
      :disabled="progressLoading || !selectedSave"
      @click="$emit('import')"
    >
      {{ progressLoading ? "导入中…" : "从存档导入（覆盖缓存）" }}
    </UiButton>
    <UiButton
      variant="secondary"
      block
      :disabled="purgeLoading || progressLoading"
      @click="$emit('purge')"
    >
      {{ purgeLoading ? "清理中…" : "清理过时缓存" }}
    </UiButton>
    <p class="hint">重新导入会启动游戏读取进度（使用临时副本，不修改原存档），并清空当前选中项与布局。</p>
    <p v-if="progressMsg" class="progress-msg">{{ progressMsg }}</p>
    <ul v-if="progressWarnings.length" class="warn-list">
      <li v-for="(w, i) in progressWarnings" :key="i">{{ w }}</li>
    </ul>
  </section>
</template>

<style scoped>
.progress-section select {
  margin-bottom: 4px;
}

.import-main {
  margin-top: 6px;
}

.hint {
  font-size: 12px;
  color: #8b949e;
  margin: 0 0 6px;
}

.progress-msg {
  font-size: 12px;
  color: #58a6ff;
  margin: 8px 0 0;
}

.warn-list {
  margin: 6px 0 0;
  padding-left: 18px;
  font-size: 11px;
  color: #f0883e;
}

.stale-banner {
  margin: 0 0 8px;
  padding: 8px 10px;
  background: #3d2a00;
  border: 1px solid #9e6a03;
  border-radius: 6px;
  color: #f0883e;
  font-size: 12px;
}

h2 {
  margin: 0 0 8px;
  font-size: 0.95rem;
}
</style>
