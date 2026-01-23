<script lang="ts">
  import { onMount } from 'svelte';
  import { getProvidersStatus, type ProviderStatus } from '$lib/api';

  let providers: ProviderStatus[] = [];
  let loading = true;
  let error: string | null = null;

  onMount(async () => {
    try {
      providers = await getProvidersStatus();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load providers';
    } finally {
      loading = false;
    }
  });
</script>

<div class="min-h-screen bg-[#0F172A] text-slate-200 p-8">
  <h1 class="text-3xl font-bold mb-8">Providers</h1>

  {#if loading}
    <div class="flex justify-center">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
    </div>
  {:else if error}
    <div class="bg-red-900/50 border border-red-500 text-red-200 p-4 rounded-lg">
      Error: {error}
    </div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {#each providers as provider}
        <div class="bg-[#1E293B] rounded-xl p-6 shadow-lg border border-slate-700/50">
          <div class="flex justify-between items-start mb-4">
            <h2 class="text-xl font-semibold text-white">{provider.name}</h2>
            {#if provider.symbol_count > 0}
              <div class="text-green-400" title="Healthy">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                </svg>
              </div>
            {:else}
              <div class="group relative">
                <div class="text-red-400 cursor-help">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                  </svg>
                </div>
                <div class="absolute right-0 top-full mt-2 w-48 px-3 py-2 bg-black/90 text-white text-xs rounded shadow-xl opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none">
                  No symbols configured - run populate_symbols first
                </div>
              </div>
            {/if}
          </div>
          
          <div class="space-y-2">
            <div class="flex justify-between items-center text-sm">
              <span class="text-slate-400">Symbols Configured</span>
              <span class="text-white font-mono bg-slate-800 px-2 py-0.5 rounded">{provider.symbol_count}</span>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
