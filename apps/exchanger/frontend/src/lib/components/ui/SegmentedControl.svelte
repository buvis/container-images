<script lang="ts">
    // @hmr:reset
    type Option = { label: string; value: string } | string;

    let {
        options,
        value = $bindable('')
    }: {
        options: Option[];
        value: string;
    } = $props();

    function getLabel(opt: Option): string {
        return typeof opt === 'string' ? opt.charAt(0).toUpperCase() + opt.slice(1) : opt.label;
    }

    function getValue(opt: Option): string {
        return typeof opt === 'string' ? opt : opt.value;
    }
</script>

<div class="flex bg-slate-900 rounded-lg p-1 border border-slate-700">
    {#each options as opt}
        {@const optValue = getValue(opt)}
        <button
            type="button"
            class="px-4 py-1.5 text-sm font-medium rounded transition-colors {value === optValue ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-slate-200'}"
            onclick={() => value = optValue}
        >
            {getLabel(opt)}
        </button>
    {/each}
</div>
