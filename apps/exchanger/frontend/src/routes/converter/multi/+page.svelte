<script lang="ts">
    import CalendarPicker from '$lib/components/CalendarPicker.svelte';
    import { onMount } from 'svelte';
    import {
        getSymbols,
        getFavorites,
        getChainRate,
        type SymbolItem,
        type Favorite,
        type ChainRate
    } from '$lib/api';
    import { formatRate, formatResult, isCrypto } from '$lib/formatters';

    let symbols: SymbolItem[] = [];
    let favorites: Favorite[] = [];
    let loading = true;

    // Form state
    let fromCurrency = '';
    let intermediateCurrency = '';
    let toCurrency = '';
    let fromProvider = '';
    let toProvider = '';
    let amount = 1;
    let date = new Date().toISOString().split('T')[0];
    let showCalendar = false;

    function toggleCalendar() {
        showCalendar = !showCalendar;
    }

    function handleDateSelect(event: CustomEvent<string>) {
        date = event.detail;
        showCalendar = false;
    }

    // Result state
    let result: ChainRate | null = null;
    let converting = false;
    let error = '';

    // Derived: unique currencies
    $: allCurrencies = [...new Set(symbols.flatMap(s => {
        const parts = getSymbolParts(s.symbol);
        return [parts.from, parts.to];
    }))].sort();

    // Find providers that can handle the leg (either direct or inverted symbol)
    function getProvidersForLeg(base: string, quote: string): string[] {
        if (!base || !quote) return [];
        const direct = `${base}${quote}`;
        const inverted = `${quote}${base}`;
        const providers = new Set<string>();
        for (const s of symbols) {
            if (s.symbol === direct || s.symbol === inverted) {
                providers.add(s.provider);
            }
        }
        return [...providers].sort();
    }

    $: fromProviders = getProvidersForLeg(fromCurrency, intermediateCurrency);
    $: toProviders = getProvidersForLeg(intermediateCurrency, toCurrency);

    // Favorites for auto-selection
    $: favoriteKeys = new Set(favorites.map(f => `${f.provider}:${f.provider_symbol}`));

    function isFavoriteProvider(base: string, quote: string, provider: string): boolean {
        const direct = `${base}${quote}`;
        const inverted = `${quote}${base}`;
        for (const s of symbols) {
            if ((s.symbol === direct || s.symbol === inverted) && s.provider === provider) {
                if (favoriteKeys.has(`${provider}:${s.provider_symbol}`)) return true;
            }
        }
        return false;
    }

    // Auto-select best provider (prefer favorites)
    $: {
        if (fromProviders.length > 0 && !fromProviders.includes(fromProvider)) {
            const fav = fromProviders.find(p => isFavoriteProvider(fromCurrency, intermediateCurrency, p));
            fromProvider = fav || fromProviders[0];
        }
        if (fromProviders.length === 0) fromProvider = '';
    }
    $: {
        if (toProviders.length > 0 && !toProviders.includes(toProvider)) {
            const fav = toProviders.find(p => isFavoriteProvider(intermediateCurrency, toCurrency, p));
            toProvider = fav || toProviders[0];
        }
        if (toProviders.length === 0) toProvider = '';
    }

    function getSymbolParts(symbol: string): { from: string; to: string } {
        if (symbol.includes('/')) {
            const [from, to] = symbol.split('/');
            return { from, to };
        }
        if (symbol.length === 6) {
            return { from: symbol.slice(0, 3), to: symbol.slice(3) };
        }
        return { from: symbol, to: '?' };
    }

    onMount(async () => {
        try {
            const [syms, favs] = await Promise.all([
                getSymbols(),
                getFavorites()
            ]);
            symbols = syms;
            favorites = favs;

            // Set sensible defaults if we have data
            if (allCurrencies.includes('BTC')) fromCurrency = 'BTC';
            if (allCurrencies.includes('EUR')) intermediateCurrency = 'EUR';
            if (allCurrencies.includes('CZK')) toCurrency = 'CZK';
        } catch (e) {
            console.error('Failed to load data', e);
        } finally {
            loading = false;
        }
    });

    $: canConvert = fromCurrency && intermediateCurrency && toCurrency && fromProvider && toProvider;

    async function convert() {
        if (!canConvert) {
            error = 'Please select all currencies and providers';
            return;
        }

        converting = true;
        error = '';
        result = null;

        try {
            result = await getChainRate(
                date,
                fromCurrency,
                intermediateCurrency,
                toCurrency,
                fromProvider,
                toProvider
            );
        } catch (e) {
            error = e instanceof Error ? e.message : 'Conversion failed';
        } finally {
            converting = false;
        }
    }

    $: fromType = (isCrypto(fromCurrency) ? 'crypto' : 'forex') as 'crypto' | 'forex';

    function formatFromRate(rate: number | null): string {
        return formatRate(rate, fromType);
    }

    function formatToRate(rate: number | null): string {
        return formatRate(rate, 'forex');
    }

    function formatFinalResult(rate: number | null, amt: number): string {
        if (rate === null) return 'N/A';
        return formatResult(amt * rate, toCurrency);
    }

    function filterNumericInput(e: Event) {
        const input = e.target as HTMLInputElement;
        input.value = input.value.replace(/[^0-9.]/g, '');
        amount = parseFloat(input.value) || 0;
    }

    function formatCombinedRate(rate: number | null): string {
        if (rate === null) return 'N/A';
        const decimals = rate > 1000 ? 2 : rate < 0.0001 ? 8 : 4;
        return rate.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: decimals
        });
    }

    // Display label for first leg showing which symbol and if inverted
    $: fromLegLabel = fromCurrency && intermediateCurrency
        ? `${fromCurrency}/${intermediateCurrency}`
        : '---';

    $: toLegLabel = intermediateCurrency && toCurrency
        ? `${intermediateCurrency}/${toCurrency}`
        : '---';
</script>


<svelte:window on:click={() => (showCalendar = false)} />

<div class="bg-slate-950 text-slate-200 p-6">
    <header class="mb-8">
        <h1 class="text-3xl font-bold text-white">Chain Converter</h1>
    </header>

    {#if loading}
        <div class="max-w-2xl mx-auto">
            <div class="bg-slate-900 p-8 rounded-xl border border-slate-800 animate-pulse h-96"></div>
        </div>
    {:else}
        <div class="max-w-2xl mx-auto space-y-6">
            <!-- Converter Card -->
            <div class="bg-slate-900 p-6 rounded-xl border border-slate-800">
                <!-- Currency Chain -->
                <div class="grid grid-cols-5 gap-2 mb-6 items-end">
                    <!-- From Currency -->
                    <div class="col-span-1">
                        <label for="from" class="block text-xs font-medium text-slate-500 mb-1">From</label>
                        <select
                            id="from"
                            bind:value={fromCurrency}
                            class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-slate-500"
                        >
                            <option value="">--</option>
                            {#each allCurrencies as c}
                                <option value={c}>{c}</option>
                            {/each}
                        </select>
                    </div>

                    <!-- Arrow -->
                    <div class="flex justify-center items-center text-slate-600 pb-2">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" />
                        </svg>
                    </div>

                    <!-- Intermediate Currency -->
                    <div class="col-span-1">
                        <label for="intermediate" class="block text-xs font-medium text-slate-500 mb-1">Via</label>
                        <select
                            id="intermediate"
                            bind:value={intermediateCurrency}
                            class="w-full px-3 py-2 bg-slate-800 border border-cyan-700 rounded-lg text-cyan-400 text-sm focus:outline-none focus:border-cyan-500"
                        >
                            <option value="">--</option>
                            {#each allCurrencies as c}
                                <option value={c}>{c}</option>
                            {/each}
                        </select>
                    </div>

                    <!-- Arrow -->
                    <div class="flex justify-center items-center text-slate-600 pb-2">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" />
                        </svg>
                    </div>

                    <!-- To Currency -->
                    <div class="col-span-1">
                        <label for="to" class="block text-xs font-medium text-slate-500 mb-1">To</label>
                        <select
                            id="to"
                            bind:value={toCurrency}
                            class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-slate-500"
                        >
                            <option value="">--</option>
                            {#each allCurrencies as c}
                                <option value={c}>{c}</option>
                            {/each}
                        </select>
                    </div>
                </div>

                <!-- Provider Selection -->
                <div class="grid grid-cols-2 gap-4 mb-6">
                    <!-- First Leg Provider -->
                    <div>
                        <label for="fromProvider" class="block text-xs font-medium text-slate-500 mb-1">
                            {fromLegLabel} provider
                        </label>
                        <select
                            id="fromProvider"
                            bind:value={fromProvider}
                            disabled={fromProviders.length === 0}
                            class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-slate-500 disabled:opacity-50"
                        >
                            {#if fromProviders.length === 0}
                                <option value="">No provider available</option>
                            {:else}
                                {#each fromProviders as p}
                                    <option value={p}>{p}</option>
                                {/each}
                            {/if}
                        </select>
                    </div>

                    <!-- Second Leg Provider -->
                    <div>
                        <label for="toProvider" class="block text-xs font-medium text-slate-500 mb-1">
                            {toLegLabel} provider
                        </label>
                        <select
                            id="toProvider"
                            bind:value={toProvider}
                            disabled={toProviders.length === 0}
                            class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-slate-500 disabled:opacity-50"
                        >
                            {#if toProviders.length === 0}
                                <option value="">No provider available</option>
                            {:else}
                                {#each toProviders as p}
                                    <option value={p}>{p}</option>
                                {/each}
                            {/if}
                        </select>
                    </div>
                </div>

                <!-- Amount and Date -->
                <div class="grid grid-cols-2 gap-4 mb-6">
                    <div>
                        <label for="amount" class="block text-xs font-medium text-slate-500 mb-1">Amount in {fromCurrency || '---'}</label>
                        <div class="relative">
                            <input
                                id="amount"
                                type="text"
                                inputmode="decimal"
                                value={amount}
                                on:input={filterNumericInput}
                                class="w-full px-3 py-2 pr-12 bg-slate-800 border border-slate-700 rounded-lg text-white text-lg font-mono focus:outline-none focus:border-slate-500"
                            />
                            <span class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 font-mono text-sm">
                                {fromCurrency || '---'}
                            </span>
                        </div>
                    </div>

                    <div class="relative">
                        <label for="date" class="block text-xs font-medium text-slate-500 mb-1">Date</label>
                        <button
                            type="button"
                            class="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-left focus:outline-none focus:border-slate-500 flex items-center justify-between"
                            on:click|stopPropagation={toggleCalendar}
                        >
                            <span>{date}</span>
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                        </button>

                        {#if showCalendar}
                            <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
                            <div
                                class="absolute right-0 top-full mt-2 z-50 shadow-xl rounded-lg overflow-hidden"
                                on:click|stopPropagation
                            >
                                <CalendarPicker selectedDate={date} on:change={handleDateSelect} />
                            </div>
                        {/if}
                    </div>
                </div>

                <!-- Convert Button -->
                <button
                    on:click={convert}
                    disabled={converting || !canConvert}
                    class="w-full py-3 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-medium rounded-lg transition-colors"
                >
                    {converting ? 'Converting...' : 'Convert'}
                </button>
            </div>

            <!-- Results -->
            {#if error}
                <div class="bg-red-900/30 border border-red-800 text-red-400 p-4 rounded-lg">
                    {error}
                </div>
            {:else if result}
                <div class="bg-slate-900 p-6 rounded-xl border border-slate-800">
                    <h2 class="text-sm font-medium text-slate-400 mb-4">Calculation Breakdown</h2>

                    <!-- Step-by-step breakdown -->
                    <div class="space-y-3 mb-6">
                        <!-- First leg -->
                        <div class="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                            <div class="flex items-center gap-2 flex-wrap">
                                <span class="text-xs text-slate-500 uppercase w-12">{result.from_provider}</span>
                                <span class="text-slate-300">1 {fromCurrency}</span>
                                <span class="text-slate-500">=</span>
                                <span class="text-white font-mono">{formatFromRate(result.from_rate)}</span>
                                <span class="text-cyan-400">{intermediateCurrency}</span>
                                {#if result.from_inverted}
                                    <span class="text-xs text-amber-500 ml-1" title="Using inverted rate from {result.from_symbol}">
                                        (1/{result.from_symbol})
                                    </span>
                                {:else}
                                    <span class="text-xs text-slate-600 ml-1">
                                        ({result.from_symbol})
                                    </span>
                                {/if}
                            </div>
                        </div>

                        <!-- Multiplication sign -->
                        <div class="flex justify-center text-slate-500 text-xl">×</div>

                        <!-- Second leg -->
                        <div class="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                            <div class="flex items-center gap-2 flex-wrap">
                                <span class="text-xs text-slate-500 uppercase w-12">{result.to_provider}</span>
                                <span class="text-slate-300">1 {intermediateCurrency}</span>
                                <span class="text-slate-500">=</span>
                                <span class="text-white font-mono">{formatToRate(result.to_rate)}</span>
                                <span class="text-slate-300">{toCurrency}</span>
                                {#if result.to_inverted}
                                    <span class="text-xs text-amber-500 ml-1" title="Using inverted rate from {result.to_symbol}">
                                        (1/{result.to_symbol})
                                    </span>
                                {:else}
                                    <span class="text-xs text-slate-600 ml-1">
                                        ({result.to_symbol})
                                    </span>
                                {/if}
                            </div>
                        </div>

                        <!-- Equals sign -->
                        <div class="flex justify-center text-slate-500 text-xl">=</div>

                        <!-- Combined rate -->
                        <div class="flex items-center justify-between p-3 bg-slate-800 rounded-lg border border-slate-700">
                            <div class="flex items-center gap-2">
                                <span class="text-xs text-slate-500 uppercase w-12">rate</span>
                                <span class="text-slate-300">1 {fromCurrency}</span>
                                <span class="text-slate-500">=</span>
                                <span class="text-white font-mono font-bold">{formatCombinedRate(result.combined_rate)}</span>
                                <span class="text-slate-300">{toCurrency}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Final result -->
                    <div class="border-t border-slate-800 pt-4">
                        <div class="flex items-center justify-between">
                            <div class="text-slate-400">
                                Your {amount} {fromCurrency}
                            </div>
                            <div class="text-right">
                                <div class="text-3xl font-bold text-white font-mono">
                                    {formatFinalResult(result.combined_rate, amount)}
                                </div>
                                <div class="text-sm text-slate-500">{toCurrency}</div>
                            </div>
                        </div>
                    </div>
                </div>
            {/if}
        </div>
    {/if}
</div>
