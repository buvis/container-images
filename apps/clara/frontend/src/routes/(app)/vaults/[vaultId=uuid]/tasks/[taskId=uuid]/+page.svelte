<script lang="ts">
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import { tasksApi } from '$api/tasks';
  import type { TaskUpdateInput } from '$api/tasks';
  import Spinner from '$components/ui/Spinner.svelte';
  import Button from '$components/ui/Button.svelte';
  import Input from '$components/ui/Input.svelte';
  import Modal from '$components/ui/Modal.svelte';
  import Badge from '$components/ui/Badge.svelte';
  import CustomFieldsSection from '$components/customization/CustomFieldsSection.svelte';
  import { ArrowLeft, Pencil, Trash2, Save, X } from 'lucide-svelte';
  import type { Task } from '$lib/types/models';
  import { lookup } from '$state/lookup.svelte';

  const vaultId = $derived(page.params.vaultId!);
  const taskId = $derived(page.params.taskId!);

  let task = $state<Task | null>(null);
  let loading = $state(true);
  let loadError = $state('');
  let editing = $state(false);
  let saving = $state(false);
  let showDelete = $state(false);
  let deleting = $state(false);
  let editForm = $state<TaskUpdateInput>({});

  const priorityLabels: Record<number, string> = { 0: 'None', 1: 'Low', 2: 'Medium', 3: 'High' };

  $effect(() => {
    loading = true;
    loadError = '';
    (async () => {
      try {
        const [t] = await Promise.all([
          tasksApi.get(vaultId, taskId),
          lookup.loadContacts(vaultId),
          lookup.loadActivities(vaultId)
        ]);
        task = t;
      } catch (e) {
        loadError = e instanceof Error ? e.message : 'Failed to load task';
      } finally {
        loading = false;
      }
    })();
  });

  function startEdit() {
    if (!task) return;
    editForm = {
      title: task.title,
      description: task.description,
      due_date: task.due_date ? task.due_date.split('T')[0] : null,
      status: task.status,
      priority: task.priority,
      contact_id: task.contact_id,
      activity_id: task.activity_id
    };
    editing = true;
  }

  async function handleSave() {
    saving = true;
    try {
      task = await tasksApi.update(vaultId, taskId, editForm);
      editing = false;
    } finally {
      saving = false;
    }
  }

  async function handleDelete() {
    deleting = true;
    try {
      await tasksApi.del(vaultId, taskId);
      goto(`/vaults/${vaultId}/tasks`);
    } finally {
      deleting = false;
    }
  }

  function formatDate(d: string): string {
    return new Date(d).toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  }

  function getStatusVariant(status: string): 'default' | 'success' | 'warning' | 'danger' {
    switch (status) {
      case 'done': return 'success';
      case 'in_progress': return 'warning';
      default: return 'default';
    }
  }

  function getPriorityVariant(priority: number): 'default' | 'success' | 'warning' | 'danger' {
    switch (priority) {
      case 3: return 'danger';
      case 2: return 'warning';
      default: return 'default';
    }
  }
</script>

<svelte:head>
  <title>{task ? task.title : 'Task Details'}</title>
</svelte:head>

{#if loading}
  <div class="flex justify-center py-12">
    <Spinner />
  </div>
{:else if loadError}
  <div class="flex flex-col items-center justify-center gap-4 py-20">
    <p class="text-red-400">{loadError}</p>
    <a href="/vaults/{vaultId}/tasks" class="text-sm text-brand-400 hover:underline">Go back</a>
  </div>
{:else if task}
  <div class="mx-auto max-w-2xl space-y-6">
    <div class="flex items-center justify-between">
      <a href="/vaults/{vaultId}/tasks" class="text-neutral-400 hover:text-neutral-300">
        <ArrowLeft size={20} />
      </a>
      <div class="flex gap-2">
        {#if editing}
          <Button variant="ghost" size="sm" onclick={() => (editing = false)}>
            <X size={16}  /> Cancel
          </Button>
          <Button size="sm" loading={saving} onclick={handleSave}>
            <Save size={16}  /> Save
          </Button>
        {:else}
          <Button variant="ghost" size="sm" onclick={startEdit}>
            <Pencil size={16} />
          </Button>
          <Button variant="ghost" size="sm" onclick={() => (showDelete = true)}>
            <Trash2 size={16} class="text-red-400" />
          </Button>
        {/if}
      </div>
    </div>

    {#if editing}
      <div class="space-y-4 rounded-lg border border-neutral-700 bg-neutral-800/50 p-6">
        <Input label="Title" bind:value={editForm.title} />
        
        <div class="grid gap-4 sm:grid-cols-2">
          <Input type="date" label="Due Date" bind:value={editForm.due_date} />
          
          <div>
            <label class="mb-1 block text-sm font-medium text-neutral-300">Status</label>
            <select bind:value={editForm.status} class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500">
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="done">Done</option>
            </select>
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-neutral-300">Priority</label>
            <select bind:value={editForm.priority} class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500">
              {#each Object.entries(priorityLabels) as [val, label]}
                <option value={Number(val)}>{label}</option>
              {/each}
            </select>
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-neutral-300">Contact</label>
            <select bind:value={editForm.contact_id} class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500">
              <option value={null}>None</option>
              {#each lookup.contacts as contact}
                <option value={contact.id}>{contact.name}</option>
              {/each}
            </select>
          </div>
        </div>

        <div>
          <label class="mb-1 block text-sm font-medium text-neutral-300">Description</label>
          <textarea 
            bind:value={editForm.description} 
            rows="6" 
            class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
          ></textarea>
        </div>

        <div>
          <label class="mb-1 block text-sm font-medium text-neutral-300">Activity</label>
          <select bind:value={editForm.activity_id} class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500">
            <option value={null}>None</option>
            {#each lookup.activities as activity}
              <option value={activity.id}>{activity.title}</option>
            {/each}
          </select>
        </div>
      </div>
    {:else}
      <div class="space-y-6">
        <div>
          <div class="mb-2 flex flex-wrap items-center gap-2">
            <Badge variant={getStatusVariant(task.status)} text={task.status.replace('_', ' ')} />
            {#if task.priority > 0}
              <Badge variant={getPriorityVariant(task.priority)} text={priorityLabels[task.priority]} />
            {/if}
            {#if task.due_date}
              <span class="text-sm text-neutral-400">Due {formatDate(task.due_date)}</span>
            {/if}
          </div>
          <h1 class="text-2xl font-semibold text-white">{task.title}</h1>
        </div>

        {#if task.contact_id}
          <div class="flex items-center gap-2 text-sm text-neutral-400">
            <span class="font-medium text-neutral-300">Contact:</span>
            {lookup.getContactName(task.contact_id)}
          </div>
        {/if}

        {#if task.description}
          <div class="whitespace-pre-wrap rounded-lg border border-neutral-700 bg-neutral-800/30 p-4 text-sm leading-relaxed text-neutral-300">
            {task.description}
          </div>
        {:else}
          <p class="text-sm italic text-neutral-500">No description provided.</p>
        {/if}
        
        {#if task.activity_id}
           <div class="text-xs text-neutral-600 font-mono">Linked Activity: {task.activity_id}</div>
        {/if}

        <CustomFieldsSection {vaultId} entityType="task" entityId={taskId} />
      </div>
    {/if}
  </div>

  {#if showDelete}
    <Modal title="Delete Task" onclose={() => (showDelete = false)}>
      <p class="text-sm text-neutral-400">
        Are you sure you want to delete "{task.title}"? This cannot be undone.
      </p>
      <div class="mt-4 flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (showDelete = false)}>Cancel</Button>
        <Button variant="danger" loading={deleting} onclick={handleDelete}>Delete</Button>
      </div>
    </Modal>
  {/if}
{/if}
