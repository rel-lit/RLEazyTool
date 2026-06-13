<script setup lang="ts">
import UiControl from "./primitives/UiControl.vue";

defineOptions({ inheritAttrs: false });

withDefaults(
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
</script>

<template>
  <UiControl
    v-bind="$attrs"
    class="ui-icon-btn"
    :disabled="disabled"
    :type="type"
    :aria-label="ariaLabel || undefined"
  >
    <slot />
  </UiControl>
</template>
