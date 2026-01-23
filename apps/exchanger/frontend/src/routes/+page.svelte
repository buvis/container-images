<script lang="ts">
  import { onMount } from 'svelte';
  import { getHealth, getFavorites, getRatesHistory, type Rate } from '$lib/api';
  import TaskPipeline from './TaskPipeline.svelte';
  import Sparkline from './Sparkline.svelte';

  let healthStatus = 'unknown';
  let favorites: string[] = [];
  let favoritesData: Record<string, { date: string; rate: number | null }[]> = {};
  let loading = true;

  function formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  async function loadData() {
    try {
      const health = await getHealth();
      healthStatus = health.status;

      favorites = await getFavorites();
      
      const today = new Date();
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(today.getDate() - 7);
      
      const from = formatDate(sevenDaysAgo);
      const to = formatDate(today);

      const historyPromises = favorites.map(async (symbol) => {
        const history = await getRatesHistory(symbol, from, to);
        return { symbol, history };
      });

      const results = await Promise.all(historyPromises);
      favoritesData = results.reduce((acc, { symbol, history }) => {
        acc[symbol] = history;
        return acc;
      }, {} as Record<string, { date: string; rate: number | null }[]>);

    } catch (e) {
      console.error('Failed to load dashboard data', e);
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    loadData();
  });
</script>

<div class="min-h-screen bg-slate-950 text-slate-100 p-8">
  <header class="flex items-center justify-between mb-8">
    <h1 class="text-3xl font-bold text-white">Exchanger Dashboard</h1>
    <div class="flex items-center gap-2 bg-slate-900 px-4 py-2 rounded-full border border-slate-800">
      <div class={`w-3 h-3 rounded-full ${healthStatus === 'ok' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]'}`}></div>
      <span class="text-sm font-medium uppercase tracking-wider">{healthStatus}</span>
    </div>
  </header>

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
    <!-- Main Content - Favorites & Sparklines -->
    <div class="lg:col-span-2 space-y-6">
      <h2 class="text-xl font-semibold text-slate-300">Market Overview</h2>
      
      {#if loading}
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          {#each Array(4) as _}
            <div class="bg-slate-900 p-6 rounded-xl border border-slate-800 animate-pulse h-32"></div>
          {/each}
        </div>
      {:else}
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          {#each favorites as symbol}
            <div class="bg-slate-900 p-6 rounded-xl border border-slate-800 hover:border-slate-700 transition-colors">
              <div class="flex justify-between items-start mb-4">
                <div>
                  <h3 class="text-lg font-bold text-white">{symbol}</h3>
                  <p class="text-sm text-slate-400">7 Day Trend</p>
                </div>
                {#if favoritesData[symbol] && favoritesData[symbol].length > 0}
                   {@const current = favoritesData[symbol][favoritesData[symbol].length - 1].rate}
                   {@const previous = favoritesData[symbol][0].rate}
                   {@const change = current && previous ? ((current - previous) / previous) * 100 : 0}
                   <div class={`text-sm font-bold ${change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                     {change > 0 ? '+' : ''}{change.toFixed(2)}%
                   </div>
                {/if}
              </div>
              
              {#if favoritesData[symbol]}
                <Sparkline data={favoritesData[symbol]} color={
                  favoritesData[symbol].length > 1 && 
                  (favoritesData[symbol][favoritesData[symbol].length-1].rate || 0) >= (favoritesData[symbol][0].rate || 0) 
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

    <!-- Sidebar - Task Pipeline -->
    <div class="space-y-6">
      <TaskPipeline />
    </div>
  </div>
</div>
