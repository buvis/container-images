<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/state';
  import { notificationsApi } from '$api/notifications';
  import { auth } from '$state/auth.svelte';
  import { vaultState } from '$state/vault.svelte';
  import { Menu, LogOut, ChevronDown, Bell } from 'lucide-svelte';
  import type { Notification } from '$lib/types/models';

  let { ontogglesidebar }: { ontogglesidebar: () => void } = $props();

  const vaultId = $derived(vaultState.currentId ?? page.params.vaultId ?? '');

  let userMenuOpen = $state(false);
  let notificationsOpen = $state(false);
  let notifications = $state<Notification[]>([]);
  let unreadCount = $state(0);

  async function handleLogout() {
    await auth.logout();
    goto('/auth/login');
  }

  function handleVaultChange(e: Event) {
    const select = e.target as HTMLSelectElement;
    const vault = vaultState.vaults.find((v) => v.id === select.value);
    if (vault) {
      vaultState.setCurrent(vault);
      goto(`/vaults/${vault.id}/dashboard`);
    }
  }

  async function loadNotifications() {
    if (!vaultId) return;
    notifications = await notificationsApi.list(vaultId);
    const unread = await notificationsApi.unreadCount(vaultId);
    unreadCount = unread.count;
  }

  async function handleNotificationClick(notification: Notification) {
    if (!vaultId) return;
    if (!notification.read) {
      await notificationsApi.markRead(vaultId, notification.id);
      await loadNotifications();
    }
    notificationsOpen = false;
    if (notification.link) goto(notification.link);
  }

  async function handleMarkAllRead() {
    if (!vaultId) return;
    await notificationsApi.markAllRead(vaultId);
    await loadNotifications();
  }

  function formatDate(value: string): string {
    return new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  }

  $effect(() => {
    if (!vaultId) return;
    loadNotifications();
  });
</script>

<header class="flex h-14 shrink-0 items-center justify-between border-b border-neutral-800 bg-neutral-900 px-4">
  <div class="flex items-center gap-3">
    <button
      class="rounded-lg p-1.5 text-neutral-400 hover:bg-neutral-800 hover:text-white lg:hidden"
      onclick={ontogglesidebar}
      aria-label="Toggle sidebar"
    >
      <Menu size={20} />
    </button>

    {#if vaultState.vaults.length > 0}
      <div class="relative">
        <select
          value={vaultState.currentId ?? ''}
          onchange={handleVaultChange}
          class="appearance-none rounded-lg border border-neutral-700 bg-neutral-800 py-1.5 pl-3 pr-8 text-sm text-white outline-none transition focus:border-brand-500"
        >
          {#each vaultState.vaults as vault}
            <option value={vault.id}>{vault.name}</option>
          {/each}
        </select>
        <ChevronDown
          size={14}
          class="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-neutral-400"
        />
      </div>
    {/if}
  </div>

  <div class="flex items-center gap-2">
    <div class="relative">
      <button
        onclick={() => {
          notificationsOpen = !notificationsOpen;
          userMenuOpen = false;
        }}
        class="relative rounded-lg p-2 text-neutral-400 transition hover:bg-neutral-800 hover:text-white"
        aria-label="Notifications"
      >
        <Bell size={18} />
        {#if unreadCount > 0}
          <span class="absolute -right-1 -top-1 min-w-4 rounded-full bg-brand-500 px-1 text-center text-[10px] font-medium text-white">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        {/if}
      </button>

      {#if notificationsOpen}
        <button
          class="fixed inset-0 z-40"
          onclick={() => (notificationsOpen = false)}
          aria-label="Close notifications"
        ></button>
        <div class="absolute right-0 z-50 mt-1 w-80 rounded-lg border border-neutral-700 bg-neutral-800 shadow-xl">
          <div class="flex items-center justify-between border-b border-neutral-700 px-3 py-2">
            <p class="text-sm font-medium text-white">Notifications</p>
            <button
              class="text-xs text-brand-400 hover:text-brand-300"
              onclick={handleMarkAllRead}
            >
              Mark all read
            </button>
          </div>
          <div class="max-h-80 overflow-y-auto">
            {#if notifications.length === 0}
              <p class="px-3 py-4 text-sm text-neutral-500">No notifications</p>
            {:else}
              {#each notifications.slice(0, 8) as notification}
                <button
                  class="block w-full border-b border-neutral-700 px-3 py-2 text-left transition hover:bg-neutral-700/50"
                  onclick={() => handleNotificationClick(notification)}
                >
                  <div class="flex items-start justify-between gap-2">
                    <p class="text-sm {notification.read ? 'text-neutral-300' : 'font-medium text-white'}">
                      {notification.title}
                    </p>
                    <span class="shrink-0 text-xs text-neutral-500">{formatDate(notification.created_at)}</span>
                  </div>
                  <p class="mt-1 line-clamp-2 text-xs text-neutral-500">{notification.body}</p>
                </button>
              {/each}
            {/if}
          </div>
          {#if vaultId}
            <a
              href="/vaults/{vaultId}/notifications"
              onclick={() => (notificationsOpen = false)}
              class="block border-t border-neutral-700 px-3 py-2 text-center text-xs text-brand-400 transition hover:bg-neutral-700/50 hover:text-brand-300"
            >
              View all notifications
            </a>
          {/if}
        </div>
      {/if}
    </div>

    <div class="relative">
      <button
        onclick={() => {
          userMenuOpen = !userMenuOpen;
          notificationsOpen = false;
        }}
        class="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm text-neutral-300 transition hover:bg-neutral-800 hover:text-white"
      >
        <span class="flex h-7 w-7 items-center justify-center rounded-full bg-brand-500/20 text-xs font-medium text-brand-400">
          {auth.user?.name?.charAt(0).toUpperCase() ?? '?'}
        </span>
        <span class="hidden sm:inline">{auth.user?.name ?? 'User'}</span>
        <ChevronDown size={14} />
      </button>

      {#if userMenuOpen}
        <button
          class="fixed inset-0 z-40"
          onclick={() => (userMenuOpen = false)}
          aria-label="Close menu"
        ></button>
        <div class="absolute right-0 z-50 mt-1 w-48 rounded-lg border border-neutral-700 bg-neutral-800 py-1 shadow-xl">
          <div class="border-b border-neutral-700 px-3 py-2">
            <p class="text-sm text-white">{auth.user?.name}</p>
            <p class="text-xs text-neutral-400">{auth.user?.email}</p>
          </div>
          <button
            onclick={handleLogout}
            class="flex w-full items-center gap-2 px-3 py-2 text-sm text-neutral-300 transition hover:bg-neutral-700 hover:text-white"
          >
            <LogOut size={14} />
            Sign out
          </button>
        </div>
      {/if}
    </div>
  </div>
</header>
