<script lang="ts">
  import { page } from '$app/state';
  import { giftsApi } from '$api/gifts';
  import type { GiftCreateInput, GiftUpdateInput } from '$api/gifts';
  import DataList from '$components/data/DataList.svelte';
  import Button from '$components/ui/Button.svelte';
  import Badge from '$components/ui/Badge.svelte';
  import Modal from '$components/ui/Modal.svelte';
  import Input from '$components/ui/Input.svelte';
  import { Plus, Gift, ExternalLink, Pencil, Trash2 } from 'lucide-svelte';
  import type { Gift as GiftModel } from '$lib/types/models';
  import { lookup } from '$state/lookup.svelte';

  const vaultId = $derived(page.params.vaultId!);

  let showCreate = $state(false);
  let createForm = $state<GiftCreateInput>({ contact_id: '', direction: 'idea', name: '' });
  let creating = $state(false);
  let editingGift = $state<GiftModel | null>(null);
  let deletingGift = $state<GiftModel | null>(null);
  let editForm = $state<GiftUpdateInput>({});
  let saving = $state(false);
  let deleting = $state(false);
  let dataList: DataList<GiftModel>;
  let formError = $state('');

  const filters = [
    { label: 'Given', value: 'given' },
    { label: 'Received', value: 'received' },
    { label: 'Ideas', value: 'idea' }
  ];

  async function loadGifts(params: { offset: number; limit: number; search: string; filter: string | null }) {
    return giftsApi.list(vaultId, {
      search: params.search || undefined,
      direction: params.filter ?? undefined,
      offset: params.offset,
      limit: params.limit
    });
  }

  async function handleCreate(e: SubmitEvent) {
    e.preventDefault();
    if (!createForm.name.trim()) return;
    formError = '';
    creating = true;
    try {
      await giftsApi.create(vaultId, createForm);
      showCreate = false;
      createForm = { contact_id: '', direction: 'idea', name: '' };
      dataList.refresh();
    } catch (err) {
      formError = err instanceof Error ? err.message : 'Something went wrong';
    } finally {
      creating = false;
    }
  }

  function startEdit(gift: GiftModel) {
    editForm = {
      contact_id: gift.contact_id,
      direction: gift.direction,
      name: gift.name,
      description: gift.description,
      amount: gift.amount,
      currency: gift.currency,
      status: gift.status,
      link: gift.link
    };
    editingGift = gift;
  }

  async function handleEdit(e: SubmitEvent) {
    e.preventDefault();
    if (!editingGift) return;
    formError = '';
    saving = true;
    try {
      await giftsApi.update(vaultId, editingGift.id, editForm);
      dataList.refresh();
      editingGift = null;
    } catch (err) {
      formError = err instanceof Error ? err.message : 'Something went wrong';
    } finally {
      saving = false;
    }
  }

  async function handleDelete() {
    if (!deletingGift) return;
    deleting = true;
    try {
      await giftsApi.del(vaultId, deletingGift.id);
      dataList.refresh();
      deletingGift = null;
    } finally {
      deleting = false;
    }
  }
</script>

<svelte:head><title>Gifts</title></svelte:head>

<div class="space-y-4">
    <DataList
      bind:this={dataList}
      load={loadGifts}
      {filters}
      searchPlaceholder="Search gifts..."
      emptyIcon={Gift}
      emptyTitle="No gifts yet"
    >
      {#snippet header()}
        <Button onclick={() => (showCreate = true)}><Plus size={16} /> Add Gift</Button>
      {/snippet}
      {#snippet row(item: GiftModel)}
        <div class="flex items-center gap-3 px-4 py-3">
          <Gift size={20} class="shrink-0 text-neutral-400" />
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <p class="truncate text-sm font-medium text-white">{item.name}</p>
              {#if item.link}
                <a href={item.link} target="_blank" rel="noopener noreferrer" class="text-brand-400 hover:text-brand-300"><ExternalLink size={12} /></a>
              {/if}
            </div>
            {#if item.description}<p class="truncate text-xs text-neutral-500">{item.description}</p>{/if}
          </div>
          <div class="flex items-center gap-2">
            {#if item.amount}<span class="text-sm font-medium text-neutral-300">{item.currency} {item.amount}</span>{/if}
            <Badge variant={item.direction === 'given' ? 'success' : 'default'} text={item.direction} />
            <button onclick={() => startEdit(item)} class="shrink-0 text-neutral-400 hover:text-neutral-300"><Pencil size={14} /></button>
            <button onclick={() => (deletingGift = item)} class="shrink-0 text-neutral-400 hover:text-red-400"><Trash2 size={14} /></button>
          </div>
        </div>
      {/snippet}
    </DataList>
</div>

{#if showCreate}
  <Modal title="New Gift" onclose={() => (showCreate = false)}>
    <form onsubmit={handleCreate} class="space-y-4">
      <Input label="Name" bind:value={createForm.name} required />
      <div>
        <label class="mb-1 block text-sm font-medium text-neutral-300">Direction</label>
        <select bind:value={createForm.direction} class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500">
          <option value="idea">Idea</option>
          <option value="given">Given</option>
          <option value="received">Received</option>
        </select>
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-neutral-300">Contact</label>
        <select bind:value={createForm.contact_id} required class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500">
          <option value="">Select contact...</option>
          {#each lookup.contacts as c}
            <option value={c.id}>{c.name}</option>
          {/each}
        </select>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <Input label="Amount" type="number" step="0.01" bind:value={createForm.amount} />
        <Input label="Currency" bind:value={createForm.currency} placeholder="USD" />
      </div>
      <Input label="Link" bind:value={createForm.link} placeholder="https://" />
      {#if formError}<p class="text-sm text-red-400">{formError}</p>{/if}
      <div class="flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (showCreate = false)}>Cancel</Button>
        <Button type="submit" loading={creating}>Create</Button>
      </div>
    </form>
  </Modal>
{/if}

{#if editingGift}
  <Modal title="Edit Gift" onclose={() => (editingGift = null)}>
    <form onsubmit={handleEdit} class="space-y-4">
      <div>
        <label class="mb-1 block text-sm font-medium text-neutral-300">Contact</label>
        <select bind:value={editForm.contact_id} required class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500">
          <option value="">Select contact...</option>
          {#each lookup.contacts as c}
            <option value={c.id}>{c.name}</option>
          {/each}
        </select>
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-neutral-300">Direction</label>
        <select bind:value={editForm.direction} class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500">
          <option value="idea">Idea</option>
          <option value="given">Given</option>
          <option value="received">Received</option>
        </select>
      </div>
      <Input label="Name" bind:value={editForm.name} required />
      <div>
        <label class="mb-1 block text-sm font-medium text-neutral-300">Description</label>
        <textarea bind:value={editForm.description} rows="3" class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500 focus:ring-1 focus:ring-brand-500"></textarea>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <Input label="Amount" type="number" step="0.01" bind:value={editForm.amount} />
        <Input label="Currency" bind:value={editForm.currency} placeholder="USD" />
      </div>
      <Input label="Status" bind:value={editForm.status} />
      <Input label="Link" bind:value={editForm.link} placeholder="https://" />
      {#if formError}<p class="text-sm text-red-400">{formError}</p>{/if}
      <div class="flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (editingGift = null)}>Cancel</Button>
        <Button type="submit" loading={saving}>Save</Button>
      </div>
    </form>
  </Modal>
{/if}

{#if deletingGift}
  <Modal title="Delete Gift" onclose={() => (deletingGift = null)}>
    <p class="text-sm text-neutral-400">Delete <strong>{deletingGift.name}</strong>? This cannot be undone.</p>
    <div class="mt-4 flex justify-end gap-3">
      <Button variant="ghost" onclick={() => (deletingGift = null)}>Cancel</Button>
      <Button variant="danger" loading={deleting} onclick={handleDelete}>Delete</Button>
    </div>
  </Modal>
{/if}
