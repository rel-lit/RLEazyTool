<script setup lang="ts">
import { computed } from "vue";
import UiControl from "./primitives/UiControl.vue";
import type { ListLayoutMark } from "../domains/list-layout-mark";

defineOptions({ inheritAttrs: false });

const props = withDefaults(
  defineProps<{
    selected?: boolean;
    forbidden?: boolean;
    size?: "sm" | "md";
    disabled?: boolean;
    type?: "button" | "submit";
    layoutMark?: ListLayoutMark;
  }>(),
  {
    selected: false,
    forbidden: false,
    size: "md",
    disabled: false,
    type: "button",
    layoutMark: () => ({ kind: "none", ring: "intermediate" }),
  }
);

const classes = computed(() => [
  "ui-chip",
  props.size === "sm" ? "ui-chip--sm" : "ui-chip--md",
  {
    "ui-chip--on": props.selected && !props.forbidden,
    "ui-chip--forbidden": props.forbidden,
    "ui-chip--has-layout-mark": props.layoutMark?.kind === "hollow-sphere",
  },
]);

const showLayoutMark = computed(() => props.layoutMark?.kind === "hollow-sphere");

const layoutMarkClasses = computed(() => {
  const ring = props.layoutMark?.ring ?? "intermediate";
  return ["ui-chip__layout-mark", `ui-chip__layout-mark--${ring}`];
});

const layoutMarkStyle = computed(() => {
  const m = props.layoutMark;
  if (!m || m.kind !== "hollow-sphere") return undefined;
  return {
    "--ui-chip-mark-fill": m.fill ?? "transparent",
  } as Record<string, string>;
});
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
      :class="layoutMarkClasses"
      role="presentation"
      aria-hidden="true"
      :style="layoutMarkStyle"
    />
  </UiControl>
</template>
