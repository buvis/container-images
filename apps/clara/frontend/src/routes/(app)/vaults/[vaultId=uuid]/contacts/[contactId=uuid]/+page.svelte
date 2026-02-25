<script lang="ts">
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import { contactsApi } from '$api/contacts';
  import type { ContactUpdateInput } from '$api/contacts';
  import { notesApi } from '$api/notes';
  import { api } from '$api/client';
  import ContactTabs from '$components/contacts/ContactTabs.svelte';
  import ContactMethodsSection from '$components/contacts/ContactMethodsSection.svelte';
  import AddressesSection from '$components/contacts/AddressesSection.svelte';
  import PetsSection from '$components/contacts/PetsSection.svelte';
  import TagsSection from '$components/contacts/TagsSection.svelte';
  import RelationshipsSection from '$components/contacts/RelationshipsSection.svelte';
  import CustomFieldsSection from '$components/customization/CustomFieldsSection.svelte';
  import Spinner from '$components/ui/Spinner.svelte';
  import Button from '$components/ui/Button.svelte';
  import Input from '$components/ui/Input.svelte';
  import Modal from '$components/ui/Modal.svelte';
  import Badge from '$components/ui/Badge.svelte';
  import Textarea from '$components/ui/Textarea.svelte';
  import { Star, Pencil, Trash2, ArrowLeft, Camera } from 'lucide-svelte';
  import { filesApi } from '$api/files';
  import type { Contact, Activity, Task, Note, Gift, Debt } from '$lib/types/models';
  import type { PaginatedResponse } from '$lib/types/common';

  const vaultId = $derived(page.params.vaultId!);
  const contactId = $derived(page.params.contactId!);

  let contact = $state<Contact | null>(null);
  let loading = $state(true);
  let loadError = $state('');
  let showEdit = $state(false);
  let showDelete = $state(false);
  let editForm = $state<ContactUpdateInput>({});
  let saving = $state(false);
  let deleting = $state(false);
  let photoUploading = $state(false);

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'activities', label: 'Activities' },
    { id: 'tasks', label: 'Tasks' },
    { id: 'notes', label: 'Notes' },
    { id: 'gifts', label: 'Gifts' },
    { id: 'debts', label: 'Debts' }
  ];

  let activeTab = $state('overview');

  // Tab data
  let tabActivities = $state<Activity[]>([]);
  let tabTasks = $state<Task[]>([]);
  let tabNotes = $state<Note[]>([]);
  let tabGifts = $state<Gift[]>([]);
  let tabDebts = $state<Debt[]>([]);
  let tabLoading = $state(false);
  const TAB_LIMIT = 20;
  let tabTotals = $state<Record<string, number>>({});

  $effect(() => {
    loading = true;
    loadError = '';
    (async () => {
      try {
        contact = await contactsApi.get(vaultId, contactId);
      } catch (e) {
        loadError = e instanceof Error ? e.message : 'Failed to load contact';
      } finally {
        loading = false;
      }
    })();
  });

  function loadTab(tab: string, append = false) {
    if (!contact) return;
    tabLoading = true;
    const base = `/vaults/${vaultId}`;
    const cid = `contact_id=${contactId}`;
    const offset = append ? { activities: tabActivities, tasks: tabTasks, notes: tabNotes, gifts: tabGifts, debts: tabDebts }[tab]?.length ?? 0 : 0;
    const lim = `limit=${TAB_LIMIT}&offset=${offset}`;
    if (tab === 'activities') {
      api.get<PaginatedResponse<Activity>>(`${base}/contacts/${contactId}/activities?${lim}`).then((r) => { tabActivities = append ? [...tabActivities, ...r.items] : r.items; tabTotals.activities = r.meta.total; tabLoading = false; });
    } else if (tab === 'tasks') {
      api.get<PaginatedResponse<Task>>(`${base}/tasks?${cid}&${lim}`).then((r) => { tabTasks = append ? [...tabTasks, ...r.items] : r.items; tabTotals.tasks = r.meta.total; tabLoading = false; });
    } else if (tab === 'notes') {
      notesApi.forContact(vaultId, contactId, { limit: TAB_LIMIT, offset }).then((r) => { tabNotes = append ? [...tabNotes, ...r.items] : r.items; tabTotals.notes = r.meta.total; tabLoading = false; });
    } else if (tab === 'gifts') {
      api.get<PaginatedResponse<Gift>>(`${base}/gifts?${cid}&${lim}`).then((r) => { tabGifts = append ? [...tabGifts, ...r.items] : r.items; tabTotals.gifts = r.meta.total; tabLoading = false; });
    } else if (tab === 'debts') {
      api.get<PaginatedResponse<Debt>>(`${base}/debts?${cid}&${lim}`).then((r) => { tabDebts = append ? [...tabDebts, ...r.items] : r.items; tabTotals.debts = r.meta.total; tabLoading = false; });
    } else {
      tabLoading = false;
    }
  }

  $effect(() => {
    if (!contact) return;
    loadTab(activeTab);
  });

  function openEdit() {
    if (!contact) return;
    editForm = {
      first_name: contact.first_name,
      last_name: contact.last_name,
      nickname: contact.nickname,
      birthdate: contact.birthdate,
      gender: contact.gender,
      pronouns: contact.pronouns,
      notes_summary: contact.notes_summary,
      favorite: contact.favorite
    };
    showEdit = true;
  }

  async function handleSave() {
    saving = true;
    try {
      contact = await contactsApi.update(vaultId, contactId, editForm);
      showEdit = false;
    } finally {
      saving = false;
    }
  }

  async function handleDelete() {
    deleting = true;
    try {
      await contactsApi.del(vaultId, contactId);
      goto(`/vaults/${vaultId}/contacts`);
    } finally {
      deleting = false;
    }
  }

  async function toggleFavorite() {
    if (!contact) return;
    contact = await contactsApi.update(vaultId, contactId, { favorite: !contact.favorite });
  }

  async function handlePhotoUpload(e: Event) {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    photoUploading = true;
    try {
      const uploaded = await filesApi.upload(vaultId, file);
      contact = await contactsApi.update(vaultId, contactId, { photo_file_id: uploaded.id });
    } finally {
      photoUploading = false;
      (e.target as HTMLInputElement).value = '';
    }
  }

  function formatDate(d: string | null | undefined): string {
    if (!d) return '';
    return new Date(d).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
  }
</script>

<svelte:head>
  <title>{contact ? `${contact.first_name} ${contact.last_name}` : 'Contact'}</title>
</svelte:head>

{#if loading}
  <div class="flex justify-center py-12"><Spinner /></div>
{:else if loadError}
  <div class="flex flex-col items-center justify-center gap-4 py-20">
    <p class="text-red-400">{loadError}</p>
    <a href="/vaults/{vaultId}/contacts" class="text-sm text-brand-400 hover:underline">Go back</a>
  </div>
{:else if contact}
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-start gap-4">
      <a href="/vaults/{vaultId}/contacts" class="mt-1 text-neutral-400 hover:text-neutral-300">
        <ArrowLeft size={20} />
      </a>

      <input id="photo-upload" type="file" accept="image/*" class="hidden" onchange={handlePhotoUpload} />
      <button onclick={() => document.getElementById('photo-upload')?.click()} class="group relative" disabled={photoUploading}>
        {#if contact.photo_file_id}
          <img
            src="/api/v1/vaults/{vaultId}/files/{contact.photo_file_id}/download"
            alt="{contact.first_name}"
            class="h-14 w-14 rounded-full object-cover"
          />
        {:else}
          <div class="flex h-14 w-14 items-center justify-center rounded-full bg-brand-500/20 text-lg font-semibold text-brand-400">
            {contact.first_name[0]}{contact.last_name?.[0] ?? ''}
          </div>
        {/if}
        <div class="absolute inset-0 flex items-center justify-center rounded-full bg-black/50 opacity-0 transition group-hover:opacity-100">
          <Camera size={18} class="text-white" />
        </div>
      </button>

      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2">
          <h1 class="text-2xl font-semibold text-white">{contact.first_name} {contact.last_name}</h1>
          <button onclick={toggleFavorite} class="p-1" aria-label="Toggle favorite">
            <Star size={20} class={contact.favorite ? 'fill-amber-400 text-amber-400' : 'text-neutral-400 hover:text-amber-400'} />
          </button>
        </div>
        {#if contact.nickname}<p class="text-sm text-neutral-500">"{contact.nickname}"</p>{/if}
        {#if contact.pronouns}<p class="text-xs text-neutral-400">{contact.pronouns}</p>{/if}
      </div>

      <div class="flex gap-2">
        <Button variant="ghost" size="sm" onclick={openEdit}><Pencil size={16} /></Button>
        <Button variant="ghost" size="sm" onclick={() => (showDelete = true)}><Trash2 size={16} class="text-red-400" /></Button>
      </div>
    </div>

    <ContactTabs {tabs} active={activeTab} onchange={(id) => (activeTab = id)} />

    <div>
      {#if activeTab === 'overview'}
        <div class="grid gap-4 sm:grid-cols-2">
          <div class="rounded-lg border border-neutral-800 p-4">
            <h3 class="mb-2 text-xs font-semibold uppercase tracking-wider text-neutral-500">Details</h3>
            <dl class="space-y-2 text-sm">
              {#if contact.birthdate}
                <div class="flex justify-between"><dt class="text-neutral-500">Birthday</dt><dd class="text-white">{formatDate(contact.birthdate)}</dd></div>
              {/if}
              {#if contact.gender}
                <div class="flex justify-between"><dt class="text-neutral-500">Gender</dt><dd class="text-white">{contact.gender}</dd></div>
              {/if}
            </dl>
          </div>
          {#if contact.notes_summary}
            <div class="rounded-lg border border-neutral-800 p-4">
              <h3 class="mb-2 text-xs font-semibold uppercase tracking-wider text-neutral-500">Notes</h3>
              <p class="whitespace-pre-wrap text-sm text-neutral-300">{contact.notes_summary}</p>
            </div>
          {/if}
          <ContactMethodsSection {vaultId} {contactId} />
          <AddressesSection {vaultId} {contactId} />
          <TagsSection {vaultId} {contactId} />
          <PetsSection {vaultId} {contactId} />
          <RelationshipsSection {vaultId} {contactId} />
          <CustomFieldsSection {vaultId} entityType="contact" entityId={contactId} />
        </div>

      {:else if tabLoading}
        <div class="flex justify-center py-8"><Spinner /></div>

      {:else if activeTab === 'activities'}
        {#if tabActivities.length === 0}
          <p class="py-8 text-center text-sm text-neutral-500">No activities</p>
        {:else}
          <div class="divide-y divide-neutral-800 rounded-xl border border-neutral-800">
            {#each tabActivities as item}
              <div class="flex items-center justify-between px-4 py-3">
                <div class="min-w-0"><p class="truncate text-sm font-medium text-white">{item.title}</p>{#if item.location}<p class="truncate text-xs text-neutral-500">{item.location}</p>{/if}</div>
                <span class="shrink-0 text-xs text-neutral-500">{formatDate(item.happened_at)}</span>
              </div>
            {/each}
          </div>
          {#if tabActivities.length < (tabTotals.activities ?? 0)}
            <button onclick={() => loadTab('activities', true)} class="mt-3 w-full text-center text-sm text-brand-400 hover:underline">Load more</button>
          {/if}
        {/if}

      {:else if activeTab === 'tasks'}
        {#if tabTasks.length === 0}
          <p class="py-8 text-center text-sm text-neutral-500">No tasks</p>
        {:else}
          <div class="divide-y divide-neutral-800 rounded-xl border border-neutral-800">
            {#each tabTasks as item}
              <div class="flex items-center justify-between px-4 py-3">
                <div class="min-w-0"><p class="truncate text-sm font-medium text-white">{item.title}</p>{#if item.due_date}<p class="text-xs text-neutral-500">Due {formatDate(item.due_date)}</p>{/if}</div>
                <Badge variant={item.status === 'done' ? 'success' : 'default'} text={item.status} />
              </div>
            {/each}
          </div>
          {#if tabTasks.length < (tabTotals.tasks ?? 0)}
            <button onclick={() => loadTab('tasks', true)} class="mt-3 w-full text-center text-sm text-brand-400 hover:underline">Load more</button>
          {/if}
        {/if}

      {:else if activeTab === 'notes'}
        {#if tabNotes.length === 0}
          <p class="py-8 text-center text-sm text-neutral-500">No notes</p>
        {:else}
          <div class="divide-y divide-neutral-800 rounded-xl border border-neutral-800">
            {#each tabNotes as item}
              <div class="px-4 py-3">
                <p class="text-sm font-medium text-white">{item.title || 'Untitled'}</p>
                <p class="mt-1 line-clamp-2 text-xs text-neutral-500">{item.body_markdown}</p>
                <span class="mt-2 block text-xs text-neutral-400">{formatDate(item.created_at)}</span>
              </div>
            {/each}
          </div>
          {#if tabNotes.length < (tabTotals.notes ?? 0)}
            <button onclick={() => loadTab('notes', true)} class="mt-3 w-full text-center text-sm text-brand-400 hover:underline">Load more</button>
          {/if}
        {/if}

      {:else if activeTab === 'gifts'}
        {#if tabGifts.length === 0}
          <p class="py-8 text-center text-sm text-neutral-500">No gifts</p>
        {:else}
          <div class="divide-y divide-neutral-800 rounded-xl border border-neutral-800">
            {#each tabGifts as item}
              <div class="flex items-center justify-between px-4 py-3">
                <div class="min-w-0"><p class="truncate text-sm font-medium text-white">{item.name}</p>{#if item.amount}<p class="text-xs text-neutral-500">{item.currency} {item.amount}</p>{/if}</div>
                <Badge variant={item.direction === 'given' ? 'success' : 'default'} text={item.direction} />
              </div>
            {/each}
          </div>
          {#if tabGifts.length < (tabTotals.gifts ?? 0)}
            <button onclick={() => loadTab('gifts', true)} class="mt-3 w-full text-center text-sm text-brand-400 hover:underline">Load more</button>
          {/if}
        {/if}

      {:else if activeTab === 'debts'}
        {#if tabDebts.length === 0}
          <p class="py-8 text-center text-sm text-neutral-500">No debts</p>
        {:else}
          <div class="divide-y divide-neutral-800 rounded-xl border border-neutral-800">
            {#each tabDebts as item}
              <div class="flex items-center justify-between px-4 py-3">
                <div class="min-w-0"><p class="text-sm font-medium text-white">{item.currency} {item.amount}</p>{#if item.notes}<p class="truncate text-xs text-neutral-500">{item.notes}</p>{/if}</div>
                <div class="flex items-center gap-2">
                  <Badge variant={item.direction === 'you_owe' ? 'danger' : 'success'} text={item.direction === 'you_owe' ? 'You owe' : 'Owed to you'} />
                  {#if item.settled}<Badge text="Settled" />{/if}
                </div>
              </div>
            {/each}
          </div>
          {#if tabDebts.length < (tabTotals.debts ?? 0)}
            <button onclick={() => loadTab('debts', true)} class="mt-3 w-full text-center text-sm text-brand-400 hover:underline">Load more</button>
          {/if}
        {/if}
      {/if}
    </div>
  </div>

  {#if showEdit}
    <Modal title="Edit Contact" onclose={() => (showEdit = false)}>
      <form onsubmit={handleSave} class="space-y-4">
        <Input label="First name" bind:value={editForm.first_name} required />
        <Input label="Last name" bind:value={editForm.last_name} />
        <Input label="Nickname" bind:value={editForm.nickname} />
        <Input label="Birthdate" type="date" bind:value={editForm.birthdate} />
        <Input label="Gender" bind:value={editForm.gender} />
        <Input label="Pronouns" bind:value={editForm.pronouns} />
        <Textarea label="Notes summary" bind:value={editForm.notes_summary} rows={3} />
        <div class="flex justify-end gap-3">
          <Button variant="ghost" onclick={() => (showEdit = false)}>Cancel</Button>
          <Button type="submit" loading={saving}>Save</Button>
        </div>
      </form>
    </Modal>
  {/if}

  {#if showDelete}
    <Modal title="Delete Contact" onclose={() => (showDelete = false)}>
      <p class="text-sm text-neutral-400">Delete <strong>{contact.first_name} {contact.last_name}</strong>? This cannot be undone.</p>
      <div class="mt-4 flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (showDelete = false)}>Cancel</Button>
        <Button variant="danger" loading={deleting} onclick={handleDelete}>Delete</Button>
      </div>
    </Modal>
  {/if}
{/if}
