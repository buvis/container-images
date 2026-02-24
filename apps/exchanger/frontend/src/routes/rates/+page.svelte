<script lang="ts">
    import { onMount } from 'svelte';
    import { 
        getRates, 
        getRatesHistory, 
        getFavorites, 
        addFavorite, 
        removeFavorite,
        type Rate,
        type Favorite
    } from '$lib/api';
    
    import CalendarPicker from '$lib/components/CalendarPicker.svelte';
    import SymbolList from '$lib/components/SymbolList.svelte';
    import RateChart from '$lib/components/RateChart.svelte';

    let selectedDate = new Date().toISOString().split('T')[0];
    let selectedSymbol: string | null = null;
    let activeType: 'forex' | 'crypto' = 'forex';
    
    let rates: Rate[] = [];
    let favorites: Favorite[] = [];
    let history: { date: string; rate: number | null }[] = [];

    let loadingRates = false;
    let loadingHistory = false;
    let currentRange = '30d';
    let currentRangeDays = 30;
    
    // Derived provider
    $: provider = activeType === 'crypto' ? 'fcs' : 'cnb';
    $: year = parseInt(selectedDate.split('-')[0]);

    onMount(async () => {
        await loadFavorites();
        await loadRates();
    });

    async function loadFavorites() {
        try {
            favorites = await getFavorites();
        } catch (e) {
            console.error('Failed to load favorites', e);
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

    async function loadHistory(from?: string, to?: string) {
        if (!selectedSymbol) return;
        loadingHistory = true;

        if (!from || !to) {
            const t = new Date();
            const f = new Date();
            f.setDate(t.getDate() - currentRangeDays);
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
        
        loadRates();
    }

    function handleTypeChange(e: CustomEvent<'forex' | 'crypto'>) {
        activeType = e.detail;
        selectedSymbol = null;
        history = [];
        setTimeout(() => {
            loadRates();
        }, 0);
    }

    function handleSelectSymbol(e: CustomEvent<string>) {
        selectedSymbol = e.detail;
        loadHistory();
    }

    async function handleToggleFavorite(e: CustomEvent<{ provider: string; provider_symbol: string }>) {
        const { provider, provider_symbol } = e.detail;
        try {
            const existing = favorites.find(f => f.provider === provider && f.provider_symbol === provider_symbol);
            if (existing) {
                await removeFavorite(provider, provider_symbol);
                favorites = favorites.filter(f => !(f.provider === provider && f.provider_symbol === provider_symbol));
            } else {
                await addFavorite(provider, provider_symbol);
                favorites = [...favorites, { provider, provider_symbol }];
            }
        } catch (error) {
            console.error('Failed to toggle favorite', error);
        }
    }

    function handleRangeChange(e: CustomEvent<{ from: string, to: string, range: string, days: number }>) {
        currentRange = e.detail.range;
        currentRangeDays = e.detail.days;
        loadHistory(e.detail.from, e.detail.to);
    }
</script>

<div class="bg-slate-950 text-slate-200 p-6 flex flex-col gap-6">
    <header class="mb-4">
        <h1 class="text-3xl font-bold text-white">Rates</h1>
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
                activeRange={currentRange}
                on:rangeChange={handleRangeChange}
            />
        </div>
    </div>
</div>
