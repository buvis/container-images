<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { type TaskState } from '$lib/api';
  import { formatDateTime } from '$lib/formatters';

  let tasks: TaskState[] = [];
  let loading = true;
  let ws: WebSocket | null = null;
  let reconnectDelay = 1000;
  let loadingTimeout: ReturnType<typeof setTimeout> | null = null;
  let connected = false;
  let pingInterval: ReturnType<typeof setInterval> | null = null;

  function getRateLimitCountdown(until: string | null): string | null {
    if (!until) return null;
    const end = new Date(until).getTime();
    const now = Date.now();
    const remaining = Math.max(0, Math.ceil((end - now) / 1000));
    return remaining > 0 ? `${remaining}s` : null;
  }

  function connect() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${location.host}/api/ws/tasks`);

    ws.onopen = () => {
      reconnectDelay = 1000;
      loading = false;
      connected = true;
      if (loadingTimeout) clearTimeout(loadingTimeout);
      // Start ping interval
      if (pingInterval) clearInterval(pingInterval);
      pingInterval = setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 25000);
    };

    ws.onmessage = (e) => {
      const data = e.data;
      // Handle ping/pong
      if (data === 'ping') {
        ws?.send('pong');
        return;
      }
      if (data === 'pong') {
        return;
      }
      // Task state update
      const parsed = JSON.parse(data);
      tasks = Object.entries(parsed).map(([name, state]) => ({
        name,
        ...(state as Omit<TaskState, 'name'>)
      }));
    };

    ws.onerror = () => {
      loading = false;
      connected = false;
    };

    ws.onclose = () => {
      connected = false;
      if (pingInterval) {
        clearInterval(pingInterval);
        pingInterval = null;
      }
      setTimeout(connect, reconnectDelay);
      reconnectDelay = Math.min(reconnectDelay * 2, 30000);
    };
  }

  onMount(() => {
    connect();
    // Stop showing loading after 3s even if WS fails
    loadingTimeout = setTimeout(() => { loading = false; }, 3000);
  });

  onDestroy(() => {
    ws?.close();
    if (loadingTimeout) clearTimeout(loadingTimeout);
    if (pingInterval) clearInterval(pingInterval);
  });
</script>

<div class="bg-slate-800 p-4 rounded-lg shadow-lg border border-slate-700">
  <div class="flex items-center justify-between mb-4">
    <h2 class="text-xl font-bold text-white">Tasks</h2>
    <span class="flex items-center gap-1.5 text-xs">
      <span class="w-2 h-2 rounded-full {connected ? 'bg-green-500' : 'bg-red-500'}"></span>
      <span class="text-slate-400">{connected ? 'Live' : 'Reconnecting'}</span>
    </span>
  </div>

  {#if loading && tasks.length === 0}
    <div class="animate-pulse space-y-4">
      {#each Array(3) as _}
        <div class="h-12 bg-slate-700 rounded"></div>
      {/each}
    </div>
  {:else if tasks.length === 0}
    <div class="flex items-center justify-center py-8 text-slate-500">
      <span class="text-sm">No active tasks</span>
    </div>
  {:else}
    <div class="space-y-4">
      {#each tasks as task}
        {@const countdown = getRateLimitCountdown(task.rate_limit_until)}
        <div class="bg-slate-900 p-4 rounded border border-slate-700">
          <div class="flex justify-between items-center mb-2">
            <span class="font-semibold text-white">{task.name}</span>
            <span class="text-xs text-slate-400">Last: {formatDateTime(task.last_run) || 'Never'}</span>
          </div>

          {#if task.status === 'running'}
            <!-- Progress bar -->
            <div class="mb-2">
              <div class="h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  class="h-full bg-blue-500 transition-all duration-300"
                  class:animate-pulse={countdown}
                  style="width: {task.progress ?? 0}%"
                ></div>
              </div>
            </div>

            <div class="flex justify-between items-center text-xs">
              <span class="text-slate-400">
                {#if countdown}
                  <span class="text-amber-400">Rate limited: {countdown}</span>
                {:else}
                  {task.message}
                {/if}
              </span>
              <span class="text-blue-400 font-mono">{task.progress ?? 0}%</span>
            </div>
          {:else}
            <!-- Status badge -->
            <div class="flex justify-between items-center">
              <span class="text-xs text-slate-400 truncate max-w-[70%]">{task.message}</span>
              <span class={`text-xs px-2 py-1 rounded ${
                task.status === 'error' ? 'bg-red-900 text-red-200' :
                task.status === 'done' ? 'bg-green-900 text-green-200' :
                'bg-slate-800 text-slate-400'
              }`}>
                {task.status}
              </span>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>
