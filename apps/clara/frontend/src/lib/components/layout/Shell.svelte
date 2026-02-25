<script lang="ts">
  import Sidebar from '$components/layout/Sidebar.svelte';
  import Topbar from '$components/layout/Topbar.svelte';
  import MobileNav from '$components/layout/MobileNav.svelte';
  import type { Snippet } from 'svelte';

  let { children }: { children: Snippet } = $props();

  let sidebarOpen = $state(false);
</script>

<div class="flex h-screen bg-neutral-950 text-white">
  <!-- Desktop sidebar -->
  <div class="hidden lg:flex">
    <Sidebar />
  </div>

  <!-- Mobile sidebar overlay -->
  {#if sidebarOpen}
    <div class="fixed inset-0 z-40 lg:hidden">
      <button
        class="absolute inset-0 bg-black/50"
        onclick={() => (sidebarOpen = false)}
        aria-label="Close sidebar"
      ></button>
      <div class="relative z-50 h-full w-64">
        <Sidebar onnavigate={() => (sidebarOpen = false)} />
      </div>
    </div>
  {/if}

  <!-- Main area -->
  <div class="flex flex-1 flex-col overflow-hidden">
    <Topbar ontogglesidebar={() => (sidebarOpen = !sidebarOpen)} />
    <main class="flex-1 overflow-y-auto p-4 pb-16 lg:p-6 lg:pb-6">
      {@render children()}
    </main>
  </div>

  <!-- Mobile bottom nav -->
  <div class="lg:hidden">
    <MobileNav />
  </div>
</div>
