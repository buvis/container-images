<script lang="ts">
    import { createEventDispatcher } from 'svelte';

    export let selectedDate: string = new Date().toISOString().split('T')[0];

    const dispatch = createEventDispatcher();

    let currentYear = parseInt(selectedDate.split('-')[0]);
    let currentMonth = parseInt(selectedDate.split('-')[1]) - 1;
    let showMonthPicker = false;
    let showYearPicker = false;

    const today = new Date();
    const todayStr = today.toISOString().split('T')[0];
    const thisYear = today.getFullYear();
    const thisMonth = today.getMonth();
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const yearRange = Array.from({ length: 11 }, (_, i) => thisYear - 10 + i);

    $: daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    $: firstDayOfMonth = (new Date(currentYear, currentMonth, 1).getDay() + 6) % 7;
    $: monthName = new Date(currentYear, currentMonth).toLocaleString('default', { month: 'long' });

    // Reactive: rebuild day data when selectedDate or view changes
    $: days = Array.from({ length: daysInMonth }, (_, i) => {
        const day = i + 1;
        const dateStr = new Date(Date.UTC(currentYear, currentMonth, day)).toISOString().split('T')[0];
        return {
            day,
            dateStr,
            isSelected: selectedDate === dateStr,
            isToday: todayStr === dateStr,
            isFuture: dateStr > todayStr
        };
    });

    $: isCurrentMonth = currentYear === thisYear && currentMonth === thisMonth;

    function prevMonth() {
        if (currentMonth === 0) {
            currentMonth = 11;
            currentYear--;
        } else {
            currentMonth--;
        }
    }

    function nextMonth() {
        if (currentMonth === 11) {
            currentMonth = 0;
            currentYear++;
        } else {
            currentMonth++;
        }
    }

    function selectMonth(m: number) {
        currentMonth = m;
        showMonthPicker = false;
    }

    function selectYear(y: number) {
        currentYear = y;
        showYearPicker = false;
    }

    function toggleMonthPicker() {
        showMonthPicker = !showMonthPicker;
        showYearPicker = false;
    }

    function toggleYearPicker() {
        showYearPicker = !showYearPicker;
        showMonthPicker = false;
    }

    function selectDate(dateStr: string) {
        selectedDate = dateStr;
        dispatch('change', selectedDate);
    }

    function goToToday() {
        const today = new Date();
        currentYear = today.getFullYear();
        currentMonth = today.getMonth();
        selectDate(todayStr);
    }

    function closePickers() {
        showMonthPicker = false;
        showYearPicker = false;
    }
</script>

<svelte:window on:click={closePickers} />

<div class="bg-slate-800 p-4 rounded-lg shadow-lg text-slate-200 w-full max-w-sm">
    <div class="flex justify-between items-center mb-4">
        <button on:click={prevMonth} class="p-1 hover:bg-slate-700 rounded cursor-pointer" aria-label="Previous month">&lt;</button>
        <div class="flex gap-1 relative">
            <button
                on:click|stopPropagation={toggleMonthPicker}
                class="font-bold hover:bg-slate-700 px-2 py-0.5 rounded cursor-pointer"
                aria-label="Select month"
            >
                {monthName}
            </button>
            <button
                on:click|stopPropagation={toggleYearPicker}
                class="font-bold hover:bg-slate-700 px-2 py-0.5 rounded cursor-pointer"
                aria-label="Select year"
            >
                {currentYear}
            </button>

            {#if showMonthPicker}
                <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
                <div on:click|stopPropagation class="absolute top-full left-0 mt-1 bg-slate-700 rounded-lg shadow-xl z-20 p-2 grid grid-cols-3 gap-1 w-48">
                    {#each months as m, i}
                        {@const isFutureMonth = currentYear === thisYear && i > thisMonth}
                        <button
                            on:click={() => !isFutureMonth && selectMonth(i)}
                            disabled={isFutureMonth}
                            class="px-2 py-1.5 rounded text-sm transition-colors
                                {isFutureMonth ? 'text-slate-600 cursor-not-allowed' : 'cursor-pointer'}
                                {i === currentMonth ? 'bg-blue-600 text-white' : !isFutureMonth ? 'hover:bg-slate-600' : ''}"
                        >
                            {m}
                        </button>
                    {/each}
                </div>
            {/if}

            {#if showYearPicker}
                <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
                <div on:click|stopPropagation class="absolute top-full right-0 mt-1 bg-slate-700 rounded-lg shadow-xl z-20 p-2 max-h-48 overflow-y-auto w-24">
                    {#each yearRange as y}
                        <button
                            on:click={() => selectYear(y)}
                            class="block w-full text-center px-2 py-1 rounded text-sm cursor-pointer transition-colors
                                {y === currentYear ? 'bg-blue-600 text-white' : 'hover:bg-slate-600'}"
                        >
                            {y}
                        </button>
                    {/each}
                </div>
            {/if}
        </div>
        <button
            on:click={nextMonth}
            disabled={isCurrentMonth}
            class="p-1 rounded {isCurrentMonth ? 'text-slate-600 cursor-not-allowed' : 'hover:bg-slate-700 cursor-pointer'}"
            aria-label="Next month"
        >&gt;</button>
    </div>

    <div class="grid grid-cols-7 gap-1 text-center text-sm">
        {#each ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'] as dayName}
            <div class="text-slate-500 font-medium py-1 text-xs">{dayName}</div>
        {/each}
        {#each Array(firstDayOfMonth) as _}
            <div></div>
        {/each}
        {#each days as d}
            <button
                class="p-2 rounded-lg transition-all relative
                    {d.isFuture ? 'text-slate-600 cursor-not-allowed' : 'cursor-pointer'}
                    {d.isSelected ? 'bg-blue-600 text-white font-semibold scale-105 shadow-md z-10' : !d.isFuture ? 'hover:bg-slate-700' : ''}"
                on:click={() => !d.isFuture && selectDate(d.dateStr)}
                disabled={d.isFuture}
            >
                {d.day}
                {#if d.isToday}
                    <span class="absolute bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full {d.isSelected ? 'bg-white' : 'bg-blue-400'}"></span>
                {/if}
            </button>
        {/each}
    </div>

    <div class="mt-3 pt-3 border-t border-slate-700 flex justify-center">
        <button
            on:click={goToToday}
            class="flex items-center gap-2 text-sm font-medium text-slate-300 bg-slate-700/40 hover:bg-slate-700 hover:text-white px-3 py-1.5 rounded-md border border-slate-600/50 hover:border-slate-500 transition-colors cursor-pointer"
        >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Today
        </button>
    </div>
</div>
