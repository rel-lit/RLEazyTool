<script setup lang="ts">
import { ref, watch } from "vue";

export type SidebarTab = "save" | "history";

const TABS: ReadonlyArray<{ id: SidebarTab; label: string }> = [
  { id: "save", label: "存档" },
  { id: "history", label: "历史" },
];

const props = defineProps<{
  activeTab: SidebarTab;
}>();

const emit = defineEmits<{
  "update:activeTab": [tab: SidebarTab];
}>();

const contentCollapsed = ref(false);

watch(
  () => props.activeTab,
  () => {
    contentCollapsed.value = false;
  }
);

function onTabChange(tab: SidebarTab): void {
  emit("update:activeTab", tab);
}

function toggleCollapse(): void {
  contentCollapsed.value = !contentCollapsed.value;
}
</script>

<template>
  <div
    class="side-shell"
    :class="{ 'side-shell--collapsed': contentCollapsed }"
  >
    <aside
      v-show="!contentCollapsed"
      class="side-shell__pane"
      :aria-hidden="contentCollapsed"
    >
      <slot />
    </aside>

    <div class="side-shell__rail">
      <header class="side-shell__head">
        <button
          type="button"
          class="side-shell__fold"
          :aria-label="contentCollapsed ? '展开侧栏' : '收起侧栏'"
          @click="toggleCollapse"
        >
          <span aria-hidden="true">{{ contentCollapsed ? "›" : "‹" }}</span>
        </button>
      </header>

      <nav role="tablist" class="side-shell__tabs" aria-label="侧栏标签">
        <button
          v-for="tab in TABS"
          :key="tab.id"
          role="tab"
          type="button"
          class="side-shell__tab"
          :class="{ 'side-shell__tab--active': activeTab === tab.id }"
          :aria-selected="activeTab === tab.id"
          :tabindex="activeTab === tab.id ? 0 : -1"
          @click="onTabChange(tab.id)"
        >
          <span class="side-shell__tab-body">
            <span class="side-shell__tab-label">{{ tab.label }}</span>
          </span>
        </button>
      </nav>

      <div class="side-shell__well" aria-hidden="true" />
    </div>
  </div>
</template>

<style scoped>
.side-shell {
  display: flex;
  align-self: stretch;
  flex-shrink: 0;
  min-height: 0;
  border: 1px solid var(--ui-border);
  border-radius: var(--shell-sidebar-radius);
  background: var(--ui-bg-panel);
  overflow: hidden;
}

.side-shell--collapsed {
  width: var(--shell-tab-rail-width);
}

.side-shell__pane {
  width: var(--shell-left-content-width);
  flex-shrink: 0;
  min-height: 0;
  overflow: hidden;
  padding: 12px;
  background: var(--ui-bg-panel);
}

.side-shell__rail {
  width: var(--shell-tab-rail-width);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--ui-bg-inset);
  border-left: 1px solid var(--ui-border);
}

.side-shell--collapsed .side-shell__rail {
  border-left: none;
}

.side-shell__head {
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  padding: 6px 0;
  border-bottom: 1px solid var(--ui-border);
  background: var(--ui-bg-inset);
}

.side-shell__fold {
  width: 22px;
  height: 22px;
  padding: 0;
  border: 1px solid transparent;
  border-radius: 4px;
  background: transparent;
  color: var(--ui-text-muted);
  font-size: 13px;
  font-weight: 600;
  line-height: 1;
  cursor: pointer;
  transition:
    background 0.15s ease,
    color 0.15s ease,
    border-color 0.15s ease;
}

.side-shell__fold:hover {
  background: var(--ui-bg-control);
  color: var(--ui-text);
  border-color: var(--ui-border-muted);
}

.side-shell__tabs {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.side-shell__tab {
  position: relative;
  display: block;
  width: 100%;
  margin: 0;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  font-family: inherit;
}

.side-shell__tab-body {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 58px;
  padding: 10px 0;
  background: var(--ui-bg-inset);
  border-bottom: 1px solid var(--ui-border);
}

.side-shell__tab-label {
  writing-mode: vertical-rl;
  text-orientation: upright;
  font-size: 11px;
  letter-spacing: 0.18em;
  color: var(--ui-text-muted);
  transition: color 0.15s ease;
}

.side-shell__tab:hover .side-shell__tab-label {
  color: var(--ui-text);
}

.side-shell__tab:hover .side-shell__tab-body {
  background: var(--ui-bg-control);
}

.side-shell__tab--active {
  z-index: 2;
}

.side-shell__tab--active .side-shell__tab-body {
  margin-left: -1px;
  width: calc(100% + 1px);
  background: var(--ui-bg-panel);
  border-bottom-color: var(--ui-border);
  box-shadow: inset 2px 0 0 var(--ui-border-accent);
}

.side-shell__tab--active .side-shell__tab-label {
  color: var(--ui-text);
  font-weight: 600;
}

.side-shell__well {
  flex: 1;
  min-height: 0;
  background: var(--ui-bg-inset);
  border-right: 1px solid var(--ui-border);
}

.side-shell--collapsed .side-shell__well {
  border-right: none;
}
</style>
