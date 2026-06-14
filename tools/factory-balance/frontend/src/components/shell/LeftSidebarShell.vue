<script setup lang="ts">
import { ref, watch } from "vue";
import VerticalTabRail, { type SidebarTab } from "./VerticalTabRail.vue";

export type { SidebarTab };

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
</script>

<template>
  <div class="left-shell">
    <aside
      v-show="!contentCollapsed"
      class="left-shell__content panel"
      :aria-hidden="contentCollapsed"
    >
      <slot />
    </aside>

    <VerticalTabRail
      :active-tab="activeTab"
      :content-collapsed="contentCollapsed"
      @update:active-tab="onTabChange"
      @toggle-collapse="contentCollapsed = !contentCollapsed"
    />
  </div>
</template>

<style scoped>
.left-shell {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  flex-shrink: 0;
  min-height: 0;
}

.left-shell__content {
  width: var(--shell-left-content-width);
  min-height: 0;
  overflow: hidden;
  border-radius: 8px 0 0 8px;
  border-right: none;
}

.panel {
  background: #161b22;
  border: 1px solid #30363d;
  padding: 12px;
}
</style>
