<script lang="ts">
  import { goto } from '$app/navigation';
  import { vaultsApi } from '$api/vaults';
  import Button from '$components/ui/Button.svelte';
  import Input from '$components/ui/Input.svelte';
  import Modal from '$components/ui/Modal.svelte';
  import Spinner from '$components/ui/Spinner.svelte';
  import { Plus, Pencil, Trash2, Archive } from 'lucide-svelte';
  import type { Vault } from '$lib/types/models';

  let vaults = $state<Vault[]>([]);
  let loading = $state(true);

  let showCreate = $state(false);
  let createName = $state('');
  let creating = $state(false);

  let editId = $state<string | null>(null);
  let editName = $state('');
  let saving = $state(false);

  let deleteId = $state<string | null>(null);
  let deleting = $state(false);

  $effect(() => {
    loadVaults();
  });

  async function loadVaults() {
    loading = true;
    vaults = await vaultsApi.list();
    loading = false;
  }

  async function handleCreate(e: Event) {
    e.preventDefault();
    creating = true;
    try {
      await vaultsApi.create({ name: createName });
      showCreate = false;
      createName = '';
      await loadVaults();
    } finally {
      creating = false;
    }
  }

  function startEdit(v: Vault) {
    editId = v.id;
    editName = v.name;
  }

  async function handleRename(id: string) {
    saving = true;
    try {
      await vaultsApi.rename(id, editName);
      editId = null;
      await loadVaults();
    } finally {
      saving = false;
    }
  }

  async function handleDelete(id: string) {
    deleting = true;
    try {
      await vaultsApi.del(id);
      deleteId = null;
      await loadVaults();
    } finally {
      deleting = false;
    }
  }

  function selectVault(v: Vault) {
    goto(`/vaults/${v.id}/dashboard`);
  }
</script>

<svelte:head><title>Vaults</title></svelte:head>

<div class="mx-auto max-w-2xl space-y-6 p-8">
  <div class="flex items-center justify-between">
    <h1 class="text-2xl font-semibold text-white">Your Vaults</h1>
    <Button onclick={() => (showCreate = true)}>
      <Plus size={16} />
      New Vault
    </Button>
  </div>

  {#if loading}
    <div class="flex justify-center py-12"><Spinner /></div>
  {:else if vaults.length === 0}
    <div class="flex flex-col items-center gap-3 py-16 text-neutral-500">
      <Archive size={40} strokeWidth={1.5} />
      <p class="text-sm">No vaults yet. Create one to get started.</p>
    </div>
  {:else}
    <div class="space-y-2">
      {#each vaults as v (v.id)}
        <div class="group flex items-center gap-4 rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-3 transition hover:border-neutral-700">
          {#if editId === v.id}
            <div class="flex flex-1 items-center gap-2">
              <input
                type="text"
                bind:value={editName}
                onkeydown={(e) => { if (e.key === 'Enter') handleRename(v.id); if (e.key === 'Escape') editId = null; }}
                class="flex-1 rounded border border-brand-500 bg-neutral-800 px-2 py-1 text-sm text-white outline-none"
                autofocus
              />
              <Button size="sm" loading={saving} onclick={() => handleRename(v.id)}>Save</Button>
              <Button size="sm" variant="ghost" onclick={() => (editId = null)}>Cancel</Button>
            </div>
          {:else}
            <button onclick={() => selectVault(v)} class="min-w-0 flex-1 text-left">
              <p class="text-sm font-medium text-white">{v.name}</p>
              <p class="text-xs text-neutral-500">Created {new Date(v.created_at).toLocaleDateString()}</p>
            </button>
            <div class="flex items-center gap-1">
              {#if deleteId === v.id}
                <span class="text-xs text-red-400">Delete vault?</span>
                <Button size="sm" variant="danger" loading={deleting} onclick={() => handleDelete(v.id)}>Yes</Button>
                <Button size="sm" variant="ghost" onclick={() => (deleteId = null)}>No</Button>
              {:else}
                <button onclick={() => startEdit(v)} class="rounded p-1 text-neutral-600 opacity-0 transition hover:text-white group-hover:opacity-100">
                  <Pencil size={14} />
                </button>
                <button onclick={() => (deleteId = v.id)} class="rounded p-1 text-neutral-600 opacity-0 transition hover:text-red-400 group-hover:opacity-100">
                  <Trash2 size={14} />
                </button>
              {/if}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>

{#if showCreate}
  <Modal title="Create Vault" onclose={() => (showCreate = false)}>
    <form onsubmit={handleCreate} class="space-y-4">
      <Input label="Vault name" bind:value={createName} required />
      <div class="flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (showCreate = false)}>Cancel</Button>
        <Button type="submit" loading={creating}>Create</Button>
      </div>
    </form>
  </Modal>
{/if}
