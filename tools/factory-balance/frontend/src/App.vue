<script setup lang="ts">
import { provide, ref } from "vue";
import { useApp } from "./app/useApp";
import ItemTabsPanel from "./components/panels/ItemTabsPanel.vue";
import HistoryPanel from "./components/panels/HistoryPanel.vue";
import LayoutWorkspace from "./components/panels/LayoutWorkspace.vue";
import ModeToolbar from "./components/panels/ModeToolbar.vue";
import ProgressPanel from "./components/panels/ProgressPanel.vue";
import { UiButton } from "./ui";

const app = useApp();
provide("appBus", app.bus);

type LeftSidebar = "save" | "history";
const leftSidebar = ref<LeftSidebar>("save");

function showSave(): void {
  leftSidebar.value = "save";
}

function showHistory(): void {
  leftSidebar.value = "history";
  void app.layoutHistory.refresh();
}

async function restoreHistory(id: number): Promise<void> {
  await app.layoutHistory.loadRecord(id);
}

async function removeHistory(id: number): Promise<void> {
  await app.layoutHistory.remove(id);
}

async function clearHistory(): Promise<void> {
  if (!confirm("确定清空全部布局历史？")) return;
  await app.layoutHistory.clearAll();
}
</script>

<template>
  <div class="app">
    <header class="header">
      <h1>异星自平衡布局计算器</h1>
      <p class="sub">纯布局 + SBTO · 存档进度同步 · v0.2</p>
    </header>

    <div class="main">
      <div class="sidebar-group">
        <aside class="panel save-panel">
          <ProgressPanel
            v-if="leftSidebar === 'save'"
            :factorio-status="app.session.status"
            :saves="app.session.saves"
            :selected-save="app.savePicker.selectedSave"
            :progress-loading="app.importCtrl.loading"
            :purge-loading="app.purgeCtrl.loading"
            :progress-msg="app.status.message"
            :progress-warnings="app.status.warnings"
            :progress-stale="app.session.progressStale"
            :active-save-key="app.session.activeSaveKey"
            @update:selected-save="app.savePicker.selectedSave = $event"
            @import="app.importCtrl.importFromSave()"
            @purge="app.purgeCtrl.purge(true)"
          />
          <HistoryPanel
            v-else
            :entries="app.layoutHistory.entries"
            :loading="app.layoutHistory.loading"
            :error="app.layoutHistory.error"
            :active-save-key="app.session.activeSaveKey"
            @refresh="app.layoutHistory.refresh()"
            @restore="restoreHistory($event)"
            @remove="removeHistory($event)"
            @clear-all="clearHistory()"
          />
        </aside>

        <aside class="panel item-panel">
          <div class="item-panel-head">
            <div class="sidebar-switch">
              <UiButton
                variant="toggle"
                size="sm"
                :pressed="leftSidebar === 'save'"
                @click="showSave"
              >
                存档
              </UiButton>
              <UiButton
                variant="toggle"
                size="sm"
                :pressed="leftSidebar === 'history'"
                @click="showHistory"
              >
                历史
              </UiButton>
            </div>

            <ModeToolbar
              :catalog-mode="app.catalog.mode"
              :catalog-loading="app.catalog.loading"
              :progress-loading="app.importCtrl.loading"
              :progress-stale="app.session.progressStale"
              :supply-mode="app.selection.supplyMode"
              @switch-catalog-mode="app.switchCatalogMode($event)"
              @update:supply-mode="app.selection.supplyMode = $event"
            />
          </div>

          <ItemTabsPanel
            :target-search-query="app.catalog.targetSearchQuery"
            :supply-search-query="app.catalog.supplySearchQuery"
            :filtered-manufacture-items="app.catalog.filteredManufactureItems"
            :filtered-supply-items="app.catalog.filteredSupplyItems"
            :selected-targets="app.selection.selectedTargets"
            :supplied-items="app.selection.suppliedItems"
            :forbidden-items="app.selection.forbiddenItems"
            @update:target-search-query="app.catalog.targetSearchQuery = $event"
            @update:supply-search-query="app.catalog.supplySearchQuery = $event"
            @toggle-target="app.selection.toggleTarget($event)"
            @toggle-supplied="app.selection.toggleSupplied($event)"
            @toggle-forbidden="app.selection.toggleForbidden($event)"
            @clear-targets="app.selection.clearTargets()"
            @clear-supply-selections="app.selection.clearSupplySelections()"
          />
        </aside>
      </div>

      <section class="panel result-panel">
        <LayoutWorkspace
          :layout="app.layout.layout"
          :stale="app.layout.stale"
          :loading="app.layout.loading"
          :error="app.layout.error"
          :analysis-warnings="app.layout.analysisWarnings"
          :selected-edge-id="app.layout.selectedEdgeId"
          :selected-edge="app.layout.selectedEdge"
          :selected-tap="app.layout.selectedTap"
          @select-edge="app.layout.selectEdge($event)"
          @compute="app.layout.compute()"
        />
      </section>
    </div>
  </div>
</template>

<style scoped>
.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 16px 20px;
  overflow: hidden;
}

.header h1 {
  margin: 0;
  font-size: 1.5rem;
}

.sub {
  margin: 4px 0 16px;
  color: #8b949e;
  font-size: 0.9rem;
}

.main {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 12px;
  align-items: stretch;
}

.sidebar-group {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
  min-height: 0;
}

.panel {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 12px;
}

.save-panel {
  width: 260px;
  min-height: 0;
  overflow: hidden;
}

.item-panel {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  overflow: hidden;
}

.item-panel-head {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.item-panel :deep(.item-tabs) {
  flex: 1;
  min-height: 0;
}

.result-panel {
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow-y: auto;
}

.sidebar-switch {
  display: flex;
  gap: 6px;
}

.sidebar-switch :deep(.ui-btn) {
  flex: 1;
  min-width: 0;
}
</style>
