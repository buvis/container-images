<script lang="ts">
  type Tab = { id: string; label: string };

  let { tabs, active, onchange }: { tabs: Tab[]; active: string; onchange: (id: string) => void } = $props();
</script>

<div class="flex gap-1 overflow-x-auto border-b border-neutral-800">
  {#each tabs as tab}
    <button
      onclick={() => onchange(tab.id)}
      class="shrink-0 border-b-2 px-4 py-2 text-sm font-medium transition
        {active === tab.id
          ? 'border-brand-400 text-brand-400'
          : 'border-transparent text-neutral-500 hover:text-neutral-300'}"
    >
      {tab.label}
    </button>
  {/each}
</div>
