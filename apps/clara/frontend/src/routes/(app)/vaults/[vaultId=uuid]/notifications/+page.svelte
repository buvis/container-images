<script lang="ts">
  import { page } from '$app/state';
  import { notificationsApi } from '$api/notifications';
  import Spinner from '$components/ui/Spinner.svelte';
  import Button from '$components/ui/Button.svelte';
  import { Bell, CheckCheck, Mail, MailOpen, Trash2 } from 'lucide-svelte';
  import type { Notification } from '$lib/types/models';

  const vaultId = $derived(page.params.vaultId!);

  let notifications = $state<Notification[]>([]);
  let loading = $state(true);
  let markingAll = $state(false);
  let clearingRead = $state(false);

  $effect(() => {
    loading = true;
    notificationsApi.list(vaultId).then((n) => {
      notifications = n;
      loading = false;
    });
  });

  async function toggleRead(notif: Notification) {
    const updated = notif.read
      ? await notificationsApi.markUnread(vaultId, notif.id)
      : await notificationsApi.markRead(vaultId, notif.id);
    notifications = notifications.map((n) => (n.id === notif.id ? updated : n));
  }

  async function deleteNotification(notif: Notification) {
    await notificationsApi.delete(vaultId, notif.id);
    notifications = notifications.filter((n) => n.id !== notif.id);
  }

  async function markAllRead() {
    markingAll = true;
    try {
      await notificationsApi.markAllRead(vaultId);
      notifications = notifications.map((n) => ({ ...n, read: true }));
    } finally {
      markingAll = false;
    }
  }

  function formatDate(d: string): string {
    return new Date(d).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  }

  async function clearRead() {
    clearingRead = true;
    try {
      await notificationsApi.clearRead(vaultId);
      notifications = notifications.filter((n) => !n.read);
    } finally {
      clearingRead = false;
    }
  }

  const unreadCount = $derived(notifications.filter((n) => !n.read).length);
  const readCount = $derived(notifications.filter((n) => n.read).length);
</script>

<svelte:head>
  <title>Notifications</title>
</svelte:head>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-2xl font-semibold text-white">Notifications</h1>
      {#if !loading && unreadCount > 0}
        <p class="text-sm text-neutral-400">{unreadCount} unread</p>
      {/if}
    </div>
    <div class="flex items-center gap-2">
      {#if unreadCount > 0}
        <Button size="sm" variant="ghost" loading={markingAll} onclick={markAllRead}>
          <CheckCheck size={16} class="mr-1.5" />Mark all read
        </Button>
      {/if}
      {#if readCount > 0}
        <Button size="sm" variant="ghost" loading={clearingRead} onclick={clearRead}>
          <Trash2 size={16} class="mr-1.5" />Clear read
        </Button>
      {/if}
    </div>
  </div>

  {#if loading}
    <div class="flex justify-center py-12"><Spinner /></div>
  {:else if notifications.length === 0}
    <div class="flex flex-col items-center gap-3 py-16 text-neutral-500">
      <Bell size={40} strokeWidth={1.5} />
      <p class="text-sm">No notifications yet</p>
    </div>
  {:else}
    <div class="divide-y divide-neutral-800 rounded-xl border border-neutral-800">
      {#each notifications as notif (notif.id)}
        <div class="flex items-start gap-3 px-4 py-3 {notif.read ? 'opacity-60' : ''}">
          <div class="mt-0.5 shrink-0 text-neutral-500">
            {#if notif.read}
              <MailOpen size={16} />
            {:else}
              <Mail size={16} class="text-brand-400" />
            {/if}
          </div>
          <div class="min-w-0 flex-1">
            {#if notif.link}
              <a href={notif.link} class="text-sm font-medium text-white hover:text-brand-400">{notif.title}</a>
            {:else}
              <p class="text-sm font-medium text-white">{notif.title}</p>
            {/if}
            {#if notif.body}
              <p class="mt-0.5 line-clamp-2 text-xs text-neutral-400">{notif.body}</p>
            {/if}
            <span class="mt-1 block text-xs text-neutral-500">{formatDate(notif.created_at)}</span>
          </div>
          <button
            onclick={() => toggleRead(notif)}
            class="shrink-0 rounded p-1 text-neutral-500 transition hover:bg-neutral-800 hover:text-white"
            aria-label={notif.read ? 'Mark unread' : 'Mark read'}
          >
            {#if notif.read}
              <Mail size={14} />
            {:else}
              <MailOpen size={14} />
            {/if}
          </button>
          <button
            onclick={() => deleteNotification(notif)}
            class="shrink-0 rounded p-1 text-neutral-500 transition hover:bg-neutral-800 hover:text-red-400"
            aria-label="Delete notification"
          >
            <Trash2 size={14} />
          </button>
        </div>
      {/each}
    </div>
  {/if}
</div>
