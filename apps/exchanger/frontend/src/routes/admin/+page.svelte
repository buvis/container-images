<script lang="ts">
    import { onMount } from 'svelte';
    import { 
        triggerBackfill, 
        populateSymbols, 
        getBackups, 
        createBackup, 
        restoreBackup,
        getTaskStatus
    } from '$lib/api';
    import type { TaskState } from '$lib/api';

    let activeTab: 'backfill' | 'symbols' | 'backups' = 'backfill';
    
    // Backfill state
    let backfillProvider = 'cnb';
    let backfillLength = 30;
    let backfillSymbols = '';
    let backfillMessage = '';
    let backfillError = '';
    let taskStatuses: TaskState[] = [];

    // Symbols state
    let symbolsProvider = 'cnb';
    let symbolsMessage = '';
    let symbolsError = '';

    // Backups state
    let backups: string[] = [];
    let selectedBackup = '';
    let backupMessage = '';
    let backupError = '';

    // Data fetching
    async function loadTaskStatus() {
        try {
            taskStatuses = await getTaskStatus();
        } catch (e) {
            console.error(e);
        }
    }

    async function loadBackups() {
        try {
            backups = await getBackups();
            if (backups.length > 0 && !selectedBackup) {
                selectedBackup = backups[0];
            }
        } catch (e) {
            console.error(e);
            backupError = 'Failed to load backups';
        }
    }

    // Handlers
    async function handleBackfill() {
        backfillMessage = '';
        backfillError = '';
        try {
            const symbolsList = backfillSymbols 
                ? backfillSymbols.split(',').map(s => s.trim()).filter(s => s)
                : undefined;
            
            await triggerBackfill(backfillProvider, backfillLength, symbolsList);
            backfillMessage = 'Backfill triggered successfully';
            await loadTaskStatus();
        } catch (e: any) {
            backfillError = e.message || 'Failed to trigger backfill';
        }
    }

    async function handlePopulateSymbols() {
        symbolsMessage = '';
        symbolsError = '';
        try {
            await populateSymbols(symbolsProvider);
            symbolsMessage = 'Symbol population triggered successfully';
        } catch (e: any) {
            symbolsError = e.message || 'Failed to populate symbols';
        }
    }

    async function handleCreateBackup() {
        backupMessage = '';
        backupError = '';
        try {
            const result = await createBackup();
            backupMessage = `Backup created: ${result.filename}`;
            await loadBackups();
        } catch (e: any) {
            backupError = e.message || 'Failed to create backup';
        }
    }

    async function handleRestoreBackup() {
        if (!selectedBackup) return;
        backupMessage = '';
        backupError = '';
        try {
            await restoreBackup(selectedBackup);
            backupMessage = `Restore triggered for ${selectedBackup}`;
        } catch (e: any) {
            backupError = e.message || 'Failed to restore backup';
        }
    }

    // React to tab changes
    $: if (activeTab === 'backups') loadBackups();
    $: if (activeTab === 'backfill') loadTaskStatus();
</script>

<div class="min-h-screen bg-[#0F172A] text-slate-200 p-8 font-sans">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-3xl font-bold mb-8 text-white">Admin Panel</h1>

        <!-- Tabs -->
        <div class="flex space-x-1 mb-6 border-b border-slate-700">
            <button 
                class="px-4 py-2 rounded-t-lg transition-colors {activeTab === 'backfill' ? 'bg-[#1E293B] text-white border-t border-x border-slate-600' : 'hover:bg-[#1E293B]/50 text-slate-400'}"
                on:click={() => activeTab = 'backfill'}
            >
                Backfill
            </button>
            <button 
                class="px-4 py-2 rounded-t-lg transition-colors {activeTab === 'symbols' ? 'bg-[#1E293B] text-white border-t border-x border-slate-600' : 'hover:bg-[#1E293B]/50 text-slate-400'}"
                on:click={() => activeTab = 'symbols'}
            >
                Symbols
            </button>
            <button 
                class="px-4 py-2 rounded-t-lg transition-colors {activeTab === 'backups' ? 'bg-[#1E293B] text-white border-t border-x border-slate-600' : 'hover:bg-[#1E293B]/50 text-slate-400'}"
                on:click={() => activeTab = 'backups'}
            >
                Backups
            </button>
        </div>

        <!-- Content -->
        <div class="bg-[#1E293B] p-6 rounded-b-lg rounded-tr-lg shadow-xl border border-slate-700">
            
            <!-- Backfill Tab -->
            {#if activeTab === 'backfill'}
                <div class="space-y-6">
                    <h2 class="text-xl font-semibold text-white">Trigger Backfill</h2>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="space-y-2">
                            <label class="block text-sm font-medium text-slate-300">Provider</label>
                            <select bind:value={backfillProvider} class="w-full bg-[#0F172A] border border-slate-600 rounded p-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none">
                                <option value="cnb">CNB</option>
                                <option value="fcs">FCS</option>
                            </select>
                        </div>

                        <div class="space-y-2">
                            <label class="block text-sm font-medium text-slate-300">Length (days)</label>
                            <input 
                                type="number" 
                                min="1" 
                                max="365" 
                                bind:value={backfillLength} 
                                class="w-full bg-[#0F172A] border border-slate-600 rounded p-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                            />
                        </div>

                        <div class="col-span-1 md:col-span-2 space-y-2">
                            <label class="block text-sm font-medium text-slate-300">Symbols (comma separated, optional)</label>
                            <input 
                                type="text" 
                                placeholder="EUR, USD, GBP"
                                bind:value={backfillSymbols} 
                                class="w-full bg-[#0F172A] border border-slate-600 rounded p-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                            />
                        </div>
                    </div>

                    <button 
                        on:click={handleBackfill}
                        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition-colors"
                    >
                        Trigger Backfill
                    </button>

                    {#if backfillMessage}
                        <div class="p-3 bg-green-900/30 text-green-400 rounded border border-green-900">{backfillMessage}</div>
                    {/if}
                    {#if backfillError}
                        <div class="p-3 bg-red-900/30 text-red-400 rounded border border-red-900">{backfillError}</div>
                    {/if}

                    {#if taskStatuses.length > 0}
                        <div class="mt-8">
                            <h3 class="text-lg font-medium text-white mb-4">Task Status</h3>
                            <div class="overflow-x-auto">
                                <table class="w-full text-left border-collapse">
                                    <thead>
                                        <tr class="border-b border-slate-600">
                                            <th class="p-2 text-slate-400">Name</th>
                                            <th class="p-2 text-slate-400">Status</th>
                                            <th class="p-2 text-slate-400">Last Run</th>
                                            <th class="p-2 text-slate-400">Next Run</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {#each taskStatuses as task}
                                            <tr class="border-b border-slate-700/50 hover:bg-[#0F172A]/30">
                                                <td class="p-2">{task.name}</td>
                                                <td class="p-2">
                                                    <span class="px-2 py-1 rounded text-xs {task.status === 'running' ? 'bg-blue-900 text-blue-300' : 'bg-slate-700 text-slate-300'}">
                                                        {task.status}
                                                    </span>
                                                </td>
                                                <td class="p-2 text-sm text-slate-400">{task.last_run || '-'}</td>
                                                <td class="p-2 text-sm text-slate-400">{task.next_run || '-'}</td>
                                            </tr>
                                        {/each}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    {/if}
                </div>
            {/if}

            <!-- Symbols Tab -->
            {#if activeTab === 'symbols'}
                <div class="space-y-6">
                    <h2 class="text-xl font-semibold text-white">Populate Symbols</h2>
                    
                    <div class="space-y-2 max-w-md">
                        <label class="block text-sm font-medium text-slate-300">Provider</label>
                        <select bind:value={symbolsProvider} class="w-full bg-[#0F172A] border border-slate-600 rounded p-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none">
                            <option value="cnb">CNB</option>
                            <option value="fcs">FCS</option>
                        </select>
                    </div>

                    <button 
                        on:click={handlePopulateSymbols}
                        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition-colors"
                    >
                        Populate Symbols
                    </button>

                    {#if symbolsMessage}
                        <div class="p-3 bg-green-900/30 text-green-400 rounded border border-green-900">{symbolsMessage}</div>
                    {/if}
                    {#if symbolsError}
                        <div class="p-3 bg-red-900/30 text-red-400 rounded border border-red-900">{symbolsError}</div>
                    {/if}
                </div>
            {/if}

            <!-- Backups Tab -->
            {#if activeTab === 'backups'}
                <div class="space-y-6">
                    <h2 class="text-xl font-semibold text-white">Manage Backups</h2>
                    
                    <div class="bg-[#0F172A] p-4 rounded border border-slate-600">
                        <h3 class="text-lg font-medium text-white mb-4">Create Backup</h3>
                        <button 
                            on:click={handleCreateBackup}
                            class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded font-medium transition-colors"
                        >
                            Create New Backup
                        </button>
                    </div>

                    <div class="bg-[#0F172A] p-4 rounded border border-slate-600">
                        <h3 class="text-lg font-medium text-white mb-4">Restore Backup</h3>
                        <div class="flex gap-4">
                            <select bind:value={selectedBackup} class="flex-1 bg-[#1E293B] border border-slate-600 rounded p-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none">
                                {#if backups.length === 0}
                                    <option value="" disabled>No backups available</option>
                                {:else}
                                    {#each backups as backup}
                                        <option value={backup}>{backup}</option>
                                    {/each}
                                {/if}
                            </select>
                            <button 
                                on:click={handleRestoreBackup}
                                disabled={!selectedBackup}
                                class="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded font-medium transition-colors"
                            >
                                Restore
                            </button>
                        </div>
                    </div>

                    {#if backupMessage}
                        <div class="p-3 bg-green-900/30 text-green-400 rounded border border-green-900">{backupMessage}</div>
                    {/if}
                    {#if backupError}
                        <div class="p-3 bg-red-900/30 text-red-400 rounded border border-red-900">{backupError}</div>
                    {/if}

                    <div class="mt-4">
                        <h3 class="text-sm font-medium text-slate-400 mb-2">Available Backups</h3>
                        <ul class="space-y-1 text-sm text-slate-300">
                            {#each backups as backup}
                                <li class="p-2 hover:bg-[#0F172A] rounded">{backup}</li>
                            {/each}
                        </ul>
                    </div>
                </div>
            {/if}

        </div>
    </div>
</div>
