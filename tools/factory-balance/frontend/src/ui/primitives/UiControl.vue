<script setup lang="ts">
import { ref, toRef, useAttrs } from "vue";
import type { UiControlEmit } from "../interaction/events";
import { useUiControl } from "../interaction/useUiControl";

defineOptions({ inheritAttrs: false });

const props = withDefaults(
  defineProps<{
    disabled?: boolean;
    type?: "button" | "submit" | "reset";
    /** 为 true 时 secondary 会 preventDefault，不弹出系统菜单 */
    suppressContextMenu?: boolean;
  }>(),
  {
    disabled: false,
    type: "button",
    suppressContextMenu: false,
  }
);

const emit = defineEmits<{
  primary: [event: MouseEvent];
  secondary: [event: MouseEvent];
  longPress: [event: PointerEvent];
  auxClick: [event: MouseEvent];
  wheel: [event: WheelEvent];
  hoverChange: [hovering: boolean];
  focusChange: [focused: boolean];
  pressChange: [pressed: boolean];
}>();

const attrs = useAttrs();
const rootRef = ref<HTMLButtonElement | null>(null);

const { uiStateAttrs } = useUiControl(rootRef, emit as UiControlEmit, {
  disabled: toRef(props, "disabled"),
  suppressContextMenu: toRef(props, "suppressContextMenu"),
});
</script>

<template>
  <button
    ref="rootRef"
    v-bind="{ ...uiStateAttrs, ...attrs }"
    :type="type"
    :disabled="disabled"
  >
    <slot />
  </button>
</template>
