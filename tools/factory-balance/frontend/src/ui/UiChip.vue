<script setup lang="ts">
import { computed } from "vue";
import UiControl from "./primitives/UiControl.vue";
import type { ListLayoutMarkKind } from "../domains/list-layout-mark";

defineOptions({ inheritAttrs: false });

const props = withDefaults(
  defineProps<{
    selected?: boolean;
    forbidden?: boolean;
    size?: "sm" | "md";
    disabled?: boolean;
    type?: "button" | "submit";
    /** 列表项—布局关联标记；none 不显示右侧镂空圈 */
    layoutMark?: ListLayoutMarkKind;
  }>(),
  {
    selected: false,
    forbidden: false,
    size: "md",
    disabled: false,
    type: "button",
    layoutMark: "none",
  }
);

const classes = computed(() => [
  "ui-chip",
  props.size === "sm" ? "ui-chip--sm" : "ui-chip--md",
  {
    "ui-chip--on": props.selected && !props.forbidden,
    "ui-chip--forbidden": props.forbidden,
    "ui-chip--has-layout-mark": props.layoutMark !== "none",
  },
]);

const showLayoutMark = computed(() => props.layoutMark === "hollow-sphere");
</script>

<template>
  <UiControl
    v-bind="$attrs"
    :class="classes"
    :disabled="disabled"
    :type="type"
    suppress-context-menu
  >
    <span class="ui-chip__label"><slot /></span>
    <span
      v-if="showLayoutMark"
      class="ui-chip__layout-mark"
      role="presentation"
      aria-hidden="true"
    />
  </UiControl>
</template>
