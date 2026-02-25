<script lang="ts">
  import { page } from '$app/state';
  import { vaultState } from '$state/vault.svelte';
  import type { FeatureFlags } from '$state/vault.svelte';
  import { Home, Users, CheckSquare, BookOpen, Bell } from 'lucide-svelte';

  type NavItem = { label: string; icon: typeof Home; path: string; flag?: keyof FeatureFlags };

  const allItems: NavItem[] = [
    { label: 'Home', icon: Home, path: 'dashboard' },
    { label: 'Contacts', icon: Users, path: 'contacts' },
    { label: 'Tasks', icon: CheckSquare, path: 'tasks' },
    { label: 'Journal', icon: BookOpen, path: 'journal', flag: 'journal' },
    { label: 'Reminders', icon: Bell, path: 'reminders' }
  ];

  let items = $derived(
    allItems.filter((item) => !item.flag || vaultState.featureFlags[item.flag])
  );

  let basePath = $derived(
    vaultState.currentId ? `/vaults/${vaultState.currentId}` : ''
  );

  function isActive(itemPath: string): boolean {
    return page.url.pathname.includes(`/${itemPath}`);
  }
</script>

<nav class="fixed inset-x-0 bottom-0 z-30 border-t border-neutral-800 bg-neutral-900" style="padding-bottom: env(safe-area-inset-bottom, 0px)">
  <div class="flex items-center justify-around py-2">
    {#each items as item}
      {@const active = isActive(item.path)}
      <a
        href="{basePath}/{item.path}"
        class="flex flex-col items-center gap-0.5 px-3 py-1 text-xs transition
          {active ? 'text-brand-400' : 'text-neutral-500 hover:text-neutral-300'}"
      >
        <item.icon size={20} />
        <span>{item.label}</span>
      </a>
    {/each}
  </div>
</nav>
