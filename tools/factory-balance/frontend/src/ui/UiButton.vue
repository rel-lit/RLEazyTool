<script setup lang="ts">
import { computed, ref, toRef } from "vue";
import { useUiControlInteraction } from "./interaction/useUiControlInteraction";

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

const emit = defineEmits<{
  longPress: [event: PointerEvent];
  secondaryClick: [event: MouseEvent];
  auxClick: [event: MouseEvent];
  wheel: [event: WheelEvent];
  hoverChange: [hovering: boolean];
  focusChange: [focused: boolean];
  pressChange: [pressed: boolean];
}>();

const rootRef = ref<HTMLButtonElement | null>(null);
const { uiStateAttrs } = useUiControlInteraction(rootRef, emit, toRef(props, "disabled"));

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
  <button
    ref="rootRef"
    v-bind="uiStateAttrs"
    :type="type"
    :class="classes"
    :disabled="disabled"
  >
    <slot />
  </button>
</template>
