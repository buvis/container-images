<script lang="ts">
    import { fade } from 'svelte/transition';

    export let coverage: Record<string, number> = {};
    export let favoritesCount: number = 0;
    export let missingSymbols: Record<string, string[]> = {};

    let hoveredDay: { date: string, value: number, missing: string[] } | null = null;
    let mouseX = 0;
    let mouseY = 0;
    let innerWidth = 0;
    let innerHeight = 0;

    const TOOLTIP_WIDTH = 200;
    const TOOLTIP_OFFSET = 15;

    $: tooltipX = (mouseX + TOOLTIP_WIDTH + TOOLTIP_OFFSET > innerWidth)
        ? mouseX - TOOLTIP_WIDTH - TOOLTIP_OFFSET
        : mouseX + TOOLTIP_OFFSET;

    $: tooltipY = Math.max(0, (mouseY + 200 > innerHeight)
        ? mouseY - 10
        : mouseY + TOOLTIP_OFFSET);

    $: maxValue = Math.max(...Object.values(coverage), 1);
    $: days = getPast365Days(coverage);

    function isComplete(val: number): boolean {
        if (val === 0) return false;
        if (favoritesCount > 0) return val >= favoritesCount;
        if (maxValue === 1) return true;
        return val / maxValue >= 0.8;
    }

    function getPast365Days(data: Record<string, number>) {
        const d = [];
        const today = new Date();
        const start = new Date(today);
        start.setDate(today.getDate() - 365);

        const startDay = start.getDay();
        const gridStart = new Date(start);
        gridStart.setDate(start.getDate() - startDay);

        for (let i = 0; i < 371; i++) {
            const current = new Date(gridStart);
            current.setDate(gridStart.getDate() + i);

            const offset = current.getTimezoneOffset() * 60000;
            const localDate = new Date(current.getTime() - offset);
            const dateStr = localDate.toISOString().split('T')[0];

            d.push({
                date: dateStr,
                month: current.getMonth(),
                day: current.getDate(),
                value: data[dateStr] || 0
            });
        }
        return d;
    }

    function getColor(val: number) {
        if (val === 0) return 'bg-slate-700';

        if (favoritesCount > 0) {
            if (val >= favoritesCount) return 'bg-green-500';
            return 'bg-yellow-500';
        }

        if (maxValue === 1) return 'bg-green-500';

        const ratio = val / maxValue;
        if (ratio < 0.8) return 'bg-yellow-500';
        return 'bg-green-500';
    }

    function handleMouseEnter(e: MouseEvent, day: { date: string, value: number }) {
        hoveredDay = { ...day, missing: missingSymbols[day.date] || [] };
        mouseX = e.clientX;
        mouseY = e.clientY;
    }

    function handleMouseMove(e: MouseEvent) {
        mouseX = e.clientX;
        mouseY = e.clientY;
    }

    function handleMouseLeave() {
        hoveredDay = null;
    }
</script>

<svelte:window bind:innerWidth bind:innerHeight />

<div class="bg-slate-800 rounded-lg shadow-lg p-4 border border-slate-700 overflow-x-auto">
    <div class="flex items-center justify-between mb-2">
        <h3 class="text-slate-200 font-bold text-sm">Data Coverage</h3>
        <div class="flex items-center gap-2 text-xs text-slate-400">
            <span class="flex items-center gap-1"><span class="w-3 h-3 bg-slate-700 rounded-sm"></span> Missing</span>
            <span class="flex items-center gap-1"><span class="w-3 h-3 bg-yellow-500 rounded-sm"></span> Partial</span>
            <span class="flex items-center gap-1"><span class="w-3 h-3 bg-green-500 rounded-sm"></span> Complete</span>
        </div>
    </div>

    <div class="flex gap-1">
        {#each Array(53) as _, weekIndex}
            <div class="flex flex-col gap-1">
                {#each Array(7) as _, dayIndex}
                    {@const day = days[weekIndex * 7 + dayIndex]}
                    <div
                        class="w-3 h-3 rounded-sm {getColor(day.value)} hover:ring-1 hover:ring-white transition-all duration-75 cursor-default"
                        on:mouseenter={(e) => handleMouseEnter(e, day)}
                        on:mousemove={handleMouseMove}
                        on:mouseleave={handleMouseLeave}
                        role="img"
                        aria-label="{day.date}: {day.value} rates"
                    ></div>
                {/each}
            </div>
        {/each}
    </div>
</div>

{#if hoveredDay}
    <div
        class="fixed z-50 w-[200px] bg-slate-900 border border-slate-600 rounded-md shadow-2xl pointer-events-none text-xs text-slate-200 flex flex-col overflow-hidden"
        style="top: {tooltipY}px; left: {tooltipX}px;"
        transition:fade={{ duration: 150 }}
    >
        <div class="bg-slate-800 p-2 border-b border-slate-700 flex justify-between items-center">
            <span class="font-bold text-slate-100">{hoveredDay.date}</span>
            <span class="font-mono text-slate-400">{hoveredDay.value}</span>
        </div>
        <div class="p-2 bg-slate-900/95 backdrop-blur-sm">
            {#if hoveredDay.missing.length > 0}
                <div class="flex items-center justify-between mb-1.5">
                    <span class="text-red-400 font-medium">Missing</span>
                    <span class="bg-slate-800 text-slate-400 px-1 rounded text-[10px]">{hoveredDay.missing.length}</span>
                </div>
                <div class="flex flex-wrap gap-1 max-h-32 overflow-y-auto pr-1">
                    {#each hoveredDay.missing as sym}
                        <span class="px-1.5 py-0.5 bg-red-500/10 text-red-300 rounded border border-red-500/20 text-[10px] font-mono">{sym}</span>
                    {/each}
                </div>
            {:else if isComplete(hoveredDay.value)}
                <div class="text-emerald-400 flex items-center gap-1.5 py-1">
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                    <span>All symbols present</span>
                </div>
            {:else if hoveredDay.value === 0}
                <span class="text-slate-400">No data</span>
            {:else}
                <span class="text-yellow-400">{hoveredDay.value}/{favoritesCount > 0 ? favoritesCount : maxValue} symbols</span>
            {/if}
        </div>
    </div>
{/if}
