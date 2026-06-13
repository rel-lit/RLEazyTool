<script setup lang="ts">
import { ref, toRef } from "vue";
import { useUiControlInteraction } from "./interaction/useUiControlInteraction";

const props = withDefaults(
  defineProps<{
    disabled?: boolean;
    type?: "button" | "submit";
    ariaLabel?: string;
  }>(),
  {
    disabled: false,
    type: "button",
    ariaLabel: "",
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
</script>

<template>
  <button
    ref="rootRef"
    v-bind="uiStateAttrs"
    type="button"
    class="ui-icon-btn"
    :disabled="disabled"
    :aria-label="ariaLabel || undefined"
  >
    <slot />
  </button>
</template>
