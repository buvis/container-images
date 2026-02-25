<script lang="ts">
  import { goto } from '$app/navigation';
  import { auth } from '$state/auth.svelte';
  import Button from '$components/ui/Button.svelte';
  import Input from '$components/ui/Input.svelte';

  let email = $state('');
  let password = $state('');
  let error = $state('');
  let submitting = $state(false);
  let tempToken = $state('');
  let twoFactorCode = $state('');
  let twoFactorMode = $state<'totp' | 'recovery' | null>(null);
  let twoFactorError = $state('');
  let verifying = $state(false);

  function handleAuthRedirect(vaultId: string | null) {
    const saved = sessionStorage.getItem('clara_redirect');
    sessionStorage.removeItem('clara_redirect');
    if (saved && saved.startsWith('/')) {
      goto(saved);
    } else if (vaultId) {
      goto(`/vaults/${vaultId}/dashboard`);
    } else {
      goto('/');
    }
  }

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();
    error = '';
    submitting = true;
    try {
      const res = await auth.login(email, password);
      if ('requires_2fa' in res) {
        tempToken = res.temp_token;
        twoFactorMode = 'totp';
        twoFactorCode = '';
        password = '';
        return;
      }
      handleAuthRedirect(res.vault_id);
    } catch (err: any) {
      error = err.detail ?? 'Login failed';
    } finally {
      submitting = false;
    }
  }

  async function handleTwoFactorSubmit(e: SubmitEvent) {
    e.preventDefault();
    if (!tempToken) {
      twoFactorError = 'Missing 2FA token. Please sign in again.';
      return;
    }
    twoFactorError = '';
    verifying = true;
    try {
      const res = await auth.verifyTwoFactor(
        tempToken,
        twoFactorCode,
        twoFactorMode === 'recovery'
      );
      handleAuthRedirect(res.vault_id);
    } catch (err: any) {
      twoFactorError = err.detail ?? 'Verification failed';
    } finally {
      verifying = false;
    }
  }
</script>

{#if twoFactorMode}
  <form
    onsubmit={handleTwoFactorSubmit}
    class="rounded-xl border border-neutral-800 bg-neutral-900 p-8 shadow-2xl"
  >
    <h2 class="mb-6 text-xl font-semibold text-white">Two-factor verification</h2>

    {#if twoFactorError}
      <div class="mb-4 rounded-lg bg-red-950/50 px-4 py-3 text-sm text-red-400">
        {twoFactorError}
      </div>
    {/if}

    <Input
      label={twoFactorMode === 'recovery' ? 'Recovery code' : 'Authenticator code'}
      bind:value={twoFactorCode}
      required
      autocomplete="one-time-code"
      placeholder={twoFactorMode === 'recovery' ? '8-character code' : '123456'}
    />

    <Button type="submit" loading={verifying} class="mt-6 w-full">
      Verify
    </Button>

    <div class="mt-4 flex items-center justify-between text-sm text-neutral-400">
      <button
        type="button"
        class="text-brand-400 hover:text-brand-300 transition"
        onclick={() => (twoFactorMode = twoFactorMode === 'recovery' ? 'totp' : 'recovery')}
      >
        {twoFactorMode === 'recovery' ? 'Use authenticator code' : 'Use recovery code'}
      </button>
      <button
        type="button"
        class="text-neutral-400 hover:text-neutral-200 transition"
        onclick={() => {
          twoFactorMode = null;
          tempToken = '';
          twoFactorCode = '';
          twoFactorError = '';
        }}
      >
        Back to sign in
      </button>
    </div>
  </form>
{:else}
  <form
    onsubmit={handleSubmit}
    class="rounded-xl border border-neutral-800 bg-neutral-900 p-8 shadow-2xl"
  >
    <h2 class="mb-6 text-xl font-semibold text-white">Sign in</h2>

    {#if error}
      <div class="mb-4 rounded-lg bg-red-950/50 px-4 py-3 text-sm text-red-400">
        {error}
      </div>
    {/if}

    <div class="space-y-4">
      <Input label="Email" type="email" bind:value={email} required autocomplete="email" placeholder="you@example.com" />
      <Input label="Password" type="password" bind:value={password} required autocomplete="current-password" placeholder="********" />
    </div>

    <Button type="submit" loading={submitting} class="mt-6 w-full">
      Sign in
    </Button>

    <p class="mt-3 text-center">
      <a href="/auth/forgot-password" class="text-sm text-neutral-400 transition hover:text-brand-400">
        Forgot password?
      </a>
    </p>

    <p class="mt-2 text-center text-sm text-neutral-400">
      No account?
      <a href="/auth/register" class="text-brand-400 hover:text-brand-300 transition">
        Create one
      </a>
    </p>
  </form>
{/if}
