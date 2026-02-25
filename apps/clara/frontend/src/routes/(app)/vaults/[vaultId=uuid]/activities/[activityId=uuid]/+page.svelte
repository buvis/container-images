<script lang="ts">
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import { activitiesApi } from '$api/activities';
  import type { ActivityUpdateInput, ParticipantInput } from '$api/activities';
  import { lookup } from '$state/lookup.svelte';
  import Spinner from '$components/ui/Spinner.svelte';
  import Button from '$components/ui/Button.svelte';
  import Input from '$components/ui/Input.svelte';
  import Modal from '$components/ui/Modal.svelte';
  import Badge from '$components/ui/Badge.svelte';
  import ParticipantsEditor from '$components/activities/ParticipantsEditor.svelte';
  import CustomFieldsSection from '$components/customization/CustomFieldsSection.svelte';
  import { ArrowLeft, Pencil, Trash2, Save, X } from 'lucide-svelte';
  import type { Activity } from '$lib/types/models';

  const vaultId = $derived(page.params.vaultId!);
  const activityId = $derived(page.params.activityId!);

  let activity = $state<Activity | null>(null);
  let loading = $state(true);
  let loadError = $state('');
  let editing = $state(false);
  let saving = $state(false);
  let showDelete = $state(false);
  let deleting = $state(false);
  let editForm = $state<ActivityUpdateInput>({});
  
  // Local state for participants editing
  let editParticipants = $state<ParticipantInput[]>([]);

  $effect(() => {
    loading = true;
    loadError = '';
    lookup.loadContacts(vaultId);
    lookup.loadActivityTypes(vaultId);
    (async () => {
      try {
        activity = await activitiesApi.get(vaultId, activityId);
      } catch (e) {
        loadError = e instanceof Error ? e.message : 'Failed to load activity';
      } finally {
        loading = false;
      }
    })();
  });

  function startEdit() {
    if (!activity) return;
    
    // Format happened_at for datetime-local input (YYYY-MM-DDThh:mm)
    const date = new Date(activity.happened_at);
    // Manually format to local YYYY-MM-DDTHH:MM
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const localISOTime = `${year}-${month}-${day}T${hours}:${minutes}`;

    editForm = { 
      activity_type_id: activity.activity_type_id, 
      title: activity.title, 
      description: activity.description, 
      happened_at: localISOTime,
      location: activity.location
    };
    
    // Clone participants to avoid mutating original state until save
    editParticipants = activity.participants.map(p => ({
      contact_id: p.contact_id,
      role: p.role
    }));
    
    editing = true;
  }

  async function handleSave() {
    saving = true;
    try { 
      // Include participants in the update
      const updateData: ActivityUpdateInput = {
        ...editForm,
        participants: editParticipants
      };
      
      // Convert datetime-local back to ISO
      if (editForm.happened_at) {
        updateData.happened_at = new Date(editForm.happened_at).toISOString();
      }

      activity = await activitiesApi.update(vaultId, activityId, updateData); 
      editing = false; 
    } finally { 
      saving = false; 
    }
  }

  async function handleDelete() {
    deleting = true;
    try { 
      await activitiesApi.del(vaultId, activityId); 
      goto(`/vaults/${vaultId}/activities`); 
    } finally { 
      deleting = false; 
    }
  }

  function formatDate(d: string): string {
    return new Date(d).toLocaleDateString(undefined, { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function getActivityTypeName(id: string | null | undefined) {
    if (!id) return null;
    return lookup.activityTypes.find(t => t.id === id)?.name;
  }
  
</script>

<svelte:head>
  <title>{activity ? activity.title : 'Activity Detail'}</title>
</svelte:head>

{#if loading}
  <div class="flex justify-center py-12"><Spinner /></div>
{:else if loadError}
  <div class="flex flex-col items-center justify-center gap-4 py-20">
    <p class="text-red-400">{loadError}</p>
    <a href="/vaults/{vaultId}/activities" class="text-sm text-brand-400 hover:underline">Go back</a>
  </div>
{:else if activity}
  <div class="mx-auto max-w-2xl space-y-6">
    <div class="flex items-center justify-between">
      <a href="/vaults/{vaultId}/activities" class="text-neutral-400 hover:text-neutral-300"><ArrowLeft size={20} /></a>
      <div class="flex gap-2">
        {#if editing}
          <Button variant="ghost" size="sm" onclick={() => (editing = false)}><X size={16} /> Cancel</Button>
          <Button size="sm" loading={saving} onclick={handleSave}><Save size={16} /> Save</Button>
        {:else}
          <Button variant="ghost" size="sm" onclick={startEdit}><Pencil size={16} /></Button>
          <Button variant="ghost" size="sm" onclick={() => (showDelete = true)}><Trash2 size={16} class="text-red-400" /></Button>
        {/if}
      </div>
    </div>

    {#if editing}
      <div class="space-y-4">
        <div>
          <label class="mb-1 block text-sm font-medium text-neutral-300">Type</label>
          <select 
            bind:value={editForm.activity_type_id}
            class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
          >
            <option value="">No Type</option>
            {#each lookup.activityTypes as type}
              <option value={type.id}>{type.name}</option>
            {/each}
          </select>
        </div>

        <Input label="Title" bind:value={editForm.title} />
        
        <Input label="Date & Time" type="datetime-local" bind:value={editForm.happened_at} />
        
        <Input label="Location" bind:value={editForm.location} />
        
        <div>
          <label class="mb-1 block text-sm font-medium text-neutral-300">Description</label>
          <textarea 
            bind:value={editForm.description} 
            rows="6" 
            class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
          ></textarea>
        </div>

        <div>
          <label class="mb-2 block text-sm font-medium text-neutral-300">Participants</label>
          <ParticipantsEditor bind:participants={editParticipants} {vaultId} />
        </div>
      </div>
    {:else}
      <div class="space-y-4">
        <div class="flex items-center gap-3">
          {#if activity.activity_type_id}
            <Badge text={getActivityTypeName(activity.activity_type_id) ?? 'Unknown'} />
          {/if}
          <span class="text-sm text-neutral-500">{formatDate(activity.happened_at)}</span>
        </div>
        
        <h1 class="text-2xl font-semibold text-white">{activity.title}</h1>
        
        {#if activity.location}
          <div class="text-sm text-neutral-400">{activity.location}</div>
        {/if}

        {#if activity.description}
          <div class="whitespace-pre-wrap text-sm leading-relaxed text-neutral-300">{activity.description}</div>
        {/if}

        {#if activity.participants.length > 0}
          <div class="mt-6 border-t border-neutral-800 pt-4">
            <h3 class="mb-3 text-sm font-medium text-neutral-400">Participants</h3>
            <div class="space-y-2">
              {#each activity.participants as p}
                <div class="flex items-center justify-between rounded-lg bg-neutral-800/50 px-3 py-2">
                  <span class="font-medium text-white">{lookup.getContactName(p.contact_id)}</span>
                  {#if p.role}
                    <span class="text-xs text-neutral-500">{p.role}</span>
                  {/if}
                </div>
              {/each}
            </div>
          </div>
        {/if}

        <CustomFieldsSection {vaultId} entityType="activity" entityId={activityId} />
      </div>
    {/if}
  </div>

  {#if showDelete}
    <Modal title="Delete Activity" onclose={() => (showDelete = false)}>
      <p class="text-sm text-neutral-400">Delete this activity? This cannot be undone.</p>
      <div class="mt-4 flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (showDelete = false)}>Cancel</Button>
        <Button variant="danger" loading={deleting} onclick={handleDelete}>Delete</Button>
      </div>
    </Modal>
  {/if}
{/if}
