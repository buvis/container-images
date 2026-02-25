<script lang="ts">
  import type { HTMLInputAttributes } from 'svelte/elements';

  interface Props extends HTMLInputAttributes {
    label?: string;
    error?: string;
    value?: string | number | null;
  }

  let {
    label,
    error,
    id,
    value = $bindable(),
    class: className = '',
    ...rest
  }: Props = $props();

  const inputId = id ?? (label ? `${label.toLowerCase().replace(/\s+/g, '-')}-${crypto.randomUUID().slice(0, 8)}` : undefined);
</script>

<div class="space-y-1.5">
  {#if label}
    <label for={inputId} class="block text-sm font-medium text-neutral-300">
      {label}
    </label>
  {/if}

  <input
    id={inputId}
    bind:value
    class="w-full rounded-lg border bg-neutral-800 px-3 py-2 text-sm text-white placeholder-neutral-500 outline-none transition
      {error
        ? 'border-red-500 focus:border-red-500 focus:ring-1 focus:ring-red-500'
        : 'border-neutral-700 focus:border-brand-500 focus:ring-1 focus:ring-brand-500'}
      {className}"
    {...rest}
  />

  {#if error}
    <p class="text-xs text-red-400">{error}</p>
  {/if}
</div>
