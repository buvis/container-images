<script lang="ts">
  import { onMount } from 'svelte';
  import { getFavorites, getRatesHistory, getConfig, type Favorite } from '$lib/api';
  import Sparkline from '../Sparkline.svelte';

  let favorites: Favorite[] = [];
  let favoritesData: Record<string, { date: string; rate: number | null }[]> = {};
  let loading = true;

  const ranges = [
    { label: '7D', days: 7 },
    { label: '30D', days: 30 },
    { label: '90D', days: 90 },
    { label: '180D', days: 180 },
    { label: '1Y', days: 365 },
  ];

  let activeRange = 7;

  function formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  async function loadFavoritesHistory(days: number) {
    const today = new Date();
    const from = new Date();
    from.setDate(today.getDate() - days);

    const historyPromises = favorites.map(async (fav) => {
      const history = await getRatesHistory(fav.provider_symbol, formatDate(from), formatDate(today), fav.provider, fav.provider_symbol);
      return { key: `${fav.provider}:${fav.provider_symbol}`, history };
    });

    const results = await Promise.all(historyPromises);
    favoritesData = results.reduce((acc, { key, history }) => {
      acc[key] = history;
      return acc;
    }, {} as Record<string, { date: string; rate: number | null }[]>);
  }

  async function setRange(days: number) {
    activeRange = days;
    loading = true;
    await loadFavoritesHistory(days);
    loading = false;
  }

  async function loadData() {
    try {
      const config = await getConfig();
      activeRange = config.dashboard_history_days;
      favorites = await getFavorites();
      await loadFavoritesHistory(activeRange);
    } catch (e) {
      console.error('Failed to load market data', e);
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
    <h1 class="text-3xl font-bold text-white">Market</h1>
    <div class="flex bg-slate-900 rounded-lg p-1">
      {#each ranges as range}
        <button
          class="px-3 py-1 text-xs font-medium rounded transition-colors {activeRange === range.days ? 'bg-slate-700 text-white shadow' : 'text-slate-400 hover:text-slate-200'}"
          on:click={() => setRange(range.days)}
        >
          {range.label}
        </button>
      {/each}
    </div>
  </header>

  {#if loading}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {#each Array(6) as _}
        <div class="bg-slate-900 p-6 rounded-xl border border-slate-800 animate-pulse h-32"></div>
      {/each}
    </div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {#each favorites as fav}
        {@const key = `${fav.provider}:${fav.provider_symbol}`}
        {@const data = favoritesData[key]}
        <div class="bg-slate-900 p-6 rounded-xl border border-slate-800 hover:border-slate-700 transition-colors">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h3 class="text-lg font-bold text-white">{fav.provider_symbol}</h3>
              <p class="text-sm text-slate-400">{ranges.find(r => r.days === activeRange)?.label || activeRange + 'D'} Trend</p>
            </div>
            {#if data && data.length > 0}
               {@const current = data[data.length - 1].rate}
               {@const previous = data[0].rate}
               {@const change = current && previous ? ((current - previous) / previous) * 100 : 0}
               <div class={`text-sm font-bold ${change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                 {change > 0 ? '+' : ''}{change.toFixed(2)}%
               </div>
            {/if}
          </div>

          {#if data}
            <Sparkline data={data} color={
              data.length > 1 &&
              (data[data.length-1].rate || 0) >= (data[0].rate || 0)
              ? '#4ade80' : '#f87171'
            } />
          {:else}
            <div class="h-16 flex items-center justify-center text-slate-600 text-sm">No Data</div>
          {/if}
        </div>
      {/each}

      {#if favorites.length === 0}
        <div class="col-span-full p-8 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
          No favorites added yet.
        </div>
      {/if}
    </div>
  {/if}
</div>
