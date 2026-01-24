<script lang="ts">
    import { onMount } from 'svelte';
    import { getRate, getFavorites, getSymbols, type SymbolItem, type Favorite } from '$lib/api';
    import { formatRate as fmtRate, formatResult as fmtResult, isCrypto } from '$lib/formatters';
    import CalendarPicker from '$lib/components/CalendarPicker.svelte';

    let symbols: SymbolItem[] = [];
    let favorites: Favorite[] = [];
    let loading = true;

    let selectedSymbol = '';
    let amount = 1;
    let date = new Date().toISOString().split('T')[0];
    let reversed = false;

    let rates: Record<string, number | null> = {};
    let converting = false;
    let error = '';
    let showCalendar = false;

    $: favoriteKeys = new Set(favorites.map(f => `${f.provider}:${f.provider_symbol}`));

    function isFavorite(s: SymbolItem): boolean {
        return favoriteKeys.has(`${s.provider}:${s.provider_symbol}`);
    }

    $: favoriteSymbols = symbols.filter(s => isFavorite(s));
    $: otherSymbols = symbols.filter(s => !isFavorite(s));

    onMount(async () => {
        try {
            const [syms, favs] = await Promise.all([
                getSymbols(),
                getFavorites()
            ]);
            symbols = syms;
            favorites = favs;
            // Find first favorite symbol
            const favKeys = new Set(favs.map(f => `${f.provider}:${f.provider_symbol}`));
            const firstFav = syms.find(s => favKeys.has(`${s.provider}:${s.provider_symbol}`));
            if (firstFav) {
                selectedSymbol = firstFav.symbol;
                await convert();
            }
        } catch (e) {
            console.error('Failed to load data', e);
        } finally {
            loading = false;
        }
    });

    async function convert() {
        if (!selectedSymbol) return;

        converting = true;
        error = '';
        rates = {};

        try {
            const result = await getRate(date, selectedSymbol, 'all');
            if ('rates' in result) {
                rates = result.rates;
            } else {
                rates = { default: result.rate };
            }
        } catch (e) {
            error = e instanceof Error ? e.message : 'Conversion failed';
        } finally {
            converting = false;
        }
    }

    function handleSymbolChange() {
        convert();
    }

    function handleDateChange() {
        convert();
    }

    function toggleCalendar() {
        showCalendar = !showCalendar;
    }

    function handleDateSelect(event: CustomEvent<string>) {
        date = event.detail;
        showCalendar = false;
        handleDateChange();
    }

    function toggleReversed() {
        reversed = !reversed;
    }

    // Get the selected symbol's type for formatting
    $: selectedSymbolData = symbols.find(s => s.symbol === selectedSymbol);
    $: symbolType = (selectedSymbolData?.type === 'crypto' ? 'crypto' : 'forex') as 'forex' | 'crypto';

    $: inputCurrency = reversed ? symbolParts.to : symbolParts.from;
    $: outputCurrency = reversed ? symbolParts.from : symbolParts.to;

    function formatRateDisplay(rate: number | null): string {
        return fmtRate(rate, symbolType);
    }

    function formatResultDisplay(rate: number | null, amt: number, rev: boolean): string {
        if (rate === null) return 'N/A';
        const result = rev ? amt / rate : amt * rate;
        return fmtResult(result, outputCurrency);
    }

    function filterNumericInput(e: Event) {
        const input = e.target as HTMLInputElement;
        input.value = input.value.replace(/[^0-9.]/g, '');
        amount = parseFloat(input.value) || 0;
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

    $: symbolParts = getSymbolParts(selectedSymbol);
</script>


<svelte:window on:click={() => (showCalendar = false)} />

<div class="bg-slate-950 text-slate-200 p-6">
    <header class="mb-8">
        <div class="flex items-center justify-between">
            <h1 class="text-3xl font-bold text-white">Converter</h1>
            <a
                href="/converter/multi"
                class="text-sm text-slate-400 hover:text-cyan-400 transition-colors flex items-center gap-1"
            >
                Chain Converter
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
            </a>
        </div>
    </header>

    {#if loading}
        <div class="max-w-xl mx-auto">
            <div class="bg-slate-900 p-8 rounded-xl border border-slate-800 animate-pulse h-64"></div>
        </div>
    {:else}
        <div class="max-w-xl mx-auto space-y-6">
            <!-- Converter Card -->
            <div class="bg-slate-900 p-6 rounded-xl border border-slate-800">
                <!-- Amount Input -->
                <div class="mb-4">
                    <label for="amount" class="block text-sm font-medium text-slate-400 mb-2">Amount in {inputCurrency}</label>
                    <div class="relative">
                        <input
                            id="amount"
                            type="text"
                            inputmode="decimal"
                            value={amount}
                            on:input={filterNumericInput}
                            class="w-full px-4 py-3 pr-16 bg-slate-800 border border-slate-700 rounded-lg text-white text-2xl font-mono focus:outline-none focus:border-slate-500"
                        />
                        <span class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 font-mono">
                            {inputCurrency}
                        </span>
                    </div>
                </div>

                <!-- Swap Button -->
                <div class="flex justify-center mb-4">
                    <button
                        on:click={toggleReversed}
                        class="p-2 rounded-full bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-400 hover:text-white transition-colors"
                        title="Swap direction"
                        aria-label="Swap conversion direction"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M5 12a1 1 0 102 0V6.414l1.293 1.293a1 1 0 001.414-1.414l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L5 6.414V12z"/>
                            <path d="M15 8a1 1 0 10-2 0v5.586l-1.293-1.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L15 13.586V8z"/>
                        </svg>
                    </button>
                </div>

                <!-- Symbol Select -->
                <div class="mb-6">
                    <label for="symbol" class="block text-sm font-medium text-slate-400 mb-2">Currency Pair</label>
                    <select
                        id="symbol"
                        bind:value={selectedSymbol}
                        on:change={handleSymbolChange}
                        class="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-slate-500"
                    >
                        {#if favoriteSymbols.length > 0}
                            <optgroup label="Favorites">
                                {#each favoriteSymbols as s}
                                    <option value={s.symbol}>{s.symbol} - {s.name}</option>
                                {/each}
                            </optgroup>
                        {/if}
                        <optgroup label="All Symbols">
                            {#each otherSymbols as s}
                                <option value={s.symbol}>{s.symbol} - {s.name}</option>
                            {/each}
                        </optgroup>
                    </select>
                </div>

                <!-- Date -->
                <div class="mb-6 relative">
                    <label for="date-btn" class="block text-sm font-medium text-slate-400 mb-2">Date</label>
                    <button
                        id="date-btn"
                        type="button"
                        on:click|stopPropagation={toggleCalendar}
                        class="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white text-left flex items-center justify-between focus:outline-none focus:border-slate-500 hover:bg-slate-750 transition-colors"
                    >
                        <span>{date}</span>
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                    </button>
                    
                    {#if showCalendar}
                        <!-- svelte-ignore a11y_click_events_have_key_events -->
                        <!-- svelte-ignore a11y_no_static_element_interactions -->
                        <div class="absolute top-full left-0 mt-2 z-50 shadow-xl w-full max-w-sm" on:click|stopPropagation>
                            <CalendarPicker selectedDate={date} on:change={handleDateSelect} />
                        </div>
                    {/if}
                </div>

                <!-- Convert Button -->
                <button
                    on:click={convert}
                    disabled={converting || !selectedSymbol}
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
            {:else if Object.keys(rates).length > 0}
                <div class="bg-slate-900 p-6 rounded-xl border border-slate-800">
                    <h2 class="text-sm font-medium text-slate-400 mb-4">Results</h2>

                    <div class="space-y-4">
                        {#each Object.entries(rates) as [provider, rate]}
                            <div class="flex items-center justify-between p-4 bg-slate-800 rounded-lg">
                                <div>
                                    <span class="text-xs text-slate-500 uppercase">{provider}</span>
                                    <div class="text-sm text-slate-400">
                                        {#if reversed}
                                            1 {symbolParts.to} = {rate !== null ? formatRateDisplay(1 / rate) : 'N/A'} {symbolParts.from}
                                        {:else}
                                            1 {symbolParts.from} = {formatRateDisplay(rate)} {symbolParts.to}
                                        {/if}
                                    </div>
                                </div>
                                <div class="text-right">
                                    <div class="text-2xl font-bold text-white font-mono">
                                        {formatResultDisplay(rate, amount, reversed)}
                                    </div>
                                    <div class="text-sm text-slate-500">{outputCurrency}</div>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}
        </div>
    {/if}
</div>
