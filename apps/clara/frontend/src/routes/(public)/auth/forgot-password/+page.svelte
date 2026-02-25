<script lang="ts">
  import { api } from '$api/client';
  import Button from '$components/ui/Button.svelte';
  import Input from '$components/ui/Input.svelte';

  let email = $state('');
  let error = $state('');
  let success = $state('');
  let submitting = $state(false);

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();
    error = '';
    success = '';
    submitting = true;
    try {
      await api.post('/auth/forgot-password', { email });
      success = 'If an account exists for that email, a reset link will arrive shortly.';
    } catch (err: any) {
      error = err.detail ?? 'Request failed';
    } finally {
      submitting = false;
    }
  }
</script>

<form
  onsubmit={handleSubmit}
  class="rounded-xl border border-neutral-800 bg-neutral-900 p-8 shadow-2xl"
>
  <h2 class="mb-2 text-xl font-semibold text-white">Forgot password</h2>
  <p class="mb-6 text-sm text-neutral-400">Enter your email to receive a reset link.</p>

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

  <Input label="Email" type="email" bind:value={email} required autocomplete="email" placeholder="you@example.com" />

  <Button type="submit" loading={submitting} class="mt-6 w-full">
    Send reset link
  </Button>

  <p class="mt-4 text-center text-sm text-neutral-400">
    Remembered your password?
    <a href="/auth/login" class="text-brand-400 hover:text-brand-300 transition">
      Sign in
    </a>
  </p>
</form>
