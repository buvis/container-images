<script lang="ts">
  import { page } from '$app/stores';
</script>

<div class="flex flex-1 items-center justify-center">
  <div class="text-center">
    <h1 class="text-6xl font-bold text-brand-400">{$page.status}</h1>
    <p class="mt-4 text-lg text-neutral-400">{$page.error?.message || 'Something went wrong'}</p>
    <button onclick={() => history.back()} class="mt-6 text-sm text-brand-400 hover:underline">
      Go back
    </button>
  </div>
</div>
