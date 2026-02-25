<script lang="ts">
  import { ChevronLeft, ChevronRight } from 'lucide-svelte';

  interface Props {
    total: number;
    offset: number;
    limit: number;
    onchange: (offset: number) => void;
  }

  let { total, offset, limit, onchange }: Props = $props();

  let currentPage = $derived(Math.floor(offset / limit) + 1);
  let totalPages = $derived(Math.max(1, Math.ceil(total / limit)));
  let hasPrev = $derived(offset > 0);
  let hasNext = $derived(offset + limit < total);

  function goTo(page: number) {
    onchange((page - 1) * limit);
  }

  function prev() {
    if (hasPrev) goTo(currentPage - 1);
  }

  function next() {
    if (hasNext) goTo(currentPage + 1);
  }

  let pageNumbers = $derived.by(() => {
    const pages: (number | '...')[] = [];
    const range = 2;
    for (let i = 1; i <= totalPages; i++) {
      if (
        i === 1 ||
        i === totalPages ||
        (i >= currentPage - range && i <= currentPage + range)
      ) {
        pages.push(i);
      } else if (pages[pages.length - 1] !== '...') {
        pages.push('...');
      }
    }
    return pages;
  });
</script>

{#if totalPages > 1}
  <div class="flex items-center justify-between pt-4">
    <p class="text-xs text-neutral-500">
      {offset + 1}-{Math.min(offset + limit, total)} of {total}
    </p>

    <div class="flex items-center gap-1">
      <button
        onclick={prev}
        disabled={!hasPrev}
        class="rounded-lg p-1.5 text-neutral-400 transition hover:bg-neutral-800 hover:text-white disabled:opacity-30 disabled:pointer-events-none"
        aria-label="Previous page"
      >
        <ChevronLeft size={16} />
      </button>

      {#each pageNumbers as p}
        {#if p === '...'}
          <span class="px-2 text-xs text-neutral-600">...</span>
        {:else}
          <button
            onclick={() => goTo(p as number)}
            class="min-w-[2rem] rounded-lg px-2 py-1 text-xs transition
              {p === currentPage
                ? 'bg-brand-500/10 text-brand-400 font-medium'
                : 'text-neutral-400 hover:bg-neutral-800 hover:text-white'}"
          >
            {p}
          </button>
        {/if}
      {/each}

      <button
        onclick={next}
        disabled={!hasNext}
        class="rounded-lg p-1.5 text-neutral-400 transition hover:bg-neutral-800 hover:text-white disabled:opacity-30 disabled:pointer-events-none"
        aria-label="Next page"
      >
        <ChevronRight size={16} />
      </button>
    </div>
  </div>
{/if}
