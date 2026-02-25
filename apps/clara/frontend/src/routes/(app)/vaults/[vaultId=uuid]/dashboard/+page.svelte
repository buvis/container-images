<script lang="ts">
  import { page } from '$app/state';
  import { dashboardApi } from '$api/dashboard';
  import Spinner from '$components/ui/Spinner.svelte';
  import Badge from '$components/ui/Badge.svelte';
  import { Bell, CheckSquare, Users, ChevronRight } from 'lucide-svelte';
  import type { Reminder, Activity, Task, Contact } from '$lib/types/models';

  const vaultId = $derived(page.params.vaultId!);

  let reminders = $state<Reminder[]>([]);
  let activities = $state<Activity[]>([]);
  let overdueTasks = $state<Task[]>([]);
  let contacts = $state<Contact[]>([]);

  let loadingReminders = $state(true);
  let loadingActivities = $state(true);
  let loadingTasks = $state(true);
  let loadingContacts = $state(true);

  $effect(() => {
    dashboardApi.upcomingReminders(vaultId).then((res) => {
      reminders = res.items;
      loadingReminders = false;
    });
    dashboardApi.recentActivities(vaultId).then((res) => {
      activities = res.items;
      loadingActivities = false;
    });
    dashboardApi.overdueTasks(vaultId).then((res) => {
      overdueTasks = res.items;
      loadingTasks = false;
    });
    dashboardApi.recentContacts(vaultId).then((res) => {
      contacts = res.items;
      loadingContacts = false;
    });
  });

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric'
    });
  }
</script>

<svelte:head>
  <title>Dashboard</title>
</svelte:head>

<div class="space-y-6">
  <h1 class="text-2xl font-semibold text-white">Dashboard</h1>

  <div class="grid gap-6 md:grid-cols-2">
    <!-- Upcoming Reminders -->
    <div class="rounded-xl border border-neutral-800 bg-neutral-900 p-5">
      <div class="mb-4 flex items-center gap-2 text-neutral-300">
        <Bell size={20} class="text-brand-400" />
        <h2 class="font-medium">Upcoming Reminders</h2>
      </div>

      {#if loadingReminders}
        <div class="flex justify-center py-4"><Spinner /></div>
      {:else if reminders.length === 0}
        <p class="text-sm text-neutral-500">No upcoming reminders</p>
      {:else}
        <ul class="space-y-3">
          {#each reminders as reminder}
            <li class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="truncate text-sm font-medium text-white">{reminder.title}</p>
                {#if reminder.description}
                  <p class="truncate text-xs text-neutral-500">{reminder.description}</p>
                {/if}
              </div>
              <Badge text={formatDate(reminder.next_expected_date)} />
            </li>
          {/each}
        </ul>
      {/if}

      <a
        href="/vaults/{vaultId}/reminders"
        class="mt-4 flex items-center gap-1 text-xs font-medium text-brand-400 hover:text-brand-300"
      >
        View all <ChevronRight size={12} />
      </a>
    </div>

    <!-- Overdue Tasks -->
    <div class="rounded-xl border border-neutral-800 bg-neutral-900 p-5">
      <div class="mb-4 flex items-center gap-2 text-neutral-300">
        <CheckSquare size={20} class="text-red-400" />
        <h2 class="font-medium">Overdue Tasks</h2>
        {#if overdueTasks.length > 0}
          <Badge variant="danger" text={String(overdueTasks.length)} />
        {/if}
      </div>

      {#if loadingTasks}
        <div class="flex justify-center py-4"><Spinner /></div>
      {:else if overdueTasks.length === 0}
        <p class="text-sm text-neutral-500">No overdue tasks</p>
      {:else}
        <ul class="space-y-3">
          {#each overdueTasks as task}
            <li class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="truncate text-sm font-medium text-white">{task.title}</p>
                {#if task.due_date}
                  <p class="text-xs text-red-400">Due {formatDate(task.due_date)}</p>
                {/if}
              </div>
              <Badge variant={task.priority >= 2 ? 'danger' : 'default'} text="P{task.priority}" />
            </li>
          {/each}
        </ul>
      {/if}

      <a
        href="/vaults/{vaultId}/tasks"
        class="mt-4 flex items-center gap-1 text-xs font-medium text-brand-400 hover:text-brand-300"
      >
        View all <ChevronRight size={12} />
      </a>
    </div>

    <!-- Recent Activities -->
    <div class="rounded-xl border border-neutral-800 bg-neutral-900 p-5">
      <div class="mb-4 flex items-center gap-2 text-neutral-300">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-brand-400"><path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/></svg>
        <h2 class="font-medium">Recent Activities</h2>
      </div>

      {#if loadingActivities}
        <div class="flex justify-center py-4"><Spinner /></div>
      {:else if activities.length === 0}
        <p class="text-sm text-neutral-500">No recent activities</p>
      {:else}
        <ul class="space-y-3">
          {#each activities as activity}
            <li class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="truncate text-sm font-medium text-white">{activity.title}</p>
                {#if activity.location}
                  <p class="truncate text-xs text-neutral-500">{activity.location}</p>
                {/if}
              </div>
              <span class="shrink-0 text-xs text-neutral-500">{formatDate(activity.happened_at)}</span>
            </li>
          {/each}
        </ul>
      {/if}

      <a
        href="/vaults/{vaultId}/activities"
        class="mt-4 flex items-center gap-1 text-xs font-medium text-brand-400 hover:text-brand-300"
      >
        View all <ChevronRight size={12} />
      </a>
    </div>

    <!-- Recent Contacts -->
    <div class="rounded-xl border border-neutral-800 bg-neutral-900 p-5">
      <div class="mb-4 flex items-center gap-2 text-neutral-300">
        <Users size={20} class="text-amber-400" />
        <h2 class="font-medium">Contacts</h2>
      </div>

      {#if loadingContacts}
        <div class="flex justify-center py-4"><Spinner /></div>
      {:else if contacts.length === 0}
        <p class="text-sm text-neutral-500">No contacts yet</p>
      {:else}
        <ul class="space-y-3">
          {#each contacts as contact}
            <li>
              <a
                href="/vaults/{vaultId}/contacts/{contact.id}"
                class="flex items-center gap-3 rounded-lg p-1 hover:bg-neutral-800"
              >
                <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-500/20 text-xs font-semibold text-brand-400">
                  {contact.first_name[0]}{contact.last_name?.[0] ?? ''}
                </div>
                <span class="truncate text-sm text-white">
                  {contact.first_name} {contact.last_name}
                </span>
              </a>
            </li>
          {/each}
        </ul>
      {/if}

      <a
        href="/vaults/{vaultId}/contacts"
        class="mt-4 flex items-center gap-1 text-xs font-medium text-brand-400 hover:text-brand-300"
      >
        View all <ChevronRight size={12} />
      </a>
    </div>
  </div>
</div>
