<script lang="ts">
    import { onMount } from 'svelte';
    import {
        getMultiProviderSymbols,
        getSymbolsByNormalized,
        getRatesHistory,
        type MultiProviderSymbol,
        type SymbolItem
    } from '$lib/api';
    import CalendarPicker from '$lib/components/CalendarPicker.svelte';

    let multiProviderSymbols: MultiProviderSymbol[] = [];
    let selectedNormalized: string | null = null;
    let symbolVariants: SymbolItem[] = [];
    let loading = true;
    let loadingHistory = false;
    let search = '';
    let selectedDate = new Date().toISOString().split('T')[0];

    // Rate history per variant: { variantKey: { provider, providerSymbol, history } }
    // variantKey = `${provider}:${provider_symbol}` for unique identification
    let variantData: Record<string, { provider: string; providerSymbol: string; history: { date: string; rate: number | null }[] }> = {};

    // Date range
    const ranges = [
        { label: '7D', days: 7 },
        { label: '30D', days: 30 },
        { label: '3M', days: 90 },
        { label: '1Y', days: 365 },
        { label: '3Y', days: 1095 },
        { label: '5Y', days: 1825 },
        { label: '10Y', days: 3650 },
    ];
    let activeRange = 30;

    $: filtered = multiProviderSymbols.filter(s =>
        !search || s.symbol.toLowerCase().includes(search.toLowerCase())
    );

    onMount(async () => {
        try {
            multiProviderSymbols = await getMultiProviderSymbols();
        } catch (e) {
            console.error('Failed to load multi-provider symbols', e);
        } finally {
            loading = false;
        }
    });

    async function selectSymbol(normalized: string) {
        selectedNormalized = normalized;
        loadingHistory = true;
        variantData = {};

        try {
            symbolVariants = await getSymbolsByNormalized(normalized);
            await loadHistory();
        } catch (e) {
            console.error('Failed to load symbol variants', e);
        } finally {
            loadingHistory = false;
        }
    }

    async function loadHistory() {
        const toDate = new Date(selectedDate + 'T00:00:00');
        const fromDate = new Date(toDate);
        fromDate.setDate(toDate.getDate() - activeRange);

        const fromStr = fromDate.toISOString().split('T')[0];
        const toStr = selectedDate;

        const promises = symbolVariants.map(async (variant) => {
            // Use provider_symbol for exact match when fetching history
            const history = await getRatesHistory(variant.symbol, fromStr, toStr, variant.provider, variant.provider_symbol);
            const variantKey = `${variant.provider}:${variant.provider_symbol}`;
            return { variantKey, provider: variant.provider, providerSymbol: variant.provider_symbol, history };
        });

        const results = await Promise.all(promises);
        variantData = results.reduce((acc, r) => {
            acc[r.variantKey] = { provider: r.provider, providerSymbol: r.providerSymbol, history: r.history };
            return acc;
        }, {} as typeof variantData);
    }

    async function setRange(days: number) {
        activeRange = days;
        if (selectedNormalized) {
            loadingHistory = true;
            await loadHistory();
            loadingHistory = false;
        }
    }

    async function handleDateChange(e: CustomEvent<string>) {
        selectedDate = e.detail;
        if (selectedNormalized) {
            loadingHistory = true;
            await loadHistory();
            loadingHistory = false;
        }
    }

    function formatRate(rate: number | null): string {
        if (rate === null) return '-';
        return rate.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 });
    }

    // SVG chart dimensions
    const chartWidth = 600;
    const chartHeight = 200;
    const padding = { top: 20, right: 20, bottom: 30, left: 60 };

    function buildPath(history: { date: string; rate: number | null }[], minRate: number, maxRate: number): string {
        const validPoints = history.filter(h => h.rate !== null);
        if (validPoints.length < 2) return '';

        const xScale = (chartWidth - padding.left - padding.right) / (history.length - 1);
        const yRange = maxRate - minRate || 1;
        const yScale = (chartHeight - padding.top - padding.bottom) / yRange;

        let path = '';
        let started = false;

        history.forEach((point, i) => {
            if (point.rate === null) return;
            const x = padding.left + i * xScale;
            const y = chartHeight - padding.bottom - (point.rate - minRate) * yScale;
            if (!started) {
                path += `M ${x} ${y}`;
                started = true;
            } else {
                path += ` L ${x} ${y}`;
            }
        });

        return path;
    }

    const colors = ['#22d3ee', '#a78bfa', '#f472b6', '#4ade80', '#fb923c'];

    $: allHistory = Object.values(variantData).flatMap(d => d.history);
    $: allRates = allHistory.map(h => h.rate).filter((r): r is number => r !== null);
    $: minRate = allRates.length ? Math.min(...allRates) : 0;
    $: maxRate = allRates.length ? Math.max(...allRates) : 1;
    $: rateRange = maxRate - minRate || 1;
    $: paddedMin = minRate - rateRange * 0.05;
    $: paddedMax = maxRate + rateRange * 0.05;
</script>

<div class="bg-slate-950 text-slate-200 p-6">
    <header class="mb-8">
        <h1 class="text-3xl font-bold text-white">Compare</h1>
    </header>

    <div class="flex flex-col lg:flex-row gap-6">
        <!-- Symbol selector + Calendar -->
        <div class="w-full lg:w-80 flex-shrink-0 flex flex-col gap-4">
            <CalendarPicker {selectedDate} on:change={handleDateChange} />

            <div class="bg-slate-900 rounded-xl border border-slate-800 p-4">
                <input
                    type="text"
                    bind:value={search}
                    placeholder="Search symbols..."
                    class="w-full px-3 py-2 mb-4 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-slate-500"
                />

                {#if loading}
                    <div class="space-y-2">
                        {#each Array(5) as _}
                            <div class="h-12 bg-slate-800 rounded animate-pulse"></div>
                        {/each}
                    </div>
                {:else if filtered.length === 0}
                    <p class="text-slate-500 text-center py-4">No multi-provider symbols found.</p>
                {:else}
                    <div class="space-y-1 max-h-[50vh] overflow-y-auto">
                        {#each filtered as item}
                            <button
                                class="w-full text-left px-3 py-2 rounded-lg transition-colors {selectedNormalized === item.symbol ? 'bg-slate-700 text-white' : 'hover:bg-slate-800 text-slate-300'}"
                                on:click={() => selectSymbol(item.symbol)}
                            >
                                <div class="font-mono font-bold">{item.symbol}</div>
                                <div class="text-xs text-slate-500">{item.providers.join(', ')}</div>
                            </button>
                        {/each}
                    </div>
                {/if}
            </div>
        </div>

        <!-- Chart area -->
        <div class="flex-1">
            {#if !selectedNormalized}
                <div class="bg-slate-900 rounded-xl border border-slate-800 p-8 text-center text-slate-500">
                    Select a symbol to compare rates across providers.
                </div>
            {:else if loadingHistory}
                <div class="bg-slate-900 rounded-xl border border-slate-800 p-8">
                    <div class="h-64 flex items-center justify-center text-slate-500">
                        Loading rate history...
                    </div>
                </div>
            {:else}
                <div class="bg-slate-900 rounded-xl border border-slate-800 p-6">
                    <div class="flex items-center justify-between mb-6">
                        <h2 class="text-xl font-bold text-white">{selectedNormalized}</h2>
                        <div class="flex bg-slate-800 rounded-lg p-1">
                            {#each ranges as range}
                                <button
                                    class="px-3 py-1 text-xs font-medium rounded transition-colors {activeRange === range.days ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-slate-200'}"
                                    on:click={() => setRange(range.days)}
                                >
                                    {range.label}
                                </button>
                            {/each}
                        </div>
                    </div>

                    <!-- Combined chart -->
                    <div class="mb-6">
                        <svg viewBox="0 0 {chartWidth} {chartHeight}" class="w-full h-auto">
                            <!-- Y-axis labels -->
                            <text x={padding.left - 10} y={padding.top} text-anchor="end" class="fill-slate-500 text-xs">
                                {formatRate(paddedMax)}
                            </text>
                            <text x={padding.left - 10} y={chartHeight - padding.bottom} text-anchor="end" class="fill-slate-500 text-xs">
                                {formatRate(paddedMin)}
                            </text>

                            <!-- Grid lines -->
                            <line
                                x1={padding.left}
                                y1={padding.top}
                                x2={chartWidth - padding.right}
                                y2={padding.top}
                                stroke="#334155"
                                stroke-dasharray="4"
                            />
                            <line
                                x1={padding.left}
                                y1={chartHeight - padding.bottom}
                                x2={chartWidth - padding.right}
                                y2={chartHeight - padding.bottom}
                                stroke="#334155"
                                stroke-dasharray="4"
                            />

                            <!-- Rate lines per variant -->
                            {#each Object.entries(variantData) as [variantKey, data], i}
                                <path
                                    d={buildPath(data.history, paddedMin, paddedMax)}
                                    fill="none"
                                    stroke={colors[i % colors.length]}
                                    stroke-width="2"
                                />
                            {/each}
                        </svg>
                    </div>

                    <!-- Legend + rates for selected date -->
                    <div class="mb-2 text-xs text-slate-500">Rates for {selectedDate}</div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {#each Object.entries(variantData) as [variantKey, data], i}
                            {@const rateForDate = data.history.find(h => h.date === selectedDate)?.rate ?? data.history.findLast(h => h.rate !== null)?.rate}
                            <div class="flex items-center gap-3 p-3 bg-slate-800 rounded-lg">
                                <div
                                    class="w-3 h-3 rounded-full flex-shrink-0"
                                    style="background-color: {colors[i % colors.length]}"
                                ></div>
                                <div class="min-w-0 flex-1">
                                    <div class="text-sm font-medium text-white">{data.provider}</div>
                                    <div class="text-xs text-slate-500 truncate">{data.providerSymbol}</div>
                                </div>
                                <div class="text-right">
                                    <div class="font-mono text-white">{formatRate(rateForDate ?? null)}</div>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}
        </div>
    </div>
</div>
