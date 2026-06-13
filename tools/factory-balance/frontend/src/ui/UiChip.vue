<script setup lang="ts">
import { computed } from "vue";
import UiControl from "./primitives/UiControl.vue";

defineOptions({ inheritAttrs: false });

const props = withDefaults(
  defineProps<{
    selected?: boolean;
    forbidden?: boolean;
    size?: "sm" | "md";
    disabled?: boolean;
    type?: "button" | "submit";
  }>(),
  {
    selected: false,
    forbidden: false,
    size: "md",
    disabled: false,
    type: "button",
  }
);

const classes = computed(() => [
  "ui-chip",
  props.size === "sm" ? "ui-chip--sm" : "ui-chip--md",
  {
    "ui-chip--on": props.selected && !props.forbidden,
    "ui-chip--forbidden": props.forbidden,
  },
]);
</script>

<template>
  <UiControl
    v-bind="$attrs"
    :class="classes"
    :disabled="disabled"
    :type="type"
    suppress-context-menu
  >
    <slot />
  </UiControl>
</template>
