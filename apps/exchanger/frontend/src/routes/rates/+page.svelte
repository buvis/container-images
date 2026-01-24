<script lang="ts">
    import { onMount } from 'svelte';
    import { 
        getRates, 
        getRatesHistory, 
        getCoverage, 
        getFavorites, 
        addFavorite, 
        removeFavorite,
        type Rate
    } from '$lib/api';
    
    import CalendarPicker from '$lib/components/CalendarPicker.svelte';
    import SymbolList from '$lib/components/SymbolList.svelte';
    import RateChart from '$lib/components/RateChart.svelte';
    import CalendarHeatmap from '$lib/components/CalendarHeatmap.svelte';

    let selectedDate = new Date().toISOString().split('T')[0];
    let selectedSymbol: string | null = null;
    let activeType: 'forex' | 'crypto' = 'forex';
    
    let rates: Rate[] = [];
    let favorites: string[] = [];
    let history: { date: string; rate: number | null }[] = [];
    let coverage: Record<string, number> = {};
    
    let loadingRates = false;
    let loadingHistory = false;
    
    // Derived provider
    $: provider = activeType === 'crypto' ? 'fcs' : 'cnb';
    $: year = parseInt(selectedDate.split('-')[0]);

    onMount(async () => {
        await loadFavorites();
        await loadCoverage();
        await loadRates();
    });

    async function loadFavorites() {
        try {
            favorites = await getFavorites();
        } catch (e) {
            console.error('Failed to load favorites', e);
        }
    }

    async function loadCoverage() {
        try {
            coverage = await getCoverage(year, provider, favorites.length ? favorites : undefined);
        } catch (e) {
            console.error('Failed to load coverage', e);
            coverage = {};
        }
    }

    async function loadRates() {
        loadingRates = true;
        try {
            rates = await getRates(selectedDate, provider, activeType);
        } catch (e) {
            console.error('Failed to load rates', e);
            rates = [];
        }
        loadingRates = false;
    }

    async function loadHistory(range: string = '30d', from?: string, to?: string) {
        if (!selectedSymbol) return;
        loadingHistory = true;
        
        if (!from || !to) {
            const t = new Date();
            const f = new Date();
            f.setDate(t.getDate() - 30);
            to = t.toISOString().split('T')[0];
            from = f.toISOString().split('T')[0];
        }

        try {
            history = await getRatesHistory(selectedSymbol, from, to, provider);
        } catch (e) {
            console.error('Failed to load history', e);
            history = [];
        }
        loadingHistory = false;
    }

    function handleDateChange(e: CustomEvent<string>) {
        const newDate = e.detail;
        const oldYear = year;
        selectedDate = newDate;
        
        const newYear = parseInt(selectedDate.split('-')[0]);
        if (newYear !== oldYear) {
            loadCoverage();
        }
        loadRates();
    }

    function handleTypeChange(e: CustomEvent<'forex' | 'crypto'>) {
        activeType = e.detail;
        selectedSymbol = null;
        history = [];
        setTimeout(() => {
            loadRates();
            loadCoverage();
        }, 0);
    }

    function handleSelectSymbol(e: CustomEvent<string>) {
        selectedSymbol = e.detail;
        loadHistory();
    }

    async function handleToggleFavorite(e: CustomEvent<string>) {
        const symbol = e.detail;
        try {
            if (favorites.includes(symbol)) {
                await removeFavorite(symbol);
                favorites = favorites.filter(f => f !== symbol);
            } else {
                await addFavorite(symbol);
                favorites = [...favorites, symbol];
            }
        } catch (error) {
            console.error('Failed to toggle favorite', error);
        }
    }

    function handleRangeChange(e: CustomEvent<{ from: string, to: string, range: string }>) {
        loadHistory(e.detail.range, e.detail.from, e.detail.to);
    }
</script>

<div class="min-h-screen bg-slate-950 text-slate-200 p-6 flex flex-col gap-6">
    <header>
        <div class="flex items-center justify-between mb-4">
            <h1 class="text-3xl font-bold text-white">Rates Explorer</h1>
            <a href="/" class="text-blue-400 hover:text-blue-300 text-sm font-medium">Back to Dashboard</a>
        </div>
        <CalendarHeatmap {year} {coverage} favoritesCount={favorites.length} />
    </header>

    <div class="flex flex-col lg:flex-row gap-6 flex-1 min-h-0">
        <!-- Sidebar -->
        <div class="w-full lg:w-96 flex flex-col gap-6">
            <CalendarPicker {selectedDate} on:change={handleDateChange} />
            
            <div class="flex-1 min-h-[400px]">
                <SymbolList 
                    {rates} 
                    {favorites} 
                    {selectedSymbol}
                    {activeType}
                    on:select={handleSelectSymbol}
                    on:toggleFavorite={handleToggleFavorite}
                    on:typeChange={handleTypeChange}
                />
            </div>
        </div>

        <!-- Main Chart -->
        <div class="flex-1 min-h-[500px]">
            <RateChart 
                symbol={selectedSymbol} 
                {history} 
                isLoading={loadingHistory}
                on:rangeChange={handleRangeChange}
            />
        </div>
    </div>
</div>
