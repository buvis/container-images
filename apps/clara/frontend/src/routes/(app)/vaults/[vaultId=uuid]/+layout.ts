import { vaultState } from '$state/vault.svelte';
import { lookup } from '$state/lookup.svelte';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ params }) => {
  const { vaultId } = params;

  await vaultState.fetchVault(vaultId);

  // Pre-load lookup data for the vault
  lookup.invalidate();
  lookup.loadContacts(vaultId);
  lookup.loadActivityTypes(vaultId);

  return { vaultId };
};
