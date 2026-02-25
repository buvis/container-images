<script lang="ts">
  import { page } from '$app/stores';
</script>

<div class="flex min-h-screen items-center justify-center bg-neutral-950 text-white">
  <div class="text-center">
    <h1 class="text-6xl font-bold text-brand-400">{$page.status}</h1>
    <p class="mt-4 text-lg text-neutral-400">{$page.error?.message || 'Something went wrong'}</p>
    <a href="/" class="mt-6 inline-block text-sm text-brand-400 hover:underline">Go home</a>
  </div>
</div>
