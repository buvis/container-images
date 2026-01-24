<script lang="ts">
  import { onMount } from 'svelte';
  import { getHealth, getFavorites, getCoverage, getMissingSymbols, getProvidersStatus, type ProviderStatus, type Favorite } from '$lib/api';
  import TaskPipeline from './TaskPipeline.svelte';
  import CalendarHeatmap from '$lib/components/CalendarHeatmap.svelte';

  let healthStatus = 'loading';
  let favorites: Favorite[] = [];
  let coverage: Record<string, number> = {};
  let missingSymbols: Record<string, string[]> = {};
  let providers: ProviderStatus[] = [];
  let loading = true;

  async function loadData() {
    try {
      const [health, provs] = await Promise.all([getHealth(), getProvidersStatus()]);
      healthStatus = health.status;
      providers = provs;

      favorites = await getFavorites();
      const favoriteSymbols = favorites.map(f => f.provider_symbol);

      const currentYear = new Date().getFullYear();
      const [c1, c2, m1, m2] = await Promise.all([
          getCoverage(currentYear, undefined, favoriteSymbols.length ? favoriteSymbols : undefined),
          getCoverage(currentYear - 1, undefined, favoriteSymbols.length ? favoriteSymbols : undefined),
          favoriteSymbols.length ? getMissingSymbols(currentYear, favoriteSymbols) : Promise.resolve({}),
          favoriteSymbols.length ? getMissingSymbols(currentYear - 1, favoriteSymbols) : Promise.resolve({})
      ]);
      coverage = { ...c2, ...c1 };
      missingSymbols = { ...m2, ...m1 };

    } catch (e) {
      console.error('Failed to load dashboard data', e);
      healthStatus = 'offline';
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    loadData();
  });
</script>

<div class="bg-slate-950 text-slate-100 p-8">
  <header class="flex items-center justify-between mb-8">
    <h1 class="text-3xl font-bold text-white">Status</h1>
    <div class="flex items-center gap-2 bg-slate-900 px-4 py-2 rounded-full border border-slate-800">
      <div class={`w-3 h-3 rounded-full ${
        healthStatus === 'ok' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' :
        healthStatus === 'loading' ? 'bg-slate-500 animate-pulse' :
        'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]'
      }`}></div>
      <span class="text-sm font-medium uppercase tracking-wider">{healthStatus}</span>
    </div>
  </header>

  <div class="mb-8">
    <CalendarHeatmap {coverage} {missingSymbols} favoritesCount={favorites.length} />
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
    <TaskPipeline />

    <!-- Providers Status -->
    <div class="bg-slate-900 rounded-xl border border-slate-800 p-4">
      <h3 class="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Providers</h3>
      <div class="space-y-2">
        {#each providers as provider}
          <div class="flex flex-col sm:flex-row sm:items-center justify-between py-3 px-4 bg-slate-800/50 rounded-lg gap-3 transition-colors hover:bg-slate-800/70">
            <div class="flex flex-col gap-2">
              <span class="text-sm font-medium text-white">{provider.name}</span>
              {#if Object.keys(provider.symbol_counts_by_type).length > 0}
                <div class="flex flex-wrap gap-2">
                  {#each Object.entries(provider.symbol_counts_by_type) as [type, count]}
                    <div class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-slate-700/30 border border-slate-700/50">
                      <span class="text-slate-200 mr-1.5 font-semibold">{count}</span>
                      <span class="text-slate-400 uppercase tracking-wider">{type}</span>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
            
            <div class="flex items-center gap-3 shrink-0 self-end sm:self-auto">
              <span class="text-xs text-slate-500">
                <span class="text-slate-300 font-semibold">{provider.symbol_count}</span> total
              </span>
              {#if provider.symbol_count > 0}
                <div class="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]"></div>
              {:else}
                <div class="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.4)]" title="No symbols configured"></div>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  </div>
</div>
