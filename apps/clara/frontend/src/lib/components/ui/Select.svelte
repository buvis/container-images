<script lang="ts">
  import type { HTMLSelectAttributes } from 'svelte/elements';
  import type { Snippet } from 'svelte';

  interface Props extends HTMLSelectAttributes {
    label?: string;
    error?: string;
    value?: any;
    children?: Snippet;
  }

  let {
    label,
    error,
    id,
    value = $bindable(),
    class: className = '',
    children,
    ...rest
  }: Props = $props();

  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-');
</script>

<div class="space-y-1.5">
  {#if label}
    <label for={inputId} class="block text-sm font-medium text-neutral-300">
      {label}
    </label>
  {/if}

  <select
    id={inputId}
    bind:value
    class="w-full rounded-lg border bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition
      {error
        ? 'border-red-500 focus:border-red-500 focus:ring-1 focus:ring-red-500'
        : 'border-neutral-700 focus:border-brand-500 focus:ring-1 focus:ring-brand-500'}
      {className}"
    {...rest}
  >
    {@render children?.()}
  </select>

  {#if error}
    <p class="text-xs text-red-400">{error}</p>
  {/if}
</div>
