<script setup lang="ts">
import { computed } from "vue";

export type UiButtonVariant =
  | "primary"
  | "secondary"
  | "danger"
  | "danger-soft"
  | "toggle"
  | "tab"
  | "link"
  | "link-muted";

const props = withDefaults(
  defineProps<{
    variant?: UiButtonVariant;
    pressed?: boolean;
    disabled?: boolean;
    block?: boolean;
    size?: "sm" | "md";
    type?: "button" | "submit" | "reset";
  }>(),
  {
    variant: "secondary",
    pressed: false,
    disabled: false,
    block: false,
    size: "md",
    type: "button",
  }
);

const classes = computed(() => [
  "ui-btn",
  `ui-btn--${props.variant}`,
  props.size === "sm" ? "ui-btn--sm" : "ui-btn--md",
  {
    "ui-btn--on": props.pressed,
    "ui-btn--block": props.block,
  },
]);
</script>

<template>
  <button :type="type" :class="classes" :disabled="disabled">
    <slot />
  </button>
</template>
