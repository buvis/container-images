<script lang="ts">
  import { page } from '$app/state';
  import { debtsApi, type DebtCreateInput, type DebtUpdateInput } from '$api/debts';
  import DataList from '$components/data/DataList.svelte';
  import Button from '$components/ui/Button.svelte';
  import Badge from '$components/ui/Badge.svelte';
  import Modal from '$components/ui/Modal.svelte';
  import Input from '$components/ui/Input.svelte';
  import { Plus, DollarSign, Pencil, Trash2 } from 'lucide-svelte';
  import type { Debt } from '$lib/types/models';
  import { lookup } from '$state/lookup.svelte';

  const vaultId = $derived(page.params.vaultId!);

  let showCreate = $state(false);
  let createForm = $state<DebtCreateInput>({ contact_id: '', direction: 'you_owe', amount: 0 });
  let creating = $state(false);
  let dataList: DataList<Debt>;
  let editingDebt = $state<Debt | null>(null);
  let deletingDebt = $state<Debt | null>(null);
  let editForm = $state<DebtUpdateInput>({});
  let saving = $state(false);
  let deleting = $state(false);
  let formError = $state('');

  const filters = [
    { label: 'You Owe', value: 'you_owe' },
    { label: 'Owed to You', value: 'owed_to_you' },
    { label: 'Settled', value: 'settled' }
  ];

  async function loadDebts(params: { offset: number; limit: number; search: string; filter: string | null }) {
    return debtsApi.list(vaultId, {
      search: params.search || undefined,
      direction: params.filter === 'settled' ? undefined : params.filter ?? undefined,
      settled: params.filter === 'settled' ? true : undefined,
      offset: params.offset,
      limit: params.limit
    });
  }

  async function handleCreate(e: SubmitEvent) {
    e.preventDefault();
    if (!createForm.contact_id || createForm.amount <= 0) return;
    formError = '';
    creating = true;
    try {
      await debtsApi.create(vaultId, createForm);
      showCreate = false;
      createForm = { contact_id: '', direction: 'you_owe', amount: 0 };
      dataList.refresh();
    } catch (err) {
      formError = err instanceof Error ? err.message : 'Something went wrong';
    } finally {
      creating = false;
    }
  }

  function startEdit(debt: Debt) {
    editForm = {
      contact_id: debt.contact_id,
      direction: debt.direction,
      amount: debt.amount,
      currency: debt.currency ?? '',
      due_date: debt.due_date ?? '',
      settled: debt.settled,
      notes: debt.notes ?? ''
    };
    editingDebt = debt;
  }

  async function handleEdit(e: SubmitEvent) {
    e.preventDefault();
    if (!editingDebt) return;
    formError = '';
    saving = true;
    try {
      await debtsApi.update(vaultId, editingDebt.id, editForm);
      dataList.refresh();
      editingDebt = null;
    } catch (err) {
      formError = err instanceof Error ? err.message : 'Something went wrong';
    } finally {
      saving = false;
    }
  }

  async function handleDelete() {
    if (!deletingDebt) return;
    deleting = true;
    try {
      await debtsApi.del(vaultId, deletingDebt.id);
      dataList.refresh();
      deletingDebt = null;
    } finally {
      deleting = false;
    }
  }

  async function toggleSettled(debt: Debt) {
    await debtsApi.update(vaultId, debt.id, { settled: !debt.settled });
    dataList.refresh();
  }
</script>

<svelte:head><title>Debts</title></svelte:head>

<div class="space-y-4">
    <DataList
      bind:this={dataList}
      load={loadDebts}
      {filters}
      searchPlaceholder="Search debts..."
      emptyIcon={DollarSign}
      emptyTitle="No debts"
    >
      {#snippet header()}
        <Button onclick={() => (showCreate = true)}><Plus size={16} /> Add Debt</Button>
      {/snippet}
      {#snippet row(item: Debt)}
        <div class="flex items-center gap-3 px-4 py-3">
          <DollarSign size={20} class="shrink-0 text-neutral-400" />
          <div class="min-w-0 flex-1">
            <p class="text-sm font-medium text-white">{item.currency} {item.amount}</p>
            <p class="text-xs text-neutral-500">{lookup.getContactName(item.contact_id)}</p>
            {#if item.notes}<p class="truncate text-xs text-neutral-500">{item.notes}</p>{/if}
          </div>
          <div class="flex items-center gap-2">
            <Badge variant={item.direction === 'you_owe' ? 'danger' : 'success'} text={item.direction === 'you_owe' ? 'You owe' : 'Owed to you'} />
            {#if item.settled}
              <Badge variant="success" text="Settled" />
            {:else}
              <Button variant="ghost" size="sm" onclick={() => toggleSettled(item)}>Settle</Button>
            {/if}
            <button onclick={() => startEdit(item)} class="shrink-0 text-neutral-400 hover:text-neutral-300"><Pencil size={14} /></button>
            <button onclick={() => (deletingDebt = item)} class="shrink-0 text-neutral-400 hover:text-red-400"><Trash2 size={14} /></button>
          </div>
        </div>
      {/snippet}
    </DataList>
</div>

{#if showCreate}
  <Modal title="New Debt" onclose={() => (showCreate = false)}>
    <form onsubmit={handleCreate} class="space-y-4">
      <div>
        <label class="mb-1 block text-sm font-medium text-neutral-300">Direction</label>
        <select bind:value={createForm.direction} class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500">
          <option value="you_owe">You Owe</option>
          <option value="owed_to_you">Owed to You</option>
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
        <Input label="Amount" type="number" step="0.01" min="0.01" bind:value={createForm.amount} required />
        <Input label="Currency" bind:value={createForm.currency} placeholder="USD" />
      </div>
      <Input label="Due date" type="date" bind:value={createForm.due_date} />
      <div>
        <label class="mb-1 block text-sm font-medium text-neutral-300">Notes</label>
        <textarea bind:value={createForm.notes} rows="2" class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500 focus:ring-1 focus:ring-brand-500"></textarea>
      </div>
      {#if formError}<p class="text-sm text-red-400">{formError}</p>{/if}
      <div class="flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (showCreate = false)}>Cancel</Button>
        <Button type="submit" loading={creating}>Create</Button>
      </div>
    </form>
  </Modal>
{/if}

{#if editingDebt}
  <Modal title="Edit Debt" onclose={() => (editingDebt = null)}>
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
          <option value="you_owe">You Owe</option>
          <option value="owed_to_you">Owed to You</option>
        </select>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <Input label="Amount" type="number" step="0.01" min="0.01" bind:value={editForm.amount} required />
        <Input label="Currency" bind:value={editForm.currency} placeholder="USD" />
      </div>
      <Input label="Due date" type="date" bind:value={editForm.due_date} />
      <label class="flex items-center gap-2 text-sm text-neutral-300">
        <input type="checkbox" bind:checked={editForm.settled} class="h-4 w-4 accent-brand-500" />
        Settled
      </label>
      <div>
        <label class="mb-1 block text-sm font-medium text-neutral-300">Notes</label>
        <textarea bind:value={editForm.notes} rows="2" class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500 focus:ring-1 focus:ring-brand-500"></textarea>
      </div>
      {#if formError}<p class="text-sm text-red-400">{formError}</p>{/if}
      <div class="flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (editingDebt = null)}>Cancel</Button>
        <Button type="submit" loading={saving}>Save</Button>
      </div>
    </form>
  </Modal>
{/if}

{#if deletingDebt}
  <Modal title="Delete Debt" onclose={() => (deletingDebt = null)}>
    <p class="text-sm text-neutral-400">Delete this debt? This cannot be undone.</p>
    <div class="mt-4 flex justify-end gap-3">
      <Button variant="ghost" onclick={() => (deletingDebt = null)}>Cancel</Button>
      <Button variant="danger" loading={deleting} onclick={handleDelete}>Delete</Button>
    </div>
  </Modal>
{/if}
