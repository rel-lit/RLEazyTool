<script setup lang="ts">
import { onMounted } from "vue";
import type { LayoutHistoryEntry } from "../../api/client";

const props = defineProps<{
  entries: LayoutHistoryEntry[];
  loading: boolean;
  error: string;
  activeSaveKey: string | null;
}>();

const emit = defineEmits<{
  refresh: [];
  restore: [id: number];
  remove: [id: number];
  clearAll: [];
}>();

onMounted(() => emit("refresh"));

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function supplyLabel(mode: string): string {
  return mode === "direct" ? "直接产物" : "原料";
}
</script>

<template>
  <section class="history-section">
    <h2>布局历史</h2>
    <p class="hint">
      按产出/供给配置 upsert 快照（含拖动坐标）；同一配置覆盖更新。
      <span v-if="activeSaveKey">当前存档：{{ activeSaveKey }}</span>
    </p>

    <div class="toolbar">
      <button type="button" class="secondary" :disabled="loading" @click="emit('refresh')">
        {{ loading ? "加载中…" : "刷新列表" }}
      </button>
      <button
        type="button"
        class="secondary danger"
        :disabled="loading || !entries.length"
        @click="emit('clearAll')"
      >
        清空全部
      </button>
    </div>

    <p v-if="error" class="error-msg">{{ error }}</p>

    <ul v-if="entries.length" class="history-list">
      <li v-for="row in entries" :key="row.id" class="history-item">
        <div class="history-item-head">
          <strong>{{ row.target_summary }}</strong>
          <span class="time">{{ formatTime(row.updated_at) }}</span>
        </div>
        <div class="meta">
          {{ row.node_count }} 节点 · {{ row.edge_count }} 边 · {{ row.tap_count }} SBTO
          · {{ supplyLabel(row.supply_mode) }}
          <span v-if="row.save_key"> · {{ row.save_key }}</span>
        </div>
        <div class="actions">
          <button type="button" class="link" @click="emit('restore', row.id)">载入画布</button>
          <button type="button" class="link muted" @click="emit('remove', row.id)">删除</button>
        </div>
      </li>
    </ul>
    <p v-else-if="!loading" class="hint empty">尚无快照。计算布局、拖动节点或离开页面后会自动保存。</p>
  </section>
</template>

<style scoped>
.history-section h2 {
  margin: 0 0 8px;
  font-size: 0.95rem;
}

.hint {
  font-size: 12px;
  color: #8b949e;
  margin: 0 0 8px;
}

.hint.empty {
  margin-top: 12px;
}

.toolbar {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
}

.secondary {
  flex: 1;
  background: #21262d;
  border: 1px solid #388bfd;
  color: #58a6ff;
  padding: 6px 8px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
}

.secondary:disabled {
  opacity: 0.5;
}

.secondary.danger {
  border-color: #da3633;
  color: #f85149;
}

.history-list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: calc(100vh - 280px);
  overflow-y: auto;
}

.history-item {
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 8px 10px;
  margin-bottom: 8px;
  background: #0d1117;
}

.history-item-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: baseline;
  font-size: 13px;
}

.time {
  font-size: 11px;
  color: #8b949e;
  flex-shrink: 0;
}

.meta {
  font-size: 11px;
  color: #8b949e;
  margin-top: 4px;
}

.actions {
  margin-top: 6px;
  display: flex;
  gap: 12px;
}

.link {
  background: none;
  border: none;
  padding: 0;
  color: #58a6ff;
  font-size: 12px;
  cursor: pointer;
}

.link.muted {
  color: #8b949e;
}

.error-msg {
  font-size: 12px;
  color: #f85149;
  margin: 0 0 8px;
}
</style>
