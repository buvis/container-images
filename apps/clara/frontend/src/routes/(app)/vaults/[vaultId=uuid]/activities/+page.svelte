<script lang="ts">
  import { page } from '$app/state';
  import { activitiesApi } from '$api/activities';
  import type { ActivityCreateInput, ActivityUpdateInput, ParticipantInput } from '$api/activities';
  import DataList from '$components/data/DataList.svelte';
  import Button from '$components/ui/Button.svelte';
  import Modal from '$components/ui/Modal.svelte';
  import Input from '$components/ui/Input.svelte';
  import Textarea from '$components/ui/Textarea.svelte';
  import Select from '$components/ui/Select.svelte';
  import ParticipantsEditor from '$components/activities/ParticipantsEditor.svelte';
  import { Plus, CalendarDays, Pencil, Trash2 } from 'lucide-svelte';
  import type { Activity } from '$lib/types/models';
  import { lookup } from '$state/lookup.svelte';

  const vaultId = $derived(page.params.vaultId!);

  let showCreate = $state(false);
  let createForm = $state<ActivityCreateInput>({
    title: '',
    description: '',
    happened_at: '',
    location: ''
  });
  let creating = $state(false);
  let dataList: DataList<Activity>;
  let editingActivity = $state<Activity | null>(null);
  let deletingActivity = $state<Activity | null>(null);
  let editForm = $state<ActivityUpdateInput>({});
  let editParticipants = $state<ParticipantInput[]>([]);
  let saving = $state(false);
  let deleting = $state(false);
  let formError = $state('');

  $effect(() => {
    lookup.loadContacts(vaultId);
    lookup.loadActivityTypes(vaultId);
  });

  async function loadActivities(params: { offset: number; limit: number; search: string; filter: string | null }) {
    return activitiesApi.list(vaultId, {
      offset: params.offset,
      limit: params.limit,
      q: params.search || undefined
    });
  }

  async function handleCreate(e: SubmitEvent) {
    e.preventDefault();
    if (!createForm.title.trim() || !createForm.happened_at) return;
    formError = '';
    creating = true;
    try {
      await activitiesApi.create(vaultId, createForm);
      showCreate = false;
      createForm = { title: '', description: '', happened_at: '', location: '' };
      dataList.refresh();
    } catch (err) {
      formError = err instanceof Error ? err.message : 'Something went wrong';
    } finally {
      creating = false;
    }
  }

  function startEdit(activity: Activity) {
    editForm = {
      activity_type_id: activity.activity_type_id,
      title: activity.title,
      description: activity.description,
      happened_at: (() => { const d = new Date(activity.happened_at); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}T${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`; })(),
      location: activity.location
    };
    editParticipants = activity.participants?.map(p => ({
      contact_id: p.contact_id,
      role: p.role
    })) ?? [];
    editingActivity = activity;
  }

  async function handleEdit(e: SubmitEvent) {
    e.preventDefault();
    if (!editingActivity) return;
    formError = '';
    saving = true;
    try {
      const data = {
        ...editForm,
        happened_at: new Date(editForm.happened_at!).toISOString(),
        participants: editParticipants
      };
      await activitiesApi.update(vaultId, editingActivity.id, data);
      dataList.refresh();
      editingActivity = null;
    } catch (err) {
      formError = err instanceof Error ? err.message : 'Something went wrong';
    } finally {
      saving = false;
    }
  }

  async function handleDelete() {
    if (!deletingActivity) return;
    deleting = true;
    try {
      await activitiesApi.del(vaultId, deletingActivity.id);
      dataList.refresh();
      deletingActivity = null;
    } finally {
      deleting = false;
    }
  }

  function formatDate(value: string): string {
    return new Date(value).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
</script>

<svelte:head><title>Activities</title></svelte:head>

<div class="space-y-4">
    <DataList
      bind:this={dataList}
      load={loadActivities}
      searchPlaceholder="Search activities..."
      emptyIcon={CalendarDays}
      emptyTitle="No activities yet"
      emptyDescription="Add your first activity to track important moments"
    >
      {#snippet header()}
        <Button onclick={() => (showCreate = true)}><Plus size={16} /> Add Activity</Button>
      {/snippet}
      {#snippet row(item: Activity)}
        <div class="flex items-start justify-between gap-3 px-4 py-3">
          <div class="min-w-0 flex-1">
            <a href={`/vaults/${vaultId}/activities/${item.id}`} class="block truncate text-sm font-medium text-white hover:underline">{item.title}</a>
            {#if item.description}
              <p class="truncate text-xs text-neutral-500">{item.description}</p>
            {/if}
            {#if item.location}
              <p class="truncate text-xs text-neutral-500">{item.location}</p>
            {/if}
          </div>
          <span class="shrink-0 text-xs text-neutral-500">{formatDate(item.happened_at)}</span>
          <div class="flex items-center gap-2">
            <button onclick={() => startEdit(item)} class="shrink-0 text-neutral-400 hover:text-neutral-300">
              <Pencil size={14} />
            </button>
            <button onclick={() => (deletingActivity = item)} class="shrink-0 text-neutral-400 hover:text-red-400">
              <Trash2 size={14} />
            </button>
          </div>
        </div>
      {/snippet}
    </DataList>
</div>

{#if showCreate}
  <Modal title="New Activity" onclose={() => (showCreate = false)}>
    <form onsubmit={handleCreate} class="space-y-4">
      <Input label="Title" bind:value={createForm.title} required />
      <Textarea label="Description" bind:value={createForm.description} />
      <Input label="Date and time" type="datetime-local" bind:value={createForm.happened_at} required />
      <Input label="Location" bind:value={createForm.location} />
      {#if formError}<p class="text-sm text-red-400">{formError}</p>{/if}
      <div class="flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (showCreate = false)}>Cancel</Button>
        <Button type="submit" loading={creating}>Create</Button>
      </div>
    </form>
  </Modal>
{/if}

{#if editingActivity}
  <Modal title="Edit Activity" onclose={() => (editingActivity = null)}>
    <form onsubmit={handleEdit} class="space-y-4">
      <Select label="Type" bind:value={editForm.activity_type_id}>
        <option value="">No Type</option>
        {#each lookup.activityTypes as t}
          <option value={t.id}>{t.name}</option>
        {/each}
      </Select>
      <Input label="Title" bind:value={editForm.title} required />
      <Textarea label="Description" bind:value={editForm.description} />
      <Input label="Date and time" type="datetime-local" bind:value={editForm.happened_at} required />
      <Input label="Location" bind:value={editForm.location} />

      <div>
        <label class="mb-1 block text-sm font-medium text-neutral-300">Participants</label>
        <ParticipantsEditor bind:participants={editParticipants} {vaultId} />
      </div>

      {#if formError}<p class="text-sm text-red-400">{formError}</p>{/if}
      <div class="flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (editingActivity = null)}>Cancel</Button>
        <Button type="submit" loading={saving}>Save</Button>
      </div>
    </form>
  </Modal>
{/if}

{#if deletingActivity}
  <Modal title="Delete Activity" onclose={() => (deletingActivity = null)}>
    <p class="text-sm text-neutral-400">Delete <strong>{deletingActivity.title}</strong>? This cannot be undone.</p>
    <div class="mt-4 flex justify-end gap-3">
      <Button variant="ghost" onclick={() => (deletingActivity = null)}>Cancel</Button>
      <Button variant="danger" loading={deleting} onclick={handleDelete}>Delete</Button>
    </div>
  </Modal>
{/if}
