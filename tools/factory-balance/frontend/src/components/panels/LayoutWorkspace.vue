<script setup lang="ts">
import type { LayoutEdge, LayoutResponse, TapOrderEntry } from "../../api/client";
import LayoutCanvas from "../LayoutCanvas.vue";

defineProps<{
  layout: LayoutResponse | null;
  stale: boolean;
  loading: boolean;
  error: string;
  analysisWarnings: string[];
  selectedEdgeId: string | null;
  selectedEdge: LayoutEdge | null;
  selectedTap: TapOrderEntry | null;
}>();

defineEmits<{
  selectEdge: [id: string | null];
  compute: [];
}>();

function edgeTypeLabel(type: string): string {
  if (type === "detour") return "绕路";
  if (type === "tap_chain") return "SBTO 链";
  return "传送带";
}
</script>

<template>
  <div class="workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">布局结果</h2>
      <button class="primary" :disabled="loading" @click="$emit('compute')">
        {{ loading ? "计算中…" : "计算自平衡布局" }}
      </button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <ul v-if="analysisWarnings.length" class="analysis-warn">
      <li v-for="(w, i) in analysisWarnings" :key="i">{{ w }}</li>
    </ul>
    <p v-if="stale && layout" class="stale-banner">产出或供给已变更，请重新计算布局。</p>

    <div class="canvas-area">
      <LayoutCanvas
        v-if="layout"
        :nodes="layout.nodes"
        :edges="layout.edges"
        :product-edges="layout.product_edges ?? []"
        :hidden-edges="layout.hidden_edges ?? []"
        :layout-direction="layout.layout_direction ?? 'left-to-right'"
        :selected-edge-id="selectedEdgeId"
        @select-edge="$emit('selectEdge', $event)"
      />
      <div v-else class="placeholder">选择产出目标后点击「计算自平衡布局」</div>
    </div>

    <div v-if="layout" class="bottom">
      <div class="tap-panel">
        <h3>SBTO 取用顺序</h3>
        <div v-for="t in layout.tap_orders" :key="t.item" class="tap-row">
          <strong>{{ t.label }}</strong>
          <span>{{ t.order_labels.join(" → ") }}</span>
          <p>{{ t.explanation }}</p>
        </div>
        <p v-if="!layout.tap_orders.length" class="hint">当前链无共享带竞争。</p>
      </div>

      <div class="detail-panel">
        <h3>边详情</h3>
        <template v-if="selectedEdge">
          <p>
            <strong>{{ selectedEdge.label }}</strong>
            · {{ edgeTypeLabel(selectedEdge.type) }}
          </p>
          <p v-if="selectedEdge.tap_index">Tap 序号: {{ selectedEdge.tap_index }}</p>
          <p v-if="selectedEdge.note">{{ selectedEdge.note }}</p>
          <p v-if="selectedTap">{{ selectedTap.explanation }}</p>
        </template>
        <p v-else class="hint">点击图中的边查看 SBTO 说明</p>

        <h3 v-if="layout.warnings.length">警告</h3>
        <ul v-if="layout.warnings.length">
          <li v-for="(w, i) in layout.warnings" :key="i">{{ w }}</li>
        </ul>

        <h3>扩展占位</h3>
        <ul class="ext">
          <li v-for="(v, k) in layout.extensions" :key="k">
            {{ k }}: {{ (v as { placeholder?: string }).placeholder }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workspace {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.workspace-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.workspace-title {
  margin: 0;
  font-size: 0.95rem;
  color: #e6edf3;
}

.primary {
  background: #238636;
  border: none;
  color: #fff;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
}

.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  color: #f85149;
  font-size: 13px;
  margin: 0;
}

.analysis-warn {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  color: #f0883e;
}

.stale-banner {
  margin: 0;
  padding: 8px 12px;
  background: #3d2a00;
  border: 1px solid #9e6a03;
  border-radius: 6px;
  color: #f0883e;
  font-size: 13px;
}

.canvas-area {
  width: 100%;
  height: 480px;
  border: 1px solid #30363d;
  border-radius: 8px;
  overflow: hidden;
  background: #161b22;
}

.placeholder {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  color: #8b949e;
}

.bottom {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.tap-panel,
.detail-panel {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 12px;
  font-size: 13px;
}

.tap-panel h3,
.detail-panel h3 {
  margin: 0 0 8px;
  font-size: 0.95rem;
}

.tap-row {
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #21262d;
}

.tap-row p {
  margin: 4px 0 0;
  color: #8b949e;
}

.hint {
  font-size: 12px;
  color: #8b949e;
}

.ext {
  margin: 0;
  padding-left: 18px;
  color: #8b949e;
}
</style>
