<script lang="ts">
  import { Star } from 'lucide-svelte';
  import type { Contact } from '$lib/types/models';

  let { contact, href }: { contact: Contact; href: string } = $props();

  const initials = $derived(
    `${contact.first_name[0] ?? ''}${contact.last_name?.[0] ?? ''}`.toUpperCase()
  );
</script>

<a
  {href}
  class="flex items-center gap-4 px-4 py-3 transition hover:bg-neutral-800/50"
>
  {#if contact.photo_file_id}
    <img
      src="/api/v1/vaults/{contact.vault_id}/files/{contact.photo_file_id}/download"
      alt="{contact.first_name}"
      class="h-10 w-10 shrink-0 rounded-full object-cover"
    />
  {:else}
    <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-500/20 text-sm font-semibold text-brand-400">
      {initials}
    </div>
  {/if}

  <div class="min-w-0 flex-1">
    <div class="flex items-center gap-2">
      <span class="truncate font-medium text-white">
        {contact.first_name} {contact.last_name}
      </span>
      {#if contact.favorite}
        <Star size={16} class="fill-amber-400 text-amber-400" />
      {/if}
    </div>
    {#if contact.nickname}
      <p class="truncate text-sm text-neutral-500">"{contact.nickname}"</p>
    {/if}
  </div>
</a>
