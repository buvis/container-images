<script lang="ts">
  import { goto } from '$app/navigation';
  import { auth } from '$state/auth.svelte';
  import Button from '$components/ui/Button.svelte';
  import Input from '$components/ui/Input.svelte';

  let name = $state('');
  let email = $state('');
  let password = $state('');
  let error = $state('');
  let submitting = $state(false);

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();
    error = '';
    submitting = true;
    try {
      await auth.register(email, password, name);
      goto('/auth/login');
    } catch (err: any) {
      error = err.detail ?? 'Registration failed';
    } finally {
      submitting = false;
    }
  }
</script>

<form
  onsubmit={handleSubmit}
  class="rounded-xl border border-neutral-800 bg-neutral-900 p-8 shadow-2xl"
>
  <h2 class="mb-6 text-xl font-semibold text-white">Create account</h2>

  {#if error}
    <div class="mb-4 rounded-lg bg-red-950/50 px-4 py-3 text-sm text-red-400">
      {error}
    </div>
  {/if}

  <div class="space-y-4">
    <Input label="Name" bind:value={name} required autocomplete="name" placeholder="Jane Doe" />
    <Input label="Email" type="email" bind:value={email} required autocomplete="email" placeholder="you@example.com" />
    <Input label="Password" type="password" bind:value={password} required minlength={8} autocomplete="new-password" placeholder="Min 8 characters" />
  </div>

  <Button type="submit" loading={submitting} class="mt-6 w-full">
    Create account
  </Button>

  <p class="mt-4 text-center text-sm text-neutral-400">
    Already have an account?
    <a href="/auth/login" class="text-brand-400 hover:text-brand-300 transition">
      Sign in
    </a>
  </p>
</form>
