<script lang="ts">
  import { page } from '$app/state';
  import { remindersApi } from '$api/reminders';
  import type { ReminderCreateInput, ReminderUpdateInput } from '$api/reminders';
  import DataList from '$components/data/DataList.svelte';
  import Button from '$components/ui/Button.svelte';
  import Badge from '$components/ui/Badge.svelte';
  import Modal from '$components/ui/Modal.svelte';
  import Input from '$components/ui/Input.svelte';
  import { Plus, Bell, BellOff, Pencil, Trash2 } from 'lucide-svelte';
  import type { Reminder } from '$lib/types/models';
  import { lookup } from '$state/lookup.svelte';

  const vaultId = $derived(page.params.vaultId!);

  let showCreate = $state(false);
  let createForm = $state<ReminderCreateInput>({
    title: '',
    next_expected_date: new Date().toISOString().split('T')[0],
    frequency_type: 'one_time',
    frequency_number: 1
  });
  let creating = $state(false);
  let dataList: DataList<Reminder>;
  let editingReminder = $state<Reminder | null>(null);
  let deletingReminder = $state<Reminder | null>(null);
  let editForm = $state<ReminderUpdateInput>({});
  let saving = $state(false);
  let deleting = $state(false);
  let formError = $state('');

  const filters = [
    { label: 'Active', value: 'active' },
    { label: 'Completed', value: 'completed' }
  ];

  $effect(() => {
    lookup.loadContacts(vaultId);
  });

  async function loadReminders(params: { offset: number; limit: number; search: string; filter: string | null }) {
    return remindersApi.list(vaultId, {
      search: params.search || undefined,
      status: params.filter ?? undefined,
      offset: params.offset,
      limit: params.limit
    });
  }

  async function handleCreate(e: SubmitEvent) {
    e.preventDefault();
    if (!createForm.title.trim()) return;
    formError = '';
    creating = true;
    try {
      await remindersApi.create(vaultId, createForm);
      showCreate = false;
      createForm = { title: '', next_expected_date: new Date().toISOString().split('T')[0], frequency_type: 'one_time', frequency_number: 1 };
      dataList.refresh();
    } catch (err) {
      formError = err instanceof Error ? err.message : 'Something went wrong';
    } finally {
      creating = false;
    }
  }

  async function markCompleted(reminder: Reminder) {
    await remindersApi.update(vaultId, reminder.id, { status: 'completed' });
    dataList.refresh();
  }

  function startEdit(reminder: Reminder) {
    editForm = {
      contact_id: reminder.contact_id ?? '',
      title: reminder.title,
      description: reminder.description,
      next_expected_date: reminder.next_expected_date,
      frequency_type: reminder.frequency_type,
      frequency_number: reminder.frequency_number,
      status: reminder.status
    };
    editingReminder = reminder;
  }

  async function handleEdit(e: SubmitEvent) {
    e.preventDefault();
    if (!editingReminder) return;
    formError = '';
    saving = true;
    try {
      await remindersApi.update(vaultId, editingReminder.id, editForm);
      dataList.refresh();
      editingReminder = null;
    } catch (err) {
      formError = err instanceof Error ? err.message : 'Something went wrong';
    } finally {
      saving = false;
    }
  }

  async function handleDelete() {
    if (!deletingReminder) return;
    deleting = true;
    try {
      await remindersApi.del(vaultId, deletingReminder.id);
      dataList.refresh();
      deletingReminder = null;
    } finally {
      deleting = false;
    }
  }

  function formatDate(d: string): string {
    return new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  }

  function isOverdue(d: string): boolean {
    return new Date(d) < new Date(new Date().toDateString());
  }

  const frequencyLabels: Record<string, string> = { one_time: 'Once', week: 'Weekly', month: 'Monthly', year: 'Yearly' };
</script>

<svelte:head><title>Reminders</title></svelte:head>

<div class="space-y-4">
    <DataList
      bind:this={dataList}
      load={loadReminders}
      {filters}
      searchPlaceholder="Search reminders..."
      emptyIcon={Bell}
      emptyTitle="No reminders"
    >
      {#snippet header()}
        <Button onclick={() => (showCreate = true)}><Plus size={16} /> Add Reminder</Button>
      {/snippet}
      {#snippet row(item: Reminder)}
        <div class="flex items-center gap-3 px-4 py-3">
          <div class="shrink-0 {item.status === 'completed' ? 'text-neutral-400' : isOverdue(item.next_expected_date) ? 'text-red-400' : 'text-brand-400'}">
            {#if item.status === 'completed'}<BellOff size={20} />{:else}<Bell size={20} />{/if}
          </div>
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-medium {item.status === 'completed' ? 'text-neutral-400 line-through' : 'text-white'}">{item.title}</p>
            {#if item.description}<p class="truncate text-xs text-neutral-500">{item.description}</p>{/if}
          </div>
          <div class="flex items-center gap-2">
            {#if item.frequency_type !== 'one_time'}
              <Badge text={frequencyLabels[item.frequency_type] ?? item.frequency_type} />
            {/if}
            <span class="text-xs {isOverdue(item.next_expected_date) && item.status !== 'completed' ? 'font-medium text-red-400' : 'text-neutral-500'}">
              {formatDate(item.next_expected_date)}
            </span>
            {#if item.status === 'active'}
              <Button variant="ghost" size="sm" onclick={() => markCompleted(item)}>Done</Button>
            {/if}
            <button onclick={() => startEdit(item)} class="shrink-0 text-neutral-400 hover:text-neutral-300"><Pencil size={14} /></button>
            <button onclick={() => (deletingReminder = item)} class="shrink-0 text-neutral-400 hover:text-red-400"><Trash2 size={14} /></button>
          </div>
        </div>
      {/snippet}
    </DataList>
</div>

{#if showCreate}
  <Modal title="New Reminder" onclose={() => (showCreate = false)}>
    <form onsubmit={handleCreate} class="space-y-4">
      <Input label="Title" bind:value={createForm.title} required />
      <div>
        <label class="mb-1 block text-sm font-medium text-neutral-300">Description</label>
        <textarea bind:value={createForm.description} rows="2" class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500 focus:ring-1 focus:ring-brand-500"></textarea>
      </div>
      <Input label="Date" type="date" bind:value={createForm.next_expected_date} required />
      <div>
        <label class="mb-1 block text-sm font-medium text-neutral-300">Frequency</label>
        <select bind:value={createForm.frequency_type} class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500">
          <option value="one_time">One time</option>
          <option value="week">Every X weeks</option>
          <option value="month">Every X months</option>
          <option value="year">Every X years</option>
        </select>
      </div>
      {#if createForm.frequency_type !== 'one_time'}
        <Input label="Every" type="number" min="1" bind:value={createForm.frequency_number} />
      {/if}
      {#if formError}<p class="text-sm text-red-400">{formError}</p>{/if}
      <div class="flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (showCreate = false)}>Cancel</Button>
        <Button type="submit" loading={creating}>Create</Button>
      </div>
    </form>
  </Modal>
{/if}

{#if editingReminder}
  <Modal title="Edit Reminder" onclose={() => (editingReminder = null)}>
    <form onsubmit={handleEdit} class="space-y-4">
      <div>
        <label class="mb-1 block text-sm font-medium text-neutral-300">Contact</label>
        <select bind:value={editForm.contact_id} class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500">
          <option value="">No contact</option>
          {#each lookup.contacts as contact}
            <option value={contact.id}>{contact.name}</option>
          {/each}
        </select>
      </div>
      <Input label="Title" bind:value={editForm.title} required />
      <div>
        <label class="mb-1 block text-sm font-medium text-neutral-300">Description</label>
        <textarea bind:value={editForm.description} rows="2" class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500 focus:ring-1 focus:ring-brand-500"></textarea>
      </div>
      <Input label="Date" type="date" bind:value={editForm.next_expected_date} required />
      <div>
        <label class="mb-1 block text-sm font-medium text-neutral-300">Frequency</label>
        <select bind:value={editForm.frequency_type} class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500">
          <option value="one_time">One time</option>
          <option value="week">Every X weeks</option>
          <option value="month">Every X months</option>
          <option value="year">Every X years</option>
        </select>
      </div>
      {#if editForm.frequency_type !== 'one_time'}
        <Input label="Every" type="number" min="1" bind:value={editForm.frequency_number} />
      {/if}
      <div>
        <label class="mb-1 block text-sm font-medium text-neutral-300">Status</label>
        <select bind:value={editForm.status} class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500">
          <option value="active">Active</option>
          <option value="completed">Completed</option>
        </select>
      </div>
      {#if formError}<p class="text-sm text-red-400">{formError}</p>{/if}
      <div class="flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (editingReminder = null)}>Cancel</Button>
        <Button type="submit" loading={saving}>Save</Button>
      </div>
    </form>
  </Modal>
{/if}

{#if deletingReminder}
  <Modal title="Delete Reminder" onclose={() => (deletingReminder = null)}>
    <p class="text-sm text-neutral-400">Delete this reminder? This cannot be undone.</p>
    <div class="mt-4 flex justify-end gap-3">
      <Button variant="ghost" onclick={() => (deletingReminder = null)}>Cancel</Button>
      <Button variant="danger" loading={deleting} onclick={handleDelete}>Delete</Button>
    </div>
  </Modal>
{/if}
