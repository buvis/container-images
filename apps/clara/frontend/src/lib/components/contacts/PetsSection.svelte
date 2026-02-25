<script lang="ts">
  import { contactsApi } from '$api/contacts';
  import Button from '$components/ui/Button.svelte';
  import { Plus, Trash2, PawPrint } from 'lucide-svelte';
  import type { Pet } from '$lib/types/models';

  interface Props {
    vaultId: string;
    contactId: string;
  }

  let { vaultId, contactId }: Props = $props();

  let items = $state<Pet[]>([]);
  let loading = $state(true);
  let error = $state('');
  let adding = $state(false);
  let editId = $state<string | null>(null);
  let form = $state({ name: '', species: '' });
  let saving = $state(false);

  $effect(() => {
    contactsApi.listPets(vaultId, contactId).then((r) => {
      items = r;
      loading = false;
    }).catch(() => {
      error = 'Failed to load pets';
      loading = false;
    });
  });

  async function handleAdd() {
    saving = true;
    try {
      const created = await contactsApi.createPet(vaultId, contactId, form);
      items = [...items, created];
      adding = false;
      form = { name: '', species: '' };
    } finally {
      saving = false;
    }
  }

  function startEdit(p: Pet) {
    editId = p.id;
    form = { name: p.name, species: p.species };
  }

  async function handleUpdate() {
    if (!editId) return;
    saving = true;
    try {
      const updated = await contactsApi.updatePet(vaultId, contactId, editId, form);
      items = items.map((p) => (p.id === editId ? updated : p));
      editId = null;
      form = { name: '', species: '' };
    } finally {
      saving = false;
    }
  }

  async function handleDelete(id: string) {
    await contactsApi.deletePet(vaultId, contactId, id);
    items = items.filter((p) => p.id !== id);
  }
</script>

<div class="rounded-lg border border-neutral-800 p-4">
  <div class="mb-3 flex items-center justify-between">
    <h3 class="text-xs font-semibold uppercase tracking-wider text-neutral-500">Pets</h3>
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
    <p class="text-xs text-neutral-500">No pets yet</p>
  {:else}
    <div class="space-y-2">
      {#each items as item (item.id)}
        {#if editId === item.id}
          <form onsubmit={handleUpdate} class="flex gap-2">
            <input bind:value={form.name} placeholder="Name" required class="min-w-0 flex-1 rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none focus:border-brand-500" />
            <input bind:value={form.species} placeholder="Species" class="w-24 rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none focus:border-brand-500" />
            <Button size="sm" type="submit" loading={saving}>Save</Button>
            <Button size="sm" variant="ghost" onclick={() => (editId = null)}>Cancel</Button>
          </form>
        {:else}
          <div class="group flex items-center gap-2 text-sm">
            <PawPrint size={14} class="shrink-0 text-neutral-500" />
            <button onclick={() => startEdit(item)} class="min-w-0 flex-1 truncate text-left text-neutral-200 hover:text-white">
              {item.name}
            </button>
            {#if item.species}
              <span class="shrink-0 text-xs text-neutral-500">{item.species}</span>
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
    <form onsubmit={handleAdd} class="mt-2 flex gap-2">
      <input bind:value={form.name} placeholder="Name" required class="min-w-0 flex-1 rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none focus:border-brand-500" />
      <input bind:value={form.species} placeholder="Species" class="w-24 rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none focus:border-brand-500" />
      <Button size="sm" type="submit" loading={saving}>Add</Button>
      <Button size="sm" variant="ghost" onclick={() => (adding = false)}>Cancel</Button>
    </form>
  {/if}
</div>
