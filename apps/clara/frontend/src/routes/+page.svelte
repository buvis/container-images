<script lang="ts">
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { auth } from '$state/auth.svelte';
  import Spinner from '$components/ui/Spinner.svelte';

  let resolved = false;

  $effect(() => {
    if (browser) resolve();
  });

  async function resolve() {
    if (resolved) return;

    try {
      await auth.fetchMe();
    } catch {
      resolved = true;
      goto('/auth/login');
      return;
    }

    if (!auth.isAuthenticated) {
      resolved = true;
      goto('/auth/login');
      return;
    }

    resolved = true;
    goto('/vaults');
  }
</script>

<div class="flex min-h-screen items-center justify-center bg-neutral-950">
  <Spinner />
</div>
