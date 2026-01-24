<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import type { Rate, Favorite } from '$lib/api';
    import SearchInput from './ui/SearchInput.svelte';
    import SegmentedControl from './ui/SegmentedControl.svelte';

    export let rates: Rate[] = [];
    export let favorites: Favorite[] = [];
    export let selectedSymbol: string | null = null;
    export let activeType: 'forex' | 'crypto' = 'forex';

    const dispatch = createEventDispatcher();
    let search = '';
    let prevType = activeType;

    $: if (activeType !== prevType) {
        dispatch('typeChange', activeType);
        prevType = activeType;
    }

    function toggleFav(e: MouseEvent, rate: Rate) {
        e.stopPropagation();
        dispatch('toggleFavorite', { provider: rate.provider, provider_symbol: rate.provider_symbol });
    }

    $: favoriteKeys = new Set(favorites.map(f => `${f.provider}:${f.provider_symbol}`));

    function isFavorite(rate: Rate): boolean {
        return favoriteKeys.has(`${rate.provider}:${rate.provider_symbol}`);
    }

    $: filteredRates = rates.filter(r =>
        r.symbol.toLowerCase().includes(search.toLowerCase())
    );
</script>

<div class="bg-slate-800 rounded-lg shadow-lg flex flex-col h-full overflow-hidden border border-slate-700">
    <div class="p-4 border-b border-slate-700 space-y-3">
        <SegmentedControl options={['forex', 'crypto']} bind:value={activeType} />
        <SearchInput bind:value={search} placeholder="Search symbol..." />
    </div>

    <div class="flex-1 overflow-y-auto p-2 space-y-1">
        {#each filteredRates as rate (rate.provider_symbol)}
            <div
                role="button"
                tabindex="0"
                class="w-full flex items-center justify-between p-2 rounded hover:bg-slate-700 transition-colors group cursor-pointer {selectedSymbol === rate.symbol ? 'bg-slate-700 ring-1 ring-slate-500' : ''}"
                on:click={() => dispatch('select', rate.symbol)}
                on:keydown={(e) => e.key === 'Enter' && dispatch('select', rate.symbol)}
            >
                <span class="font-bold text-slate-200">{rate.symbol}</span>
                <div class="flex items-center gap-3">
                    <span class="font-mono text-slate-300">{rate.rate.toFixed(4)}</span>
                    <button
                        class="text-slate-500 hover:text-yellow-400 transition-colors p-1"
                        aria-label="Toggle favorite"
                        on:click={(e) => toggleFav(e, rate)}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 {isFavorite(rate) ? 'text-yellow-400 fill-current' : 'fill-none stroke-current'}" viewBox="0 0 24 24" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                        </svg>
                    </button>
                </div>
            </div>
        {:else}
            <div class="text-center text-slate-500 py-4 text-sm">No rates found</div>
        {/each}
    </div>
</div>
