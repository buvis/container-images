<script lang="ts">
    // @hmr:reset
    let {
        value = $bindable(''),
        placeholder = 'Search...',
        debounceMs = 300
    } = $props();

    let inputValue = $state(value);
    let debounceTimer: ReturnType<typeof setTimeout>;
    let lastExternalValue = value;

    // Sync external value changes (e.g., programmatic reset)
    $effect.pre(() => {
        if (value !== lastExternalValue) {
            inputValue = value;
            lastExternalValue = value;
        }
    });

    function handleInput(e: Event) {
        const val = (e.target as HTMLInputElement).value;
        inputValue = val;
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            value = val;
            lastExternalValue = val;
        }, debounceMs);
    }
</script>

<input
    type="text"
    value={inputValue}
    oninput={handleInput}
    {placeholder}
    class="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-slate-500 focus:ring-1 focus:ring-slate-500"
/>
