<script lang="ts">
  import { Search, X } from 'lucide-svelte';

  interface Props {
    value: string;
    placeholder?: string;
    onchange: (value: string) => void;
  }

  let { value, placeholder = 'Search...', onchange }: Props = $props();

  let timeout: ReturnType<typeof setTimeout>;

  function handleInput(e: Event) {
    const input = e.target as HTMLInputElement;
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      onchange(input.value);
    }, 300);
  }

  function handleClear() {
    onchange('');
  }
</script>

<div class="relative">
  <Search size={16} class="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500" />
  <input
    type="text"
    {value}
    oninput={handleInput}
    {placeholder}
    class="w-full rounded-lg border border-neutral-700 bg-neutral-800 py-2 pl-9 pr-9 text-sm text-white placeholder-neutral-500 outline-none transition focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
  />
  {#if value}
    <button
      onclick={handleClear}
      class="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-300"
      aria-label="Clear search"
    >
      <X size={14} />
    </button>
  {/if}
</div>
