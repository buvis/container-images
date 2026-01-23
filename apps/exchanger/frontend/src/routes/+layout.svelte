<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import Sidebar from '$lib/components/Sidebar.svelte';

	let { children } = $props();
	let isSidebarOpen = $state(false);
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="flex min-h-screen bg-[#0F172A] text-slate-100">
	<Sidebar bind:isOpen={isSidebarOpen} />

	<div class="flex-1 flex flex-col min-w-0">
		<!-- Mobile Header -->
		<header class="lg:hidden flex items-center h-16 px-4 border-b border-slate-800 bg-[#1E293B]">
			<button 
				onclick={() => isSidebarOpen = !isSidebarOpen} 
				class="text-white p-2 -ml-2 rounded-md hover:bg-slate-700/50"
				aria-label="Open sidebar"
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
				</svg>
			</button>
			<span class="ml-4 font-bold text-lg">Exchanger</span>
		</header>

		<main class="flex-1 p-4 lg:p-8">
			{@render children()}
		</main>
	</div>
</div>
