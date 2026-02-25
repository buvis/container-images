<script lang="ts">
  import { page } from '$app/state';
  import { tasksApi, type TaskCreateInput, type TaskUpdateInput } from '$api/tasks';
  import DataList from '$components/data/DataList.svelte';
  import Button from '$components/ui/Button.svelte';
  import Badge from '$components/ui/Badge.svelte';
  import Modal from '$components/ui/Modal.svelte';
  import Input from '$components/ui/Input.svelte';
  import Textarea from '$components/ui/Textarea.svelte';
  import Select from '$components/ui/Select.svelte';
  import { Plus, CheckCircle, Circle, CheckSquare, Pencil, Trash2 } from 'lucide-svelte';
  import type { Task } from '$lib/types/models';
  import { lookup } from '$state/lookup.svelte';

  const vaultId = $derived(page.params.vaultId!);

  let showCreate = $state(false);
  let createForm = $state<TaskCreateInput>({ title: '' });
  let creating = $state(false);
  let dataList: DataList<Task>;
  let editingTask = $state<Task | null>(null);
  let deletingTask = $state<Task | null>(null);
  let editForm = $state<TaskUpdateInput>({});
  let saving = $state(false);
  let deleting = $state(false);
  let formError = $state('');

  const filters = [
    { label: 'Pending', value: 'pending' },
    { label: 'In Progress', value: 'in_progress' },
    { label: 'Done', value: 'done' },
    { label: 'Overdue', value: 'overdue' }
  ];

  $effect(() => {
    lookup.loadContacts(vaultId);
    lookup.loadActivities(vaultId);
  });

  async function loadTasks(params: { offset: number; limit: number; search: string; filter: string | null }) {
    return tasksApi.list(vaultId, {
      search: params.search || undefined,
      status: params.filter === 'overdue' ? undefined : params.filter ?? undefined,
      overdue: params.filter === 'overdue' ? true : undefined,
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
      await tasksApi.create(vaultId, createForm);
      showCreate = false;
      createForm = { title: '' };
      dataList.refresh();
    } catch (err) {
      formError = err instanceof Error ? err.message : 'Something went wrong';
    } finally {
      creating = false;
    }
  }

  function startEdit(task: Task) {
    editForm = {
      title: task.title,
      description: task.description ?? '',
      due_date: task.due_date ?? '',
      status: task.status,
      priority: task.priority,
      contact_id: task.contact_id ?? '',
      activity_id: task.activity_id ?? ''
    };
    editingTask = task;
  }

  async function handleEdit(e: SubmitEvent) {
    e.preventDefault();
    if (!editingTask) return;
    formError = '';
    saving = true;
    try {
      await tasksApi.update(vaultId, editingTask.id, editForm);
      dataList.refresh();
      editingTask = null;
    } catch (err) {
      formError = err instanceof Error ? err.message : 'Something went wrong';
    } finally {
      saving = false;
    }
  }

  async function handleDelete() {
    if (!deletingTask) return;
    deleting = true;
    try {
      await tasksApi.del(vaultId, deletingTask.id);
      dataList.refresh();
      deletingTask = null;
    } finally {
      deleting = false;
    }
  }

  async function toggleComplete(task: Task) {
    const newStatus = task.status === 'done' ? 'pending' : 'done';
    await tasksApi.update(vaultId, task.id, { status: newStatus });
    dataList.refresh();
  }

  function formatDate(d: string | null | undefined): string {
    if (!d) return '';
    return new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  }

  const priorityLabels: Record<number, string> = { 0: 'None', 1: 'Low', 2: 'Medium', 3: 'High' };
</script>

<svelte:head><title>Tasks</title></svelte:head>

<div class="space-y-4">
    <DataList
      bind:this={dataList}
      load={loadTasks}
      {filters}
      searchPlaceholder="Search tasks..."
      emptyIcon={CheckSquare}
      emptyTitle="No tasks yet"
    >
      {#snippet header()}
        <Button onclick={() => (showCreate = true)}><Plus size={16} /> Add Task</Button>
      {/snippet}
      {#snippet row(item: Task)}
        <div class="flex items-center gap-3 px-4 py-3">
          <button onclick={() => toggleComplete(item)} class="shrink-0 text-neutral-400 hover:text-brand-400">
            {#if item.status === 'done'}
              <CheckCircle size={20} class="text-brand-400" />
            {:else}
              <Circle size={20} />
            {/if}
          </button>
          <div class="min-w-0 flex-1">
            <a href={`/vaults/${vaultId}/tasks/${item.id}`} class="block truncate text-sm font-medium {item.status === 'done' ? 'text-neutral-400 line-through' : 'text-white'}">{item.title}</a>
            {#if item.description}<p class="truncate text-xs text-neutral-500">{item.description}</p>{/if}
          </div>
          <div class="flex items-center gap-2">
            {#if item.due_date}<span class="text-xs text-neutral-500">{formatDate(item.due_date)}</span>{/if}
            {#if item.priority > 0}
              <Badge variant={item.priority >= 3 ? 'danger' : item.priority === 2 ? 'warning' : 'default'} text={priorityLabels[item.priority] ?? `P${item.priority}`} />
            {/if}
          </div>
          <button onclick={() => startEdit(item)} class="shrink-0 text-neutral-400 hover:text-neutral-300">
            <Pencil size={14} />
          </button>
          <button onclick={() => (deletingTask = item)} class="shrink-0 text-neutral-400 hover:text-red-400">
            <Trash2 size={14} />
          </button>
        </div>
      {/snippet}
    </DataList>
</div>

{#if showCreate}
  <Modal title="New Task" onclose={() => (showCreate = false)}>
    <form onsubmit={handleCreate} class="space-y-4">
      <Input label="Title" bind:value={createForm.title} required />
      <Textarea label="Description" bind:value={createForm.description} />
      <Input label="Due date" type="date" bind:value={createForm.due_date} />
      <Select label="Priority" bind:value={createForm.priority}>
        <option value={0}>None</option>
        <option value={1}>Low</option>
        <option value={2}>Medium</option>
        <option value={3}>High</option>
      </Select>
      {#if formError}<p class="text-sm text-red-400">{formError}</p>{/if}
      <div class="flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (showCreate = false)}>Cancel</Button>
        <Button type="submit" loading={creating}>Create</Button>
      </div>
    </form>
  </Modal>
{/if}

{#if editingTask}
  <Modal title="Edit Task" onclose={() => (editingTask = null)}>
    <form onsubmit={handleEdit} class="space-y-4">
      <Input label="Title" bind:value={editForm.title} required />
      <Textarea label="Description" bind:value={editForm.description} />
      <Input label="Due date" type="date" bind:value={editForm.due_date} />
      <Select label="Status" bind:value={editForm.status}>
        <option value="pending">Pending</option>
        <option value="in_progress">In Progress</option>
        <option value="done">Done</option>
      </Select>
      <Select label="Priority" bind:value={editForm.priority}>
        <option value={0}>None</option>
        <option value={1}>Low</option>
        <option value={2}>Medium</option>
        <option value={3}>High</option>
      </Select>
      <Select label="Contact" bind:value={editForm.contact_id}>
        <option value="">Select contact...</option>
        {#each lookup.contacts as c}
          <option value={c.id}>{c.name}</option>
        {/each}
      </Select>
      <Select label="Activity" bind:value={editForm.activity_id}>
        <option value="">None</option>
        {#each lookup.activities as a}
          <option value={a.id}>{a.title}</option>
        {/each}
      </Select>
      {#if formError}<p class="text-sm text-red-400">{formError}</p>{/if}
      <div class="flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (editingTask = null)}>Cancel</Button>
        <Button type="submit" loading={saving}>Save</Button>
      </div>
    </form>
  </Modal>
{/if}

{#if deletingTask}
  <Modal title="Delete Task" onclose={() => (deletingTask = null)}>
    <p class="text-sm text-neutral-400">Delete <strong>{deletingTask.title}</strong>? This cannot be undone.</p>
    <div class="mt-4 flex justify-end gap-3">
      <Button variant="ghost" onclick={() => (deletingTask = null)}>Cancel</Button>
      <Button variant="danger" loading={deleting} onclick={handleDelete}>Delete</Button>
    </div>
  </Modal>
{/if}
