<script lang="ts">
    export let year: number = new Date().getFullYear();
    export let coverage: Record<string, number> = {};
    export let favoritesCount: number = 0;

    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

    $: days = getDaysInYear(year);
    $: maxValue = Math.max(...Object.values(coverage), 1);

    function getDaysInYear(y: number) {
        const d = [];
        const start = new Date(y, 0, 1);
        const end = new Date(y, 11, 31);
        
        // Align start to Sunday for the grid
        const startDay = start.getDay();
        const gridStart = new Date(start);
        gridStart.setDate(start.getDate() - startDay);

        // We need enough weeks to cover the year
        // 53 weeks * 7 days = 371 days
        for (let i = 0; i < 371; i++) {
            const current = new Date(gridStart);
            current.setDate(gridStart.getDate() + i);
            const dateStr = current.toISOString().split('T')[0];
            const inYear = current.getFullYear() === y;
            
            d.push({
                date: dateStr,
                inYear,
                month: current.getMonth(),
                day: current.getDate(),
                value: coverage[dateStr] || 0
            });
        }
        return d;
    }

    function getColor(val: number, inYear: boolean) {
        if (!inYear) return 'bg-transparent';
        if (val === 0) return 'bg-slate-700';
        
        if (favoritesCount > 0) {
            if (val >= favoritesCount) return 'bg-green-500';
            return 'bg-yellow-500';
        }

        // Fallback for when favoritesCount is 0 or not provided
        if (maxValue === 1) return 'bg-green-500';
        
        const ratio = val / maxValue;
        if (ratio < 0.8) return 'bg-yellow-500'; 
        return 'bg-green-500';
    }

    function getTitle(day: any) {
        if (!day.inYear) return '';
        return `${day.date}: ${day.value} rates`;
    }
</script>

<div class="bg-slate-800 rounded-lg shadow-lg p-4 border border-slate-700 overflow-x-auto">
    <div class="flex items-center justify-between mb-2">
        <h3 class="text-slate-200 font-bold text-sm">Data Coverage {year}</h3>
        <div class="flex items-center gap-2 text-xs text-slate-400">
            <span class="flex items-center gap-1"><span class="w-3 h-3 bg-slate-700 rounded-sm"></span> Missing</span>
            <span class="flex items-center gap-1"><span class="w-3 h-3 bg-yellow-500 rounded-sm"></span> Partial</span>
            <span class="flex items-center gap-1"><span class="w-3 h-3 bg-green-500 rounded-sm"></span> Complete</span>
        </div>
    </div>
    
    <div class="flex gap-1">
        <!-- Week columns -->
        {#each Array(53) as _, weekIndex}
            <div class="flex flex-col gap-1">
                {#each Array(7) as _, dayIndex}
                    <!-- svelte-ignore a11y-no-static-element-interactions -->
                    {@const day = days[weekIndex * 7 + dayIndex]}
                    <div 
                        class="w-3 h-3 rounded-sm {getColor(day.value, day.inYear)}"
                        title={getTitle(day)}
                    ></div>
                {/each}
            </div>
        {/each}
    </div>
</div>
