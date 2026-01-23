<script lang="ts">
    import { createEventDispatcher } from 'svelte';

    export let selectedDate: string = new Date().toISOString().split('T')[0];

    const dispatch = createEventDispatcher();
    
    let currentYear = parseInt(selectedDate.split('-')[0]);
    let currentMonth = parseInt(selectedDate.split('-')[1]) - 1;

    $: daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    $: firstDayOfMonth = new Date(currentYear, currentMonth, 1).getDay();
    $: monthName = new Date(currentYear, currentMonth).toLocaleString('default', { month: 'long' });

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

    function selectDate(day: number) {
        const date = new Date(Date.UTC(currentYear, currentMonth, day));
        selectedDate = date.toISOString().split('T')[0];
        dispatch('change', selectedDate);
    }

    function isSelected(day: number) {
        return selectedDate === new Date(Date.UTC(currentYear, currentMonth, day)).toISOString().split('T')[0];
    }
</script>

<div class="bg-slate-800 p-4 rounded-lg shadow-lg text-slate-200 w-full max-w-sm">
    <div class="flex justify-between items-center mb-4">
        <button on:click={prevMonth} class="p-1 hover:bg-slate-700 rounded">&lt;</button>
        <span class="font-bold">{monthName} {currentYear}</span>
        <button on:click={nextMonth} class="p-1 hover:bg-slate-700 rounded">&gt;</button>
    </div>
    <div class="grid grid-cols-7 gap-1 text-center text-sm">
        {#each ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'] as day}
            <div class="text-slate-400 font-medium py-1">{day}</div>
        {/each}
        {#each Array(firstDayOfMonth) as _}
            <div></div>
        {/each}
        {#each Array(daysInMonth) as _, i}
            <button
                class="p-2 rounded hover:bg-slate-700 {isSelected(i + 1) ? 'bg-blue-600 text-white hover:bg-blue-500' : ''}"
                on:click={() => selectDate(i + 1)}
            >
                {i + 1}
            </button>
        {/each}
    </div>
</div>
