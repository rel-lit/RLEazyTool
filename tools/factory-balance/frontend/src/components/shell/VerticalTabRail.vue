<script setup lang="ts">
import { UiIconButton } from "../../ui";

export type SidebarTab = "save" | "history";

defineProps<{
  activeTab: SidebarTab;
  contentCollapsed: boolean;
}>();

const emit = defineEmits<{
  "update:activeTab": [tab: SidebarTab];
  toggleCollapse: [];
}>();

function pick(tab: SidebarTab): void {
  emit("update:activeTab", tab);
}
</script>

<template>
  <nav class="tab-rail" aria-label="侧栏切换">
    <UiIconButton
      class="tab-rail__collapse"
      :aria-label="contentCollapsed ? '展开侧栏' : '收起侧栏'"
      @primary="emit('toggleCollapse')"
    >
      {{ contentCollapsed ? "›" : "‹" }}
    </UiIconButton>

    <button
      type="button"
      class="tab-rail__tab"
      :class="{ 'tab-rail__tab--on': activeTab === 'save' }"
      :aria-current="activeTab === 'save' ? 'page' : undefined"
      @click="pick('save')"
    >
      存档
    </button>
    <button
      type="button"
      class="tab-rail__tab"
      :class="{ 'tab-rail__tab--on': activeTab === 'history' }"
      @click="pick('history')"
    >
      历史
    </button>
  </nav>
</template>

<style scoped>
.tab-rail {
  flex-shrink: 0;
  width: var(--shell-tab-rail-width);
  display: flex;
  flex-direction: column;
  align-items: stretch;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 0 8px 8px 0;
  clip-path: polygon(0 0, 100% 0, 100% calc(100% - 20px), 0 100%);
  padding: 6px 0 24px;
  gap: 4px;
}

.tab-rail__collapse {
  align-self: center;
  margin-bottom: 4px;
}

.tab-rail__collapse :deep(.ui-icon-btn) {
  width: 24px;
  height: 24px;
  font-size: 14px;
  font-weight: 600;
}

.tab-rail__tab {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  transform: rotate(180deg);
  margin: 0 auto;
  padding: 10px 0;
  width: 28px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #8b949e;
  font-size: 12px;
  font-family: inherit;
  letter-spacing: 0.12em;
  cursor: pointer;
  transition:
    background 0.15s ease,
    color 0.15s ease;
}

.tab-rail__tab:hover {
  background: #21262d;
  color: #e6edf3;
}

.tab-rail__tab--on {
  background: #1f3d5c;
  color: #58a6ff;
}
</style>
