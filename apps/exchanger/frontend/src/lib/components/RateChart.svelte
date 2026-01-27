<script lang="ts">
    import Chart from 'chart.js/auto';
    import { createEventDispatcher, onMount, onDestroy } from 'svelte';

    export let symbol: string | null = null;
    export let history: { date: string; rate: number | null }[] = [];
    export let isLoading: boolean = false;
    export let activeRange: string = '30d';

    const dispatch = createEventDispatcher();

    let canvas: HTMLCanvasElement;
    let chart: Chart;

    const ranges = [
        { label: '7D', value: '7d', days: 7 },
        { label: '30D', value: '30d', days: 30 },
        { label: '3M', value: '3m', days: 90 },
        { label: '6M', value: '6m', days: 180 },
        { label: '1Y', value: '1y', days: 365 },
        { label: '3Y', value: '3y', days: 1095 },
        { label: '5Y', value: '5y', days: 1825 },
        { label: '10Y', value: '10y', days: 3650 },
    ];

    function setRange(range: typeof ranges[0]) {
        const to = new Date();
        const from = new Date();
        from.setDate(to.getDate() - range.days);

        const toStr = to.toISOString().split('T')[0];
        const fromStr = from.toISOString().split('T')[0];

        dispatch('rangeChange', { from: fromStr, to: toStr, range: range.value, days: range.days });
    }

    $: validRates = history.map((h, i) => ({ rate: h.rate, index: i })).filter(r => r.rate !== null);
    $: minEntry = validRates.length > 0 ? validRates.reduce((a, b) => (a.rate! < b.rate!) ? a : b) : null;
    $: maxEntry = validRates.length > 0 ? validRates.reduce((a, b) => (a.rate! > b.rate!) ? a : b) : null;

    $: pointRadii = history.map((_, i) => {
        if (minEntry && i === minEntry.index) return 6;
        if (maxEntry && i === maxEntry.index) return 6;
        return 0;
    });

    $: pointColors = history.map((_, i) => {
        if (minEntry && i === minEntry.index) return '#ef4444'; // red for low
        if (maxEntry && i === maxEntry.index) return '#22c55e'; // green for high
        return 'rgb(59, 130, 246)';
    });

    $: pointBorderColors = history.map((_, i) => {
        if (minEntry && i === minEntry.index) return '#fff';
        if (maxEntry && i === maxEntry.index) return '#fff';
        return 'rgb(59, 130, 246)';
    });

    $: data = {
        labels: history.map(h => h.date),
        datasets: [
            {
                label: symbol || 'Rate',
                fill: true,
                tension: 0.3,
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderColor: 'rgb(59, 130, 246)',
                pointRadius: pointRadii,
                pointBackgroundColor: pointColors,
                pointBorderColor: pointBorderColors,
                pointBorderWidth: 2,
                pointHitRadius: 10,
                data: history.map(h => h.rate),
            },
        ],
    };

    const options: any = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
                grid: { color: 'rgba(148, 163, 184, 0.1)' },
                ticks: { color: '#94a3b8' }
            },
            y: {
                grid: { color: 'rgba(148, 163, 184, 0.1)' },
                ticks: { color: '#94a3b8' }
            }
        },
        plugins: {
            legend: { display: false },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: 'rgba(15, 23, 42, 0.9)',
                titleColor: '#f1f5f9',
                bodyColor: '#cbd5e1',
                borderColor: '#334155',
                borderWidth: 1
            }
        },
        interaction: {
            mode: 'nearest',
            axis: 'x',
            intersect: false
        }
    };

    onMount(() => {
        if (canvas) {
            chart = new Chart(canvas, {
                type: 'line',
                data: data,
                options: options
            });
        }
    });

    onDestroy(() => {
        if (chart) {
            chart.destroy();
        }
    });

    $: if (chart && data) {
        chart.data = data;
        chart.update('none');
    }
</script>

<div class="bg-slate-800 rounded-lg shadow-lg p-4 h-full flex flex-col border border-slate-700">
    <div class="flex justify-between items-center mb-4">
        <h2 class="text-xl font-bold text-slate-200">
            {symbol ? `${symbol} History` : 'Select a symbol'}
        </h2>
        
        <div class="flex bg-slate-900 rounded-lg p-1">
            {#each ranges as range}
                <button
                    class="px-3 py-1 text-xs font-medium rounded transition-colors {activeRange === range.value ? 'bg-slate-700 text-white shadow' : 'text-slate-400 hover:text-slate-200'}"
                    on:click={() => setRange(range)}
                >
                    {range.label}
                </button>
            {/each}
        </div>
    </div>

    <div class="flex-1 relative min-h-[300px]">
        {#if isLoading}
            <div class="absolute inset-0 flex items-center justify-center bg-slate-800/50 z-10">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
        {/if}
        
        <div class="w-full h-full" style:display={symbol && history.length > 0 ? 'block' : 'none'}>
             <canvas bind:this={canvas}></canvas>
        </div>

        {#if !symbol}
            <div class="absolute inset-0 flex items-center justify-center text-slate-500">
                Select a symbol to view history
            </div>
        {:else if history.length === 0 && !isLoading}
             <div class="absolute inset-0 flex items-center justify-center text-slate-500">
                No data available
            </div>
        {/if}
    </div>

    {#if symbol && history.length > 0 && minEntry && maxEntry}
        <div class="flex gap-6 mt-3 pt-3 border-t border-slate-700 text-sm">
            <div class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-full bg-red-500 border-2 border-white"></span>
                <span class="text-slate-400">Low:</span>
                <span class="text-red-400 font-medium">{history[minEntry.index].rate?.toFixed(4)}</span>
                <span class="text-slate-500">({history[minEntry.index].date})</span>
            </div>
            <div class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-full bg-green-500 border-2 border-white"></span>
                <span class="text-slate-400">High:</span>
                <span class="text-green-400 font-medium">{history[maxEntry.index].rate?.toFixed(4)}</span>
                <span class="text-slate-500">({history[maxEntry.index].date})</span>
            </div>
        </div>
    {/if}
</div>
