<script lang="ts">
  import { contactsApi, relationshipTypesApi } from '$api/contacts';
  import Button from '$components/ui/Button.svelte';
  import { Plus, Trash2, Users } from 'lucide-svelte';
  import type { ContactRelationship, RelationshipType, Contact } from '$lib/types/models';
  import type { PaginatedResponse } from '$lib/types/common';
  import { api } from '$api/client';

  interface Props {
    vaultId: string;
    contactId: string;
  }

  let { vaultId, contactId }: Props = $props();

  let relationships = $state<ContactRelationship[]>([]);
  let relTypes = $state<RelationshipType[]>([]);
  let contactsCache = $state<Record<string, Contact>>({});
  let loading = $state(true);
  let error = $state('');
  let adding = $state(false);
  let form = $state({ other_contact_id: '', relationship_type_id: '' });
  let saving = $state(false);
  let searchResults = $state<Contact[]>([]);
  let searchQuery = $state('');

  $effect(() => {
    Promise.all([
      contactsApi.listRelationships(vaultId, contactId),
      relationshipTypesApi.list(vaultId)
    ]).then(async ([rels, types]) => {
      relationships = rels;
      relTypes = types;
      // Load related contact names
      const ids = [...new Set(rels.map((r) => r.other_contact_id))];
      for (const id of ids) {
        if (!contactsCache[id]) {
          const c = await contactsApi.get(vaultId, id);
          contactsCache[id] = c;
        }
      }
      contactsCache = { ...contactsCache };
      loading = false;
    }).catch(() => {
      error = 'Failed to load relationships';
      loading = false;
    });
  });

  async function searchContacts() {
    if (searchQuery.length < 1) {
      searchResults = [];
      return;
    }
    const r = await api.get<PaginatedResponse<Contact>>(
      `/vaults/${vaultId}/contacts?q=${encodeURIComponent(searchQuery)}&limit=5`
    );
    searchResults = r.items.filter((c) => c.id !== contactId);
  }

  function selectContact(c: Contact) {
    form.other_contact_id = c.id;
    searchQuery = `${c.first_name} ${c.last_name}`.trim();
    searchResults = [];
  }

  async function handleAdd() {
    if (!form.other_contact_id || !form.relationship_type_id) return;
    saving = true;
    try {
      const rel = await contactsApi.createRelationship(vaultId, contactId, {
        other_contact_id: form.other_contact_id,
        relationship_type_id: form.relationship_type_id
      });
      relationships = [...relationships, rel];
      // Cache the new contact
      if (!contactsCache[rel.other_contact_id]) {
        const c = await contactsApi.get(vaultId, rel.other_contact_id);
        contactsCache = { ...contactsCache, [c.id]: c };
      }
      adding = false;
      form = { other_contact_id: '', relationship_type_id: '' };
      searchQuery = '';
    } finally {
      saving = false;
    }
  }

  async function handleDelete(relId: string) {
    await contactsApi.deleteRelationship(vaultId, contactId, relId);
    relationships = relationships.filter((r) => r.id !== relId);
  }

  function getTypeName(typeId: string): string {
    return relTypes.find((t) => t.id === typeId)?.name ?? 'Unknown';
  }

  function getContactName(cId: string): string {
    const c = contactsCache[cId];
    if (!c) return '...';
    return `${c.first_name} ${c.last_name}`.trim();
  }
</script>

<div class="rounded-lg border border-neutral-800 p-4">
  <div class="mb-3 flex items-center justify-between">
    <h3 class="text-xs font-semibold uppercase tracking-wider text-neutral-500">Relationships</h3>
    {#if !adding}
      <button onclick={() => (adding = true)} class="text-neutral-400 hover:text-white">
        <Plus size={16} />
      </button>
    {/if}
  </div>

  {#if error}
    <p class="text-xs text-red-400">{error}</p>
  {:else if loading}
    <p class="text-xs text-neutral-500">Loading...</p>
  {:else if relationships.length === 0 && !adding}
    <p class="text-xs text-neutral-500">No relationships yet</p>
  {:else}
    <div class="space-y-2">
      {#each relationships as rel (rel.id)}
        <div class="group flex items-center gap-2 text-sm">
          <Users size={14} class="shrink-0 text-neutral-500" />
          <span class="text-neutral-200">{getContactName(rel.other_contact_id)}</span>
          <span class="text-xs text-neutral-500">({getTypeName(rel.relationship_type_id)})</span>
          <div class="flex-1"></div>
          <button onclick={() => handleDelete(rel.id)} class="shrink-0 text-neutral-600 opacity-0 transition hover:text-red-400 group-hover:opacity-100">
            <Trash2 size={14} />
          </button>
        </div>
      {/each}
    </div>
  {/if}

  {#if adding}
    <form onsubmit={handleAdd} class="mt-2 space-y-2">
      <div class="relative">
        <input
          bind:value={searchQuery}
          oninput={searchContacts}
          placeholder="Search contact..."
          class="w-full rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none focus:border-brand-500"
        />
        {#if searchResults.length > 0}
          <div class="absolute z-10 mt-1 w-full rounded border border-neutral-700 bg-neutral-800 shadow-lg">
            {#each searchResults as c (c.id)}
              <button
                type="button"
                onclick={() => selectContact(c)}
                class="block w-full px-2 py-1.5 text-left text-xs text-neutral-200 hover:bg-neutral-700"
              >
                {c.first_name} {c.last_name}
              </button>
            {/each}
          </div>
        {/if}
      </div>
      <select bind:value={form.relationship_type_id} class="w-full rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white">
        <option value="">Select type...</option>
        {#each relTypes as rt (rt.id)}
          <option value={rt.id}>{rt.name}</option>
        {/each}
      </select>
      <div class="flex gap-2">
        <Button size="sm" type="submit" loading={saving} disabled={!form.other_contact_id || !form.relationship_type_id}>Add</Button>
        <Button size="sm" variant="ghost" onclick={() => { adding = false; searchQuery = ''; searchResults = []; }}>Cancel</Button>
      </div>
    </form>
  {/if}
</div>
