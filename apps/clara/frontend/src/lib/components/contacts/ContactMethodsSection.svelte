<script lang="ts">
  import { contactsApi } from '$api/contacts';
  import Button from '$components/ui/Button.svelte';
  import { Plus, Trash2, Phone, Mail, Globe } from 'lucide-svelte';
  import type { ContactMethod } from '$lib/types/models';

  interface Props {
    vaultId: string;
    contactId: string;
  }

  let { vaultId, contactId }: Props = $props();

  let items = $state<ContactMethod[]>([]);
  let loading = $state(true);
  let error = $state('');
  let adding = $state(false);
  let editId = $state<string | null>(null);
  let form = $state({ type: 'phone', value: '', label: '' });
  let saving = $state(false);

  $effect(() => {
    contactsApi.listMethods(vaultId, contactId).then((r) => {
      items = r;
      loading = false;
    }).catch(() => {
      error = 'Failed to load contact methods';
      loading = false;
    });
  });

  async function handleAdd() {
    saving = true;
    try {
      const created = await contactsApi.createMethod(vaultId, contactId, form);
      items = [...items, created];
      adding = false;
      form = { type: 'phone', value: '', label: '' };
    } finally {
      saving = false;
    }
  }

  function startEdit(m: ContactMethod) {
    editId = m.id;
    form = { type: m.type, value: m.value, label: m.label };
  }

  async function handleUpdate() {
    if (!editId) return;
    saving = true;
    try {
      const updated = await contactsApi.updateMethod(vaultId, contactId, editId, form);
      items = items.map((m) => (m.id === editId ? updated : m));
      editId = null;
      form = { type: 'phone', value: '', label: '' };
    } finally {
      saving = false;
    }
  }

  async function handleDelete(id: string) {
    await contactsApi.deleteMethod(vaultId, contactId, id);
    items = items.filter((m) => m.id !== id);
  }

  function typeIcon(type: string) {
    if (type === 'email') return Mail;
    if (type === 'phone') return Phone;
    return Globe;
  }
</script>

<div class="rounded-lg border border-neutral-800 p-4">
  <div class="mb-3 flex items-center justify-between">
    <h3 class="text-xs font-semibold uppercase tracking-wider text-neutral-500">Contact Methods</h3>
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
    <p class="text-xs text-neutral-500">No contact methods yet</p>
  {:else}
    <div class="space-y-2">
      {#each items as item (item.id)}
        {#if editId === item.id}
          <form onsubmit={handleUpdate} class="flex gap-2">
            <select bind:value={form.type} class="rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white">
              <option value="phone">Phone</option>
              <option value="email">Email</option>
              <option value="other">Other</option>
            </select>
            <input bind:value={form.value} placeholder="Value" required class="min-w-0 flex-1 rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none focus:border-brand-500" />
            <input bind:value={form.label} placeholder="Label" class="w-20 rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none focus:border-brand-500" />
            <Button size="sm" type="submit" loading={saving}>Save</Button>
            <Button size="sm" variant="ghost" onclick={() => (editId = null)}>Cancel</Button>
          </form>
        {:else}
          {@const Icon = typeIcon(item.type)}
          <div class="group flex items-center gap-2 text-sm">
            <Icon size={14} class="shrink-0 text-neutral-500" />
            <button onclick={() => startEdit(item)} class="min-w-0 flex-1 truncate text-left text-neutral-200 hover:text-white">
              {item.value}
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
    <form onsubmit={handleAdd} class="mt-2 flex gap-2">
      <select bind:value={form.type} class="rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white">
        <option value="phone">Phone</option>
        <option value="email">Email</option>
        <option value="other">Other</option>
      </select>
      <input bind:value={form.value} placeholder="Value" required class="min-w-0 flex-1 rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none focus:border-brand-500" />
      <input bind:value={form.label} placeholder="Label" class="w-20 rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none focus:border-brand-500" />
      <Button size="sm" type="submit" loading={saving}>Add</Button>
      <Button size="sm" variant="ghost" onclick={() => (adding = false)}>Cancel</Button>
    </form>
  {/if}
</div>
