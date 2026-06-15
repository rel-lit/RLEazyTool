<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";
import type { LayoutResponse } from "../../api/client";
import LayoutCanvas from "../LayoutCanvas.vue";
import { layoutInspectionKey } from "../../app/useApp";
import { UiButton } from "../../ui";
import { useInfoPanelSplit } from "../../ui/interaction/useInfoPanelSplit";

const props = defineProps<{
  layout: LayoutResponse | null;
  stale: boolean;
  loading: boolean;
  error: string;
  analysisWarnings: string[];
}>();

defineEmits<{
  compute: [];
}>();

const inspection = inject(layoutInspectionKey)!;

const canvasRef = ref<InstanceType<typeof LayoutCanvas> | null>(null);
const stageBodyRef = ref<HTMLElement | null>(null);

const {
  infoHeight,
  atMax,
  dragging,
  closeVisible,
  onHandlePointerDown,
  onHandlePointerMove,
  onHandlePointerUp,
  closeInfo,
} = useInfoPanelSplit(stageBodyRef);

const handleAtRest = computed(() => infoHeight.value === 0);
const handleShowClose = computed(
  () => closeVisible.value && !dragging.value && infoHeight.value > 0
);

const panelModel = computed(() => inspection.panelModel.value);

watch(
  () => props.layout,
  (layout) => {
    if (!layout) closeInfo();
  }
);
</script>

<template>
  <div class="workspace">
    <div class="workspace-header">
      <h2 class="workspace-title">布局结果</h2>
      <UiButton variant="primary" :disabled="loading" @primary="$emit('compute')">
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
        <div
          class="canvas-area"
          :class="{ 'canvas-area--info-open': layout && infoHeight > 0 }"
        >
          <LayoutCanvas
            v-if="layout"
            ref="canvasRef"
            :nodes="layout.nodes"
            :edges="layout.edges"
            :product-edges="layout.product_edges ?? []"
            :hidden-edges="layout.hidden_edges ?? []"
            :layout-direction="layout.layout_direction ?? 'left-to-right'"
          />
          <div v-else class="placeholder">选择产出目标后点击「计算自平衡布局」</div>
        </div>

        <div
          v-if="layout"
          class="drawer-handle-row"
          :class="{ 'drawer-handle-row--rest': handleAtRest }"
        >
          <div
            class="drawer-handle"
            :class="{
              'drawer-handle--with-close': handleShowClose,
              'drawer-handle--at-max': atMax,
            }"
          >
            <button
              type="button"
              class="drawer-handle__pull"
              :aria-label="infoHeight > 0 ? '拖动调节信息区高度' : '拖动展开信息区'"
              @pointerdown="onHandlePointerDown"
              @pointermove="onHandlePointerMove"
              @pointerup="onHandlePointerUp"
              @pointercancel="onHandlePointerUp"
            >
              <span class="drawer-handle__grip" aria-hidden="true">
                <span />
                <span />
                <span />
              </span>
            </button>
            <button
              v-if="handleShowClose"
              type="button"
              class="drawer-handle__close"
              aria-label="关闭信息区"
              @click="closeInfo"
            >
              ×
            </button>
          </div>
        </div>

        <div
          v-if="layout && infoHeight > 0"
          class="info-panel"
          :style="{ height: `${infoHeight}px` }"
        >
          <div class="info-panel__scroll">
            <div class="detail-panel">
              <h3>检视详情</h3>
              <template v-if="panelModel">
                <p class="detail-head">
                  <strong>{{ panelModel.title }}</strong>
                  <span class="detail-sub">{{ panelModel.badge }}</span>
                </p>
                <section
                  v-for="(sec, si) in panelModel.sections"
                  :key="si"
                  class="detail-section"
                >
                  <h4>{{ sec.heading }}</h4>
                  <p v-for="(line, li) in sec.lines" :key="'l' + li">{{ line }}</p>
                  <ul v-if="sec.bullets?.length">
                    <li v-for="(b, bi) in sec.bullets" :key="'b' + bi">{{ b }}</li>
                  </ul>
                </section>
              </template>
              <p v-else class="hint">点击图中的节点或边查看详情；拖动上方拉手展开本区</p>

              <h3 v-if="layout.warnings.length">警告</h3>
              <ul v-if="layout.warnings.length">
                <li v-for="(w, i) in layout.warnings" :key="i">{{ w }}</li>
              </ul>
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
  position: relative;
}

.canvas-stack--at-max-info .canvas-area {
  box-shadow: inset 0 2px 0 #388bfd;
}

.canvas-area {
  flex: 1;
  min-height: 0;
  position: relative;
  border: 1px solid #30363d;
  border-radius: 8px;
  overflow: hidden;
  background: #161b22;
}

.canvas-area--info-open {
  border-bottom: none;
  border-radius: 8px 8px 0 0;
}

.placeholder {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  color: #8b949e;
}

.drawer-handle-row {
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  align-items: flex-end;
  height: 0;
  position: relative;
  z-index: 4;
  pointer-events: none;
}

.drawer-handle-row--rest {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: auto;
}

.drawer-handle {
  pointer-events: auto;
  display: flex;
  width: var(--shell-handle-width);
  height: var(--shell-handle-height);
  border: 1px solid var(--ui-border-hover);
  border-bottom: none;
  border-radius: 8px 8px 0 0;
  background: var(--ui-bg-control);
  overflow: hidden;
  transition:
    border-color 0.12s ease,
    box-shadow 0.12s ease;
}

.drawer-handle-row:not(.drawer-handle-row--rest) .drawer-handle {
  margin-top: calc(-1 * var(--shell-handle-height));
}

.drawer-handle--with-close {
  display: grid;
  grid-template-columns: minmax(0, 1fr) var(--shell-handle-close-width);
}

.drawer-handle--at-max {
  border-color: var(--ui-border-accent);
  box-shadow: 0 0 0 1px rgba(56, 139, 253, 0.35);
}

.drawer-handle__pull {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  width: 100%;
  padding: 0 8px;
  border: none;
  background: transparent;
  cursor: ns-resize;
}

.drawer-handle--with-close .drawer-handle__pull {
  border-right: 1px solid var(--ui-border-hover);
}

.drawer-handle__grip {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 3px;
  width: 72%;
  max-width: 34px;
  min-width: 0;
}

.drawer-handle__grip span {
  display: block;
  height: 2px;
  border-radius: 999px;
  background: #8b949e;
  width: 100%;
}

.drawer-handle__close {
  width: var(--shell-handle-close-width);
  padding: 0;
  border: none;
  background: #161b22;
  color: #8b949e;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
}

.drawer-handle__close:hover {
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

.detail-panel {
  font-size: 13px;
}

.detail-panel h3 {
  margin: 0 0 8px;
  font-size: 0.95rem;
}

.detail-head {
  margin: 0 0 10px;
}

.detail-sub {
  display: block;
  font-size: 12px;
  color: #8b949e;
  font-weight: normal;
  margin-top: 2px;
}

.detail-section {
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #21262d;
}

.detail-section h4 {
  margin: 0 0 6px;
  font-size: 12px;
  color: #8b949e;
  font-weight: 600;
}

.detail-section p {
  margin: 0 0 4px;
}

.detail-section ul {
  margin: 4px 0 0;
  padding-left: 18px;
}

.hint {
  font-size: 12px;
  color: #8b949e;
}
</style>
