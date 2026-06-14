<script setup lang="ts">
import { ref } from "vue";
import type { LayoutEdge, LayoutResponse, TapOrderEntry } from "../../api/client";
import LayoutCanvas from "../LayoutCanvas.vue";
import { UiButton } from "../../ui";
import { useInfoPanelSplit } from "../../ui/interaction/useInfoPanelSplit";
import type { CanvasRegionTarget } from "../../ui/interaction/canvas/types";

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

const emit = defineEmits<{
  selectEdge: [id: string | null];
  compute: [];
}>();

const canvasRef = ref<InstanceType<typeof LayoutCanvas> | null>(null);
const stageBodyRef = ref<HTMLElement | null>(null);

const {
  infoHeight,
  atMax,
  onHandlePointerDown,
  onHandlePointerMove,
  onHandlePointerUp,
  closeInfo,
} = useInfoPanelSplit(stageBodyRef);

function edgeTypeLabel(type: string): string {
  if (type === "tap_chain") return "SBTO 链";
  return "传送带";
}

function onCanvasPrimary(target: CanvasRegionTarget): void {
  if (target.kind === "edge") {
    emit("selectEdge", target.id);
    return;
  }
  emit("selectEdge", null);
}
</script>

<template>
  <div class="workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">布局结果</h2>
      <UiButton variant="primary" :disabled="loading" @primary="emit('compute')">
        {{ loading ? "计算中…" : "计算自平衡布局" }}
      </UiButton>
    </div>

    <div ref="stageBodyRef" class="stage-body">
      <div class="stage-alerts">
        <p v-if="error" class="error">{{ error }}</p>
        <ul v-if="analysisWarnings.length" class="analysis-warn">
          <li v-for="(w, i) in analysisWarnings" :key="i">{{ w }}</li>
        </ul>
        <p v-if="stale && layout" class="stale-banner">产出或供给已变更，请重新计算布局。</p>
      </div>

      <div class="canvas-stack" :class="{ 'canvas-stack--at-max-info': atMax }">
        <div class="canvas-area">
          <LayoutCanvas
            v-if="layout"
            ref="canvasRef"
            :nodes="layout.nodes"
            :edges="layout.edges"
            :product-edges="layout.product_edges ?? []"
            :hidden-edges="layout.hidden_edges ?? []"
            :layout-direction="layout.layout_direction ?? 'left-to-right'"
            :selected-edge-id="selectedEdgeId"
            @primary="onCanvasPrimary"
          />
          <div v-else class="placeholder">选择产出目标后点击「计算自平衡布局」</div>

          <div class="handle-anchor">
            <div
              class="handle-cluster"
              :class="{
                'handle-cluster--expanded': infoHeight > 0,
                'handle-cluster--at-max': atMax,
              }"
            >
              <button
                type="button"
                class="handle-drag"
                aria-label="拖动调节信息区高度"
                @pointerdown="onHandlePointerDown"
                @pointermove="onHandlePointerMove"
                @pointerup="onHandlePointerUp"
                @pointercancel="onHandlePointerUp"
              />
              <button
                v-if="infoHeight > 0"
                type="button"
                class="handle-close"
                aria-label="关闭信息区"
                @click="closeInfo"
              >
                ×
              </button>
            </div>
          </div>
        </div>

        <div
          v-if="layout && infoHeight > 0"
          class="info-panel"
          :style="{ height: `${infoHeight}px` }"
        >
          <div class="info-panel__scroll">
            <div class="info-grid">
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
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workspace {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.workspace-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.workspace-title {
  margin: 0;
  font-size: 0.95rem;
  color: #e6edf3;
}

.stage-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.stage-alerts {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 8px;
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

.canvas-stack {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.canvas-stack--at-max-info .canvas-area {
  box-shadow: inset 0 2px 0 #388bfd;
}

.canvas-area {
  flex: 1;
  min-height: var(--shell-info-min-canvas);
  position: relative;
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

.handle-anchor {
  position: absolute;
  left: 50%;
  bottom: 6px;
  transform: translateX(-50%);
  z-index: 4;
  pointer-events: none;
}

.handle-cluster {
  pointer-events: auto;
  display: flex;
  align-items: stretch;
  height: var(--shell-handle-height);
  border-radius: 999px;
  overflow: hidden;
  border: 1px solid #484f58;
  background: #30363d;
  transition:
    border-color 0.12s ease,
    box-shadow 0.12s ease;
}

.handle-cluster--expanded {
  width: 72px;
}

.handle-cluster:not(.handle-cluster--expanded) {
  width: 36px;
}

.handle-cluster--at-max {
  border-color: #388bfd;
  box-shadow: 0 0 0 1px rgba(56, 139, 253, 0.35);
}

.handle-drag {
  flex: 3;
  padding: 0;
  border: none;
  background: transparent;
  cursor: ns-resize;
}

.handle-drag::after {
  content: "";
  display: block;
  width: 16px;
  height: 3px;
  margin: 0 auto;
  border-radius: 999px;
  background: #8b949e;
}

.handle-close {
  flex: 1;
  min-width: 0;
  padding: 0;
  border: none;
  border-left: 1px solid #484f58;
  background: #21262d;
  color: #8b949e;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
}

.handle-close:hover {
  background: #30363d;
  color: #e6edf3;
}

.info-panel {
  flex-shrink: 0;
  min-height: 0;
  border: 1px solid #30363d;
  border-top: none;
  border-radius: 0 0 8px 8px;
  background: #0d1117;
  overflow: hidden;
}

.info-panel__scroll {
  height: 100%;
  overflow-y: auto;
  padding: 12px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.tap-panel,
.detail-panel {
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
