<script setup lang="ts">
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
  <button
    type="button"
    class="ui-icon-btn"
    :disabled="disabled"
    :aria-label="ariaLabel || undefined"
  >
    <slot />
  </button>
</template>
