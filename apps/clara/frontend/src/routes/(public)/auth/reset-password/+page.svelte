<script lang="ts">
  import { page } from '$app/state';
  import { api } from '$api/client';
  import Button from '$components/ui/Button.svelte';
  import Input from '$components/ui/Input.svelte';

  const token = $derived(page.url.searchParams.get('token') ?? '');
  const tokenMissing = $derived(!token);

  let password = $state('');
  let error = $state('');
  let success = $state('');
  let submitting = $state(false);

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();
    error = '';
    success = '';
    if (!token) {
      error = 'Reset link is missing or invalid.';
      return;
    }
    submitting = true;
    try {
      await api.post('/auth/reset-password', { token, password });
      success = 'Password updated. You can now sign in.';
      password = '';
    } catch (err: any) {
      error = err.detail ?? 'Reset failed';
    } finally {
      submitting = false;
    }
  }
</script>

<form
  onsubmit={handleSubmit}
  class="rounded-xl border border-neutral-800 bg-neutral-900 p-8 shadow-2xl"
>
  <h2 class="mb-2 text-xl font-semibold text-white">Reset password</h2>
  <p class="mb-6 text-sm text-neutral-400">Choose a new password for your account.</p>

  {#if tokenMissing}
    <div class="mb-4 rounded-lg bg-red-950/50 px-4 py-3 text-sm text-red-400">
      Reset link is missing or invalid. Request a new one.
    </div>
  {/if}

  {#if error}
    <div class="mb-4 rounded-lg bg-red-950/50 px-4 py-3 text-sm text-red-400">
      {error}
    </div>
  {/if}

  {#if success}
    <div class="mb-4 rounded-lg bg-emerald-950/50 px-4 py-3 text-sm text-emerald-400">
      {success}
    </div>
  {/if}

  <Input label="New password" type="password" bind:value={password} required minlength={8} autocomplete="new-password" placeholder="Min 8 characters" />

  <Button type="submit" loading={submitting} disabled={tokenMissing} class="mt-6 w-full">
    Reset password
  </Button>

  <p class="mt-4 text-center text-sm text-neutral-400">
    Remembered your password?
    <a href="/auth/login" class="text-brand-400 hover:text-brand-300 transition">
      Sign in
    </a>
  </p>
</form>
