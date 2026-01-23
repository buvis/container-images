<script lang="ts">
    import { page } from '$app/stores';
    
    let { isOpen = $bindable(false) } = $props();
    
    const navItems = [
        {
            section: 'Overview',
            items: [{ label: 'Dashboard', href: '/' }]
        },
        {
            section: 'Market Data',
            items: [{ label: 'Rates Explorer', href: '/rates' }]
        },
        {
            section: 'Operations',
            items: [{ label: 'Admin Panel', href: '/admin' }]
        },
        {
            section: 'System',
            items: [{ label: 'Providers', href: '/providers' }]
        }
    ];
</script>

<aside 
    class="fixed inset-y-0 left-0 z-50 w-64 bg-[#1E293B] border-r border-slate-700 text-white transition-transform duration-300 ease-in-out lg:static lg:translate-x-0 {isOpen ? 'translate-x-0' : '-translate-x-full'}"
>
    <!-- Sidebar Header -->
    <div class="flex h-16 items-center justify-between px-6 border-b border-slate-700">
        <span class="text-xl font-bold tracking-tight">Exchanger</span>
        <button class="lg:hidden p-1 rounded hover:bg-slate-700" onclick={() => isOpen = false} aria-label="Close sidebar">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
        </button>
    </div>

    <!-- Navigation -->
    <nav class="p-4 space-y-6 overflow-y-auto h-[calc(100vh-4rem)]">
        {#each navItems as group}
            <div>
                <h3 class="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                    {group.section}
                </h3>
                <ul class="space-y-1">
                    {#each group.items as item}
                        <li>
                            <a 
                                href={item.href}
                                class="block rounded-md px-2 py-2 text-sm font-medium transition-colors hover:bg-slate-700/50 hover:text-white {$page.url.pathname === item.href ? 'bg-slate-700 text-white' : 'text-slate-300'}"
                                onclick={() => isOpen = false} 
                            >
                                {item.label}
                            </a>
                        </li>
                    {/each}
                </ul>
            </div>
        {/each}
    </nav>
</aside>

<!-- Mobile Overlay -->
{#if isOpen}
    <div 
        class="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden transition-opacity duration-300"
        onclick={() => isOpen = false}
        role="button"
        tabindex="0"
        onkeydown={(e) => e.key === 'Enter' && (isOpen = false)}
        aria-label="Close sidebar"
    ></div>
{/if}
