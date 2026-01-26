<script lang="ts">
    import { onMount } from 'svelte';
    import { browser } from '$app/environment';
    import { page } from '$app/stores';
    import {
        triggerBackfill,
        populateSymbols,
        getBackups,
        createBackup,
        restoreBackup,
        getTaskStatus,
        getSymbols
    } from '$lib/api';
    import { formatDateTime } from '$lib/formatters';
    import type { TaskState, BackupInfo, SymbolItem } from '$lib/api';

    $: activeTab = (['backfill', 'symbols', 'backups'].includes($page.url.searchParams.get('tab') || '')
        ? $page.url.searchParams.get('tab')
        : 'backfill') as 'backfill' | 'symbols' | 'backups';
    
    // Backfill state
    let backfillProvider = 'cnb';
    let backfillLength = 30;
    // let backfillSymbols = ''; // Replaced by multi-select
    let availableSymbols: SymbolItem[] = [];
    let selectedBackfillSymbols: SymbolItem[] = [];
    let symbolSearchTerm = '';
    let isSymbolDropdownOpen = false;

    let backfillMessage = '';
    let backfillError = '';
    let taskStatuses: TaskState[] = [];

    // Symbols state
    let symbolsProvider = 'cnb';
    let symbolsMessage = '';
    let symbolsError = '';

    // Backups state
    let backups: BackupInfo[] = [];
    let selectedBackup: BackupInfo | null = null;
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

    async function loadSymbols() {
        try {
            availableSymbols = await getSymbols();
        } catch (e) {
            console.error(e);
        }
    }

    async function loadBackups() {
        try {
            const newBackups = await getBackups();
            // Preserve selection by finding matching filename
            if (selectedBackup) {
                const found = newBackups.find(b => b.filename === selectedBackup?.filename);
                selectedBackup = found || (newBackups.length > 0 ? newBackups[0] : null);
            } else if (newBackups.length > 0) {
                selectedBackup = newBackups[0];
            } else {
                selectedBackup = null;
            }
            backups = newBackups;
        } catch (e) {
            console.error(e);
            backupError = 'Failed to load backups';
        }
    }

    // Handlers
    function selectSymbol(symbol: SymbolItem) {
        if (!selectedBackfillSymbols.find(s => s.provider_symbol === symbol.provider_symbol)) {
            selectedBackfillSymbols = [...selectedBackfillSymbols, symbol];
        }
        symbolSearchTerm = '';
        // Keep dropdown open for more selections
        isSymbolDropdownOpen = true;
    }

    function removeSymbol(symbol: SymbolItem) {
        selectedBackfillSymbols = selectedBackfillSymbols.filter(s => s.provider_symbol !== symbol.provider_symbol);
    }

    async function handleBackfill() {
        backfillMessage = '';
        backfillError = '';
        try {
            const symbolsList = selectedBackfillSymbols.length > 0
                ? selectedBackfillSymbols.map(s => s.provider_symbol)
                : undefined;

            const result = await triggerBackfill(backfillProvider, Number(backfillLength), symbolsList);
            if (result.scheduled) {
                backfillMessage = result.message;
            } else {
                backfillError = result.message;
            }
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
            await restoreBackup(selectedBackup.timestamp);
            backupMessage = `Restore triggered for ${selectedBackup.filename}`;
        } catch (e: any) {
            backupError = e.message || 'Failed to restore backup';
        }
    }

    // React to tab changes (browser guard prevents SSR fetch errors)
    $: if (browser && activeTab === 'backups') loadBackups();
    $: if (browser && activeTab === 'backfill') {
        loadTaskStatus();
        if (availableSymbols.length === 0) loadSymbols();
    }

    // Reactive filtering - show up to 50 items, filter by search term
    $: currentProviderSymbols = availableSymbols.filter(s => s.provider === backfillProvider);
    $: filteredSymbols = currentProviderSymbols
        .filter(s => {
            const term = symbolSearchTerm.toLowerCase();
            const matchesSearch = s.provider_symbol.toLowerCase().includes(term) || s.name.toLowerCase().includes(term);
            const notSelected = !selectedBackfillSymbols.find(sel => sel.provider_symbol === s.provider_symbol);
            return matchesSearch && notSelected;
        })
        .slice(0, 50);

    // Clear selection on provider change
    let previousProvider = backfillProvider;
    $: if (backfillProvider !== previousProvider) {
        selectedBackfillSymbols = [];
        previousProvider = backfillProvider;
    }
</script>

<div class="bg-slate-950 text-slate-200 p-6">
    <header class="mb-8">
        <h1 class="text-3xl font-bold text-white">{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}</h1>
    </header>

    <div class="max-w-4xl mx-auto">
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-6">
            
            <!-- Backfill Tab -->
            {#if activeTab === 'backfill'}
                <div class="space-y-6">
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="space-y-2">
                            <label for="backfill-provider" class="block text-sm font-medium text-slate-300">Provider</label>
                            <select id="backfill-provider" bind:value={backfillProvider} class="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none">
                                <option value="cnb">CNB</option>
                                <option value="fcs">FCS</option>
                            </select>
                        </div>

                        <div class="space-y-2">
                            <label for="backfill-length" class="block text-sm font-medium text-slate-300">Length (days)</label>
                            <input
                                id="backfill-length"
                                type="number"
                                min="1"
                                max="3650"
                                bind:value={backfillLength}
                                class="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                            />
                        </div>

                        <div class="col-span-1 md:col-span-2 space-y-2 relative">
                            <label for="backfill-symbols" class="block text-sm font-medium text-slate-300">Symbols (optional)</label>
                            
                            <!-- Multi-select container -->
                            <div class="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white min-h-[42px] relative focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent">
                                <div class="flex flex-wrap gap-2">
                                    {#each selectedBackfillSymbols as symbol}
                                        <span class="bg-blue-900/50 border border-blue-700 text-blue-200 px-2 py-0.5 rounded text-sm flex items-center gap-1">
                                            {symbol.provider_symbol}
                                            <button
                                                on:click|stopPropagation={() => removeSymbol(symbol)}
                                                class="hover:text-white ml-1 text-blue-400 font-bold leading-none"
                                            >
                                                &times;
                                            </button>
                                        </span>
                                    {/each}
                                    
                                    <input
                                        id="backfill-symbols"
                                        type="text"
                                        placeholder={selectedBackfillSymbols.length > 0 ? "" : "Search symbols..."}
                                        bind:value={symbolSearchTerm}
                                        on:focus={() => isSymbolDropdownOpen = true}
                                        on:blur={() => setTimeout(() => isSymbolDropdownOpen = false, 200)}
                                        class="bg-transparent border-none outline-none flex-1 min-w-[120px] text-white placeholder-slate-500 text-sm py-1"
                                    />
                                </div>
                            </div>

                            <!-- Dropdown -->
                            {#if isSymbolDropdownOpen}
                                <div class="absolute top-full left-0 w-full bg-slate-900 border border-slate-700 rounded-b mt-1 max-h-60 overflow-y-auto z-50 shadow-xl">
                                    {#if filteredSymbols.length > 0}
                                        {#each filteredSymbols as symbol}
                                            <button
                                                class="w-full text-left px-3 py-2 hover:bg-slate-800 text-slate-200 text-sm transition-colors"
                                                on:mousedown|preventDefault={() => selectSymbol(symbol)}
                                            >
                                                <div class="flex justify-between items-center">
                                                    <span class="font-medium">{symbol.provider_symbol}</span>
                                                    <span class="text-slate-500 text-xs truncate ml-2">{symbol.name}</span>
                                                </div>
                                            </button>
                                        {/each}
                                        {#if currentProviderSymbols.length > 50 && !symbolSearchTerm}
                                            <div class="px-3 py-2 text-slate-500 text-xs border-t border-slate-700">Type to filter {currentProviderSymbols.length - selectedBackfillSymbols.length} symbols</div>
                                        {/if}
                                    {:else}
                                        <div class="px-3 py-2 text-slate-500 text-sm">No matching symbols</div>
                                    {/if}
                                </div>
                            {/if}
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
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {#each taskStatuses as task}
                                            <tr class="border-b border-slate-700/50 hover:bg-slate-800/30">
                                                <td class="p-2">{task.name}</td>
                                                <td class="p-2">
                                                    <span class="px-2 py-1 rounded text-xs {task.status === 'running' ? 'bg-blue-900 text-blue-300' : 'bg-slate-700 text-slate-300'}">
                                                        {task.status}
                                                    </span>
                                                </td>
                                                <td class="p-2 text-sm text-slate-400">{formatDateTime(task.last_run) || '-'}</td>
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
                    
                    <div class="space-y-2 max-w-md">
                        <label for="symbols-provider" class="block text-sm font-medium text-slate-300">Provider</label>
                        <select id="symbols-provider" bind:value={symbolsProvider} class="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none">
                            <option value="cnb">CNB</option>
                            <option value="fcs">FCS</option>
                        </select>
                    </div>

                    <button
                        on:click={handlePopulateSymbols}
                        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition-colors"
                    >
                        Refresh Symbols
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
                    
                    <div class="bg-slate-800 p-4 rounded border border-slate-700">
                        <h3 class="text-lg font-medium text-white mb-4">Create</h3>
                        <button 
                            on:click={handleCreateBackup}
                            class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded font-medium transition-colors"
                        >
                            Create New Backup
                        </button>
                    </div>

                    <div class="bg-slate-800 p-4 rounded border border-slate-700">
                        <h3 class="text-lg font-medium text-white mb-4">Restore</h3>
                        <div class="flex gap-4">
                            <select bind:value={selectedBackup} class="flex-1 bg-slate-900 border border-slate-700 rounded p-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none">
                                {#if backups.length === 0}
                                    <option value={null} disabled>No backups available</option>
                                {:else}
                                    {#each backups as backup}
                                        <option value={backup}>
                                            {backup.filename} ({formatDateTime(backup.timestamp)})
                                        </option>
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
                                <li class="p-2 hover:bg-slate-800 rounded flex justify-between items-center">
                                    <span>{backup.filename}</span>
                                    <span class="text-xs text-slate-500">{formatDateTime(backup.timestamp)}</span>
                                </li>
                            {/each}
                        </ul>
                    </div>
                </div>
        {/if}
        </div>
    </div>
</div>
