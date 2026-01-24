<script lang="ts">
    import { onMount } from 'svelte';
    import {
        getSymbols,
        getFavorites,
        addFavorite,
        removeFavorite,
        getProvidersStatus,
        type SymbolItem,
        type ProviderStatus,
        type Favorite
    } from '$lib/api';
    import SearchInput from '$lib/components/ui/SearchInput.svelte';
    import FilterPills from '$lib/components/ui/FilterPills.svelte';

    let symbols: SymbolItem[] = [];
    let favorites: Favorite[] = [];
    let providers: ProviderStatus[] = [];
    let selectedProviders: Set<string> = new Set();
    let loading = true;
    let search = '';
    let selectedTypes: Set<string> = new Set();

    // Base filtered by search only (for computing filter counts)
    $: searchFiltered = symbols.filter(s =>
        !search ||
        s.symbol.toLowerCase().includes(search.toLowerCase()) ||
        s.name.toLowerCase().includes(search.toLowerCase())
    );

    // Type counts: filtered by providers + search (excludes type filter)
    $: typeOptions = (() => {
        const base = searchFiltered.filter(s =>
            selectedProviders.size === 0 || selectedProviders.has(s.provider)
        );
        return [
            { name: 'forex', count: base.filter(s => s.type === 'forex').length },
            { name: 'crypto', count: base.filter(s => s.type === 'crypto').length }
        ];
    })();

    // Provider counts: filtered by types + search (excludes provider filter)
    $: providerOptions = (() => {
        const base = searchFiltered.filter(s =>
            selectedTypes.size === 0 || selectedTypes.has(s.type)
        );
        return providers.map(p => ({
            name: p.name,
            count: base.filter(s => s.provider === p.name).length
        }));
    })();

    $: filtered = symbols.filter(s => {
        const matchesProvider = selectedProviders.size === 0 || selectedProviders.has(s.provider);
        const matchesType = selectedTypes.size === 0 || selectedTypes.has(s.type);
        const matchesSearch = !search ||
            s.symbol.toLowerCase().includes(search.toLowerCase()) ||
            s.name.toLowerCase().includes(search.toLowerCase());
        return matchesProvider && matchesType && matchesSearch;
    });

    $: grouped = filtered.reduce((acc, s) => {
        const key = s.provider;
        if (!acc[key]) acc[key] = [];
        acc[key].push(s);
        return acc;
    }, {} as Record<string, SymbolItem[]>);

    // Reactive set for template reactivity
    $: favoriteKeys = new Set(favorites.map(f => `${f.provider}:${f.provider_symbol}`));

    onMount(async () => {
        try {
            [symbols, favorites, providers] = await Promise.all([
                getSymbols(),
                getFavorites(),
                getProvidersStatus()
            ]);
        } catch (e) {
            console.error('Failed to load symbols', e);
        } finally {
            loading = false;
        }
    });

    function getFavoriteKey(s: SymbolItem): string {
        return `${s.provider}:${s.provider_symbol}`;
    }

    async function toggleFavorite(s: SymbolItem) {
        try {
            if (favoriteKeys.has(getFavoriteKey(s))) {
                await removeFavorite(s.provider, s.provider_symbol);
                favorites = favorites.filter(f => !(f.provider === s.provider && f.provider_symbol === s.provider_symbol));
            } else {
                await addFavorite(s.provider, s.provider_symbol);
                favorites = [...favorites, { provider: s.provider, provider_symbol: s.provider_symbol }];
            }
        } catch (e) {
            console.error('Failed to toggle favorite', e);
        }
    }

    function getTypeColor(type: string): string {
        return type === 'crypto' ? 'text-amber-400' : 'text-cyan-400';
    }
</script>

<div class="bg-slate-950 text-slate-200 p-6">
    <header class="mb-6">
        <h1 class="text-3xl font-bold text-white mb-4">Symbols</h1>

        <div class="flex flex-col gap-4">
            <SearchInput bind:value={search} placeholder="Search symbols..." />

            <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
                <FilterPills options={typeOptions} bind:selected={selectedTypes} />
                
                <div class="hidden sm:block w-px h-6 bg-slate-800"></div>

                <div class="flex-1">
                    <FilterPills options={providerOptions} bind:selected={selectedProviders} />
                </div>
            </div>
        </div>
    </header>

    {#if loading}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {#each Array(9) as _}
                <div class="bg-slate-900 p-4 rounded-lg border border-slate-800 animate-pulse h-20"></div>
            {/each}
        </div>
    {:else if filtered.length === 0}
        <div class="text-center py-12 text-slate-500">
            No symbols found matching your criteria.
        </div>
    {:else}
        <div class="space-y-8">
            {#each Object.entries(grouped) as [provider, providerSymbols]}
                <section>
                    <h2 class="text-lg font-semibold text-slate-400 mb-3 uppercase tracking-wide">
                        {provider}
                        <span class="text-slate-600 font-normal text-sm ml-2">({providerSymbols.length})</span>
                    </h2>

                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                        {#each providerSymbols as symbol}
                            <div class="bg-slate-900 p-4 rounded-lg border border-slate-800 hover:border-slate-700 transition-colors flex items-start justify-between gap-3">
                                <div class="min-w-0 flex-1">
                                    <div class="flex items-center gap-2">
                                        <span class="font-mono font-bold text-white">{symbol.symbol}</span>
                                        <span class="text-xs {getTypeColor(symbol.type)}">{symbol.type}</span>
                                    </div>
                                    <p class="text-sm text-slate-400 truncate" title={symbol.name}>{symbol.name}</p>
                                </div>

                                <button
                                    class="p-1.5 rounded hover:bg-slate-800 transition-colors flex-shrink-0 cursor-pointer"
                                    on:click={() => toggleFavorite(symbol)}
                                    title={favoriteKeys.has(getFavoriteKey(symbol)) ? 'Remove from favorites' : 'Add to favorites'}
                                    aria-label={favoriteKeys.has(getFavoriteKey(symbol)) ? 'Remove from favorites' : 'Add to favorites'}
                                >
                                    <svg
                                        xmlns="http://www.w3.org/2000/svg"
                                        class="h-5 w-5 {favoriteKeys.has(getFavoriteKey(symbol)) ? 'text-yellow-400 fill-yellow-400' : 'text-slate-600'}"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        stroke-width="2"
                                    >
                                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                                    </svg>
                                </button>
                            </div>
                        {/each}
                    </div>
                </section>
            {/each}
        </div>

        <div class="mt-6 text-sm text-slate-500 text-center">
            Showing {filtered.length} of {symbols.length} symbols
        </div>
    {/if}
</div>
