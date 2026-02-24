<script lang="ts">
  import { onMount } from 'svelte';
  import { getProvidersStatus, type ProviderStatus } from '$lib/api';

  let providers: ProviderStatus[] = [];
  let loading = true;

  onMount(async () => {
    try {
      providers = await getProvidersStatus();
    } catch (e) {
      console.error('Failed to load providers', e);
    } finally {
      loading = false;
    }
  });
</script>

<div class="bg-slate-950 text-slate-100 p-8">
  <header class="mb-8">
    <h1 class="text-3xl font-bold text-white">Providers</h1>
  </header>

  {#if loading}
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      {#each Array(2) as _}
        <div class="bg-slate-900 p-6 rounded-xl border border-slate-800 animate-pulse h-40"></div>
      {/each}
    </div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      {#each providers as provider}
        <div class="bg-slate-900 rounded-xl border border-slate-800 p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-xl font-bold text-white uppercase tracking-wide">{provider.name}</h2>
            <div class="flex items-center gap-2">
              {#if provider.healthy}
                <div class="w-2.5 h-2.5 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]"></div>
                <span class="text-xs text-green-400 font-medium">Active</span>
              {:else}
                <div class="w-2.5 h-2.5 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]"></div>
                <span class="text-xs text-red-400 font-medium">No symbols</span>
              {/if}
            </div>
          </div>

          <div class="flex items-baseline gap-2 mb-4">
            <span class="text-3xl font-bold text-white">{provider.symbol_count}</span>
            <span class="text-sm text-slate-400">symbols</span>
          </div>

          {#if Object.keys(provider.symbol_counts_by_type).length > 0}
            <div class="flex flex-wrap gap-2 mb-5">
              {#each Object.entries(provider.symbol_counts_by_type) as [type, count]}
                <div class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/50">
                  <span class="text-sm font-semibold text-white">{count}</span>
                  <span class="text-xs text-slate-400 uppercase tracking-wider">{type}</span>
                </div>
              {/each}
            </div>
          {/if}

          <a
            href="/symbols?provider={provider.name}"
            class="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-white transition-colors"
          >
            Browse symbols
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 0l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
            </svg>
          </a>
        </div>
      {/each}
    </div>

    {#if providers.length === 0}
      <div class="p-8 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
        No providers registered.
      </div>
    {/if}
  {/if}
</div>
