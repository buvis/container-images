<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { getTaskStatus, type TaskState } from '$lib/api';

  let tasks: TaskState[] = [];
  let interval: any;
  let loading = true;

  const stages = ['Queued', 'Fetching', 'Processing', 'Done'];

  function getStageIndex(status: string): number {
    const s = status.toLowerCase();
    if (s.includes('queue')) return 0;
    if (s.includes('fetch')) return 1;
    if (s.includes('process')) return 2;
    if (s === 'success' || s === 'done' || s === 'completed') return 3;
    return -1;
  }

  async function fetchTasks() {
    try {
      tasks = await getTaskStatus();
    } catch (e) {
      console.error(e);
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    fetchTasks();
    interval = setInterval(fetchTasks, 5000);
  });

  onDestroy(() => {
    if (interval) clearInterval(interval);
  });
</script>

<div class="bg-slate-800 p-4 rounded-lg shadow-lg border border-slate-700">
  <h2 class="text-xl font-bold mb-4 text-white">Task Pipeline</h2>
  
  {#if loading && tasks.length === 0}
    <div class="animate-pulse space-y-4">
      {#each Array(3) as _}
        <div class="h-12 bg-slate-700 rounded"></div>
      {/each}
    </div>
  {:else}
    <div class="space-y-6">
      {#each tasks as task}
        <div class="bg-slate-900 p-4 rounded border border-slate-700">
          <div class="flex justify-between items-center mb-2">
            <span class="font-semibold text-white">{task.name}</span>
            <span class="text-xs text-slate-400">Last: {task.last_run || 'Never'}</span>
          </div>
          
          <div class="relative pt-4">
            <div class="flex justify-between mb-2">
              {#each stages as stage, i}
                <div class="flex flex-col items-center flex-1 relative z-10">
                  <div class={`w-4 h-4 rounded-full border-2 flex items-center justify-center
                    ${getStageIndex(task.status) >= i 
                      ? 'bg-blue-500 border-blue-500' 
                      : 'bg-slate-800 border-slate-600'}`}>
                    {#if getStageIndex(task.status) >= i}
                      <div class="w-2 h-2 bg-white rounded-full"></div>
                    {/if}
                  </div>
                  <span class={`text-xs mt-1 ${getStageIndex(task.status) >= i ? 'text-blue-400' : 'text-slate-500'}`}>
                    {stage}
                  </span>
                </div>
              {/each}
              
              <!-- Progress Bar Background -->
              <div class="absolute top-6 left-0 w-full h-0.5 bg-slate-700 -z-0 transform -translate-y-1/2 mx-8" style="width: calc(100% - 4rem);"></div>
              
              <!-- Active Progress -->
              <div class="absolute top-6 left-0 h-0.5 bg-blue-500 -z-0 transform -translate-y-1/2 mx-8 transition-all duration-500"
                   style="width: calc({(Math.max(0, getStageIndex(task.status)) / (stages.length - 1)) * 100}% - 4rem);">
              </div>
            </div>
            
            <div class="text-right mt-2">
              <span class={`text-xs px-2 py-1 rounded ${
                task.status === 'error' ? 'bg-red-900 text-red-200' : 
                task.status === 'running' ? 'bg-blue-900 text-blue-200' : 
                'bg-slate-800 text-slate-400'
              }`}>
                {task.status}
              </span>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
