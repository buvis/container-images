<script lang="ts">
  import { page } from '$app/state';
  import { vaultState } from '$state/vault.svelte';
  import type { FeatureFlags } from '$state/vault.svelte';
  import {
    Home,
    Users,
    CheckSquare,
    CalendarDays,
    BookOpen,
    Bell,
    StickyNote,
    Gift,
    DollarSign,
    FolderOpen,
    Settings
  } from 'lucide-svelte';

  let { onnavigate }: { onnavigate?: () => void } = $props();

  type NavItem = { label: string; icon: typeof Home; path: string; flag?: keyof FeatureFlags };

  const allNavItems: NavItem[] = [
    { label: 'Dashboard', icon: Home, path: 'dashboard' },
    { label: 'Contacts', icon: Users, path: 'contacts' },
    { label: 'Tasks', icon: CheckSquare, path: 'tasks' },
    { label: 'Activities', icon: CalendarDays, path: 'activities' },
    { label: 'Journal', icon: BookOpen, path: 'journal', flag: 'journal' },
    { label: 'Reminders', icon: Bell, path: 'reminders' },
    { label: 'Notes', icon: StickyNote, path: 'notes' },
    { label: 'Gifts', icon: Gift, path: 'gifts', flag: 'gifts' },
    { label: 'Debts', icon: DollarSign, path: 'debts', flag: 'debts' },
    { label: 'Files', icon: FolderOpen, path: 'files' },
    { label: 'Settings', icon: Settings, path: 'settings' }
  ];

  let navItems = $derived(
    allNavItems.filter((item) => !item.flag || vaultState.featureFlags[item.flag])
  );

  let basePath = $derived(
    vaultState.currentId ? `/vaults/${vaultState.currentId}` : ''
  );

  $effect(() => {
    const id = vaultState.currentId;
    if (id) vaultState.loadFeatureFlags(id);
  });

  function isActive(itemPath: string): boolean {
    return page.url.pathname.includes(`/${itemPath}`);
  }
</script>

<nav class="flex h-full w-64 flex-col border-r border-neutral-800 bg-neutral-900">
  <div class="flex h-14 items-center border-b border-neutral-800 px-4">
    <a href="/" class="text-lg font-bold tracking-tight text-white" onclick={onnavigate}>
      CLARA
    </a>
  </div>

  <div class="flex-1 overflow-y-auto py-3">
    <ul class="space-y-0.5 px-2">
      {#each navItems as item}
        {@const active = isActive(item.path)}
        <li>
          <a
            href="{basePath}/{item.path}"
            onclick={onnavigate}
            class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition
              {active
                ? 'bg-brand-500/10 text-brand-400 font-medium'
                : 'text-neutral-400 hover:bg-neutral-800 hover:text-white'}"
          >
            <item.icon size={18} />
            {item.label}
          </a>
        </li>
      {/each}
    </ul>
  </div>
</nav>
