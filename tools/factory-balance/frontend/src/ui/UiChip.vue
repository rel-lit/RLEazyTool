<script setup lang="ts">
import { computed, ref, toRef } from "vue";
import { useUiControlInteraction } from "./interaction/useUiControlInteraction";

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
  "ui-chip",
  props.size === "sm" ? "ui-chip--sm" : "ui-chip--md",
  {
    "ui-chip--on": props.selected && !props.forbidden,
    "ui-chip--forbidden": props.forbidden,
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
