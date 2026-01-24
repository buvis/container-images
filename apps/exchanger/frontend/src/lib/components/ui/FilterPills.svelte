<script lang="ts">
    // @hmr:reset
    type Option = { name: string; count?: number } | string;

    let {
        options,
        selected = $bindable(new Set<string>())
    }: {
        options: Option[];
        selected: Set<string>;
    } = $props();

    function getName(opt: Option): string {
        return typeof opt === 'string' ? opt : opt.name;
    }

    function getCount(opt: Option): number | undefined {
        return typeof opt === 'string' ? undefined : opt.count;
    }

    function toggle(name: string) {
        if (selected.has(name)) {
            selected.delete(name);
        } else {
            selected.add(name);
        }
        selected = new Set(selected);
    }

    function clear() {
        selected = new Set();
    }

    let totalCount = $derived(options.reduce((sum, opt) => sum + (getCount(opt) ?? 0), 0));
    let hasAnyCounts = $derived(options.some(opt => getCount(opt) !== undefined));
</script>

<div class="flex flex-wrap gap-2">
    <button
        type="button"
        class="px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors {selected.size === 0 ? 'bg-slate-700 border-slate-600 text-white' : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-600'}"
        onclick={clear}
    >
        All
        {#if hasAnyCounts}
            <span class="ml-1 text-xs text-slate-500">({totalCount})</span>
        {/if}
    </button>
    {#each options as opt}
        {@const name = getName(opt)}
        {@const count = getCount(opt)}
        <button
            type="button"
            class="px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors {selected.has(name) ? 'bg-slate-700 border-slate-600 text-white' : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-600'}"
            onclick={() => toggle(name)}
        >
            {name}
            {#if count !== undefined}
                <span class="ml-1 text-xs text-slate-500">({count})</span>
            {/if}
        </button>
    {/each}
</div>
