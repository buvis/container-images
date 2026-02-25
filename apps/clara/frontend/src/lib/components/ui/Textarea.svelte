<script lang="ts">
  import type { HTMLTextareaAttributes } from 'svelte/elements';

  interface Props extends HTMLTextareaAttributes {
    label?: string;
    error?: string;
    value?: string | null;
    rows?: number;
  }

  let {
    label,
    error,
    id,
    value = $bindable(),
    rows = 3,
    class: className = '',
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

  <textarea
    id={inputId}
    bind:value
    {rows}
    class="w-full rounded-lg border bg-neutral-800 px-3 py-2 text-sm text-white placeholder-neutral-500 outline-none transition
      {error
        ? 'border-red-500 focus:border-red-500 focus:ring-1 focus:ring-red-500'
        : 'border-neutral-700 focus:border-brand-500 focus:ring-1 focus:ring-brand-500'}
      {className}"
    {...rest}
  ></textarea>

  {#if error}
    <p class="text-xs text-red-400">{error}</p>
  {/if}
</div>
