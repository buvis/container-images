<script lang="ts">
  import { contactsApi } from '$api/contacts';
  import Button from '$components/ui/Button.svelte';
  import { Plus, Trash2, MapPin } from 'lucide-svelte';
  import type { Address } from '$lib/types/models';

  interface Props {
    vaultId: string;
    contactId: string;
  }

  let { vaultId, contactId }: Props = $props();

  let items = $state<Address[]>([]);
  let loading = $state(true);
  let error = $state('');
  let adding = $state(false);
  let editId = $state<string | null>(null);
  let form = $state({ label: '', line1: '', city: '', postal_code: '', country: '' });
  let saving = $state(false);

  $effect(() => {
    contactsApi.listAddresses(vaultId, contactId).then((r) => {
      items = r;
      loading = false;
    }).catch(() => {
      error = 'Failed to load addresses';
      loading = false;
    });
  });

  function resetForm() {
    form = { label: '', line1: '', city: '', postal_code: '', country: '' };
  }

  async function handleAdd() {
    saving = true;
    try {
      const created = await contactsApi.createAddress(vaultId, contactId, form);
      items = [...items, created];
      adding = false;
      resetForm();
    } finally {
      saving = false;
    }
  }

  function startEdit(a: Address) {
    editId = a.id;
    form = { label: a.label, line1: a.line1, city: a.city, postal_code: a.postal_code, country: a.country };
  }

  async function handleUpdate() {
    if (!editId) return;
    saving = true;
    try {
      const updated = await contactsApi.updateAddress(vaultId, contactId, editId, form);
      items = items.map((a) => (a.id === editId ? updated : a));
      editId = null;
      resetForm();
    } finally {
      saving = false;
    }
  }

  async function handleDelete(id: string) {
    await contactsApi.deleteAddress(vaultId, contactId, id);
    items = items.filter((a) => a.id !== id);
  }

  function formatAddress(a: Address): string {
    return [a.line1, a.city, a.postal_code, a.country].filter(Boolean).join(', ');
  }
</script>

<div class="rounded-lg border border-neutral-800 p-4">
  <div class="mb-3 flex items-center justify-between">
    <h3 class="text-xs font-semibold uppercase tracking-wider text-neutral-500">Addresses</h3>
    {#if !adding && !editId}
      <button onclick={() => (adding = true)} class="text-neutral-400 hover:text-white">
        <Plus size={16} />
      </button>
    {/if}
  </div>

  {#if error}
    <p class="text-xs text-red-400">{error}</p>
  {:else if loading}
    <p class="text-xs text-neutral-500">Loading...</p>
  {:else if items.length === 0 && !adding}
    <p class="text-xs text-neutral-500">No addresses yet</p>
  {:else}
    <div class="space-y-2">
      {#each items as item (item.id)}
        {#if editId === item.id}
          <form onsubmit={handleUpdate} class="space-y-2">
            <div class="grid grid-cols-2 gap-2">
              <input bind:value={form.label} placeholder="Label (Home, Work...)" class="rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none focus:border-brand-500" />
              <input bind:value={form.line1} placeholder="Street address" class="rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none focus:border-brand-500" />
              <input bind:value={form.city} placeholder="City" class="rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none focus:border-brand-500" />
              <input bind:value={form.postal_code} placeholder="Postal code" class="rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none focus:border-brand-500" />
              <input bind:value={form.country} placeholder="Country" class="rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none focus:border-brand-500" />
            </div>
            <div class="flex gap-2">
              <Button size="sm" type="submit" loading={saving}>Save</Button>
              <Button size="sm" variant="ghost" onclick={() => (editId = null)}>Cancel</Button>
            </div>
          </form>
        {:else}
          <div class="group flex items-center gap-2 text-sm">
            <MapPin size={14} class="shrink-0 text-neutral-500" />
            <button onclick={() => startEdit(item)} class="min-w-0 flex-1 truncate text-left text-neutral-200 hover:text-white">
              {formatAddress(item)}
            </button>
            {#if item.label}
              <span class="shrink-0 text-xs text-neutral-500">{item.label}</span>
            {/if}
            <button onclick={() => handleDelete(item.id)} class="shrink-0 text-neutral-600 opacity-0 transition hover:text-red-400 group-hover:opacity-100">
              <Trash2 size={14} />
            </button>
          </div>
        {/if}
      {/each}
    </div>
  {/if}

  {#if adding}
    <form onsubmit={handleAdd} class="mt-2 space-y-2">
      <div class="grid grid-cols-2 gap-2">
        <input bind:value={form.label} placeholder="Label (Home, Work...)" class="rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none focus:border-brand-500" />
        <input bind:value={form.line1} placeholder="Street address" class="rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none focus:border-brand-500" />
        <input bind:value={form.city} placeholder="City" class="rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none focus:border-brand-500" />
        <input bind:value={form.postal_code} placeholder="Postal code" class="rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none focus:border-brand-500" />
        <input bind:value={form.country} placeholder="Country" class="rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none focus:border-brand-500" />
      </div>
      <div class="flex gap-2">
        <Button size="sm" type="submit" loading={saving}>Add</Button>
        <Button size="sm" variant="ghost" onclick={() => (adding = false)}>Cancel</Button>
      </div>
    </form>
  {/if}
</div>
