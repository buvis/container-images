<script lang="ts">
  import type { Component, Snippet } from 'svelte';

  interface Props {
    icon?: Component<{ size?: number }>;
    title: string;
    description?: string;
    action?: Snippet;
  }

  let { icon: Icon, title, description, action }: Props = $props();
</script>

<div class="flex flex-col items-center justify-center py-12 text-center">
  {#if Icon}
    <div class="mb-4 rounded-xl bg-neutral-800 p-4 text-neutral-500">
      <Icon size={32} />
    </div>
  {/if}

  <h3 class="text-lg font-semibold text-neutral-200">{title}</h3>

  {#if description}
    <p class="mt-1 max-w-sm text-sm text-neutral-400">{description}</p>
  {/if}

  {#if action}
    <div class="mt-4">
      {@render action()}
    </div>
  {/if}
</div>
