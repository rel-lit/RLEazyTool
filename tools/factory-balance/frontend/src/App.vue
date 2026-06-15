<script setup lang="ts">
import { provide, ref } from "vue";
import { useApp } from "./app/useApp";
import ItemTabsPanel from "./components/panels/ItemTabsPanel.vue";
import HistoryPanel from "./components/panels/HistoryPanel.vue";
import LayoutWorkspace from "./components/panels/LayoutWorkspace.vue";
import ModeToolbar from "./components/panels/ModeToolbar.vue";
import ProgressPanel from "./components/panels/ProgressPanel.vue";
import RecipeAssignmentModal from "./components/modals/RecipeAssignmentModal.vue";
import LeftSidebarShell, { type SidebarTab } from "./components/shell/LeftSidebarShell.vue";

const app = useApp();
provide("appBus", app.bus);

const leftSidebarTab = ref<SidebarTab>("save");

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

function onSidebarTabChange(tab: SidebarTab): void {
  leftSidebarTab.value = tab;
  if (tab === "history") {
    void app.layoutHistory.refresh();
  }
}
</script>

<template>
  <div class="app">
    <header class="header">
      <h1>异星自平衡布局计算器</h1>
      <p class="sub">纯布局 + SBTO · 存档进度同步 · v0.2</p>
    </header>

    <div class="shell-main">
      <LeftSidebarShell
        :active-tab="leftSidebarTab"
        @update:active-tab="onSidebarTabChange"
      >
        <ProgressPanel
          v-if="leftSidebarTab === 'save'"
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
      </LeftSidebarShell>

      <aside class="workspace-column panel">
        <div class="workspace-column__head">
          <ModeToolbar
            :catalog-mode="app.catalog.mode"
            :catalog-loading="app.catalog.loading"
            :progress-loading="app.importCtrl.loading"
            :progress-stale="app.session.progressStale"
            :supply-mode="app.selection.supplyMode"
            @switch-catalog-mode="app.switchCatalogMode($event)"
            @update:supply-mode="app.actions.setSupplyMode($event)"
          />
        </div>

        <ItemTabsPanel
          :target-search-query="app.catalog.targetSearchQuery"
          :supply-search-query="app.catalog.supplySearchQuery"
          :selected-targets="app.selection.selectedTargets"
          :supplied-items="app.selection.suppliedItems"
          :forbidden-items="app.selection.forbiddenItems"
          @update:target-search-query="app.catalog.targetSearchQuery = $event"
          @update:supply-search-query="app.catalog.supplySearchQuery = $event"
        />
      </aside>

      <section class="result-column panel">
        <LayoutWorkspace
          :layout="app.layout.layout"
          :stale="app.layout.stale"
          :loading="app.layout.loading"
          :error="app.layout.error"
          :analysis-warnings="app.layout.analysisWarnings"
          @compute="app.layout.compute()"
        />
      </section>
    </div>

    <RecipeAssignmentModal
      v-if="app.layout.pendingRecipePreview"
      :items="app.layout.pendingRecipePreview.items"
      @confirm="app.layout.confirmRecipeAssignments($event)"
      @cancel="app.layout.cancelRecipePreview()"
    />
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

.shell-main {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: stretch;
}

.panel {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 12px;
}

.workspace-column {
  width: var(--shell-workspace-width);
  flex-shrink: 0;
  margin-left: var(--shell-gap-after-tabs);
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  overflow: hidden;
}

.workspace-column__head {
  flex-shrink: 0;
}

.workspace-column :deep(.item-tabs) {
  flex: 1;
  min-height: 0;
}

.result-column {
  flex: 1;
  min-width: 0;
  min-height: 0;
  margin-left: var(--shell-gap-before-result);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 12px;
}
</style>
