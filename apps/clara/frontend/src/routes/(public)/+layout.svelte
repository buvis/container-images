<script lang="ts">
  let { children } = $props();
</script>

<div class="flex min-h-screen items-center justify-center bg-neutral-950 px-4">
  <div class="w-full max-w-md">
    <div class="mb-8 text-center">
      <h1 class="text-3xl font-bold tracking-tight text-white">CLARA</h1>
      <p class="mt-1 text-sm text-neutral-400">
        Connected Life & Authentic Relationship Assistant
      </p>
    </div>
    {@render children()}
  </div>
</div>
