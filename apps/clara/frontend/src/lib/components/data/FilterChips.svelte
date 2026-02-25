<script lang="ts">
  interface Chip {
    label: string;
    value: string;
  }

  interface Props {
    chips: Chip[];
    selected: string | null;
    onselect: (value: string | null) => void;
  }

  let { chips, selected, onselect }: Props = $props();

  function toggle(value: string) {
    onselect(selected === value ? null : value);
  }
</script>

<div class="flex flex-wrap gap-2">
  {#each chips as chip}
    <button
      onclick={() => toggle(chip.value)}
      class="rounded-full border px-3 py-1 text-xs font-medium transition
        {selected === chip.value
          ? 'border-brand-500 bg-brand-500/10 text-brand-400'
          : 'border-neutral-700 text-neutral-400 hover:border-neutral-600 hover:text-neutral-300'}"
    >
      {chip.label}
    </button>
  {/each}
</div>
