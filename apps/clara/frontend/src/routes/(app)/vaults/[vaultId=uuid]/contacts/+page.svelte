<script lang="ts">
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import { contactsApi } from '$api/contacts';
  import type { ContactCreateInput } from '$api/contacts';
  import DataList from '$components/data/DataList.svelte';
  import ContactCard from '$components/contacts/ContactCard.svelte';
  import Button from '$components/ui/Button.svelte';
  import Modal from '$components/ui/Modal.svelte';
  import Input from '$components/ui/Input.svelte';
  import { Plus, Users } from 'lucide-svelte';
  import type { Contact } from '$lib/types/models';

  const vaultId = $derived(page.params.vaultId!);

  let showCreate = $state(false);
  let createForm = $state<ContactCreateInput>({ first_name: '', last_name: '' });
  let creating = $state(false);
  let formError = $state('');
  let dataList: DataList<Contact>;

  async function loadContacts(params: { offset: number; limit: number; search: string; filter: string | null }) {
    return contactsApi.list(vaultId, {
      q: params.search || undefined,
      favorites: params.filter === 'favorite' ? true : undefined,
      offset: params.offset,
      limit: params.limit
    });
  }

  const filters = [{ label: 'Favorites', value: 'favorite' }];

  async function handleCreate(e: SubmitEvent) {
    e.preventDefault();
    if (!createForm.first_name.trim()) return;
    formError = '';
    creating = true;
    try {
      const contact = await contactsApi.create(vaultId, createForm);
      showCreate = false;
      createForm = { first_name: '', last_name: '' };
      goto(`/vaults/${vaultId}/contacts/${contact.id}`);
    } catch (err) {
      formError = err instanceof Error ? err.message : 'Something went wrong';
    } finally {
      creating = false;
    }
  }
</script>

<svelte:head><title>Contacts</title></svelte:head>

<div class="space-y-4">
  <DataList
    bind:this={dataList}
    load={loadContacts}
    {filters}
    searchPlaceholder="Search contacts..."
    emptyIcon={Users}
    emptyTitle="No contacts yet"
    emptyDescription="Add your first contact to get started"
  >
    {#snippet header()}
      <Button onclick={() => (showCreate = true)}>
        <Plus size={16} />
        Add Contact
      </Button>
    {/snippet}
    {#snippet row(item: Contact)}
      <ContactCard contact={item} href="/vaults/{vaultId}/contacts/{item.id}" />
    {/snippet}
  </DataList>
</div>

{#if showCreate}
  <Modal title="New Contact" onclose={() => (showCreate = false)}>
    <form onsubmit={handleCreate} class="space-y-4">
      <Input label="First name" bind:value={createForm.first_name} required />
      <Input label="Last name" bind:value={createForm.last_name} />
      <Input label="Nickname" bind:value={createForm.nickname} />
      {#if formError}<p class="text-sm text-red-400">{formError}</p>{/if}
      <div class="flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (showCreate = false)}>Cancel</Button>
        <Button type="submit" loading={creating}>Create</Button>
      </div>
    </form>
  </Modal>
{/if}
