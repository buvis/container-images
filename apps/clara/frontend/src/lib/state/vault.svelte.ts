import { api } from '$api/client';
import type { Vault, VaultSettings } from '$api/types';

export interface FeatureFlags {
  debts: boolean;
  gifts: boolean;
  pets: boolean;
  journal: boolean;
}

class VaultState {
  vaults = $state<Vault[]>([]);
  current = $state<Vault | null>(null);
  loading = $state(false);
  featureFlags = $state<FeatureFlags>({ debts: true, gifts: true, pets: true, journal: true });

  get currentId(): string | null {
    return this.current?.id ?? null;
  }

  async fetchVaults(): Promise<void> {
    this.loading = true;
    try {
      this.vaults = await api.get<Vault[]>('/vaults');
    } catch {
      this.vaults = [];
    } finally {
      this.loading = false;
    }
  }

  async fetchVault(id: string): Promise<Vault> {
    const vault = await api.get<Vault>(`/vaults/${id}`);
    this.current = vault;
    return vault;
  }

  async loadFeatureFlags(vaultId: string): Promise<void> {
    try {
      const settings = await api.get<VaultSettings>(`/vaults/${vaultId}/settings`);
      const raw = settings.feature_flags;
      const parsed = JSON.parse(raw || '{}');
      this.featureFlags = {
        debts: parsed.debts !== false,
        gifts: parsed.gifts !== false,
        pets: parsed.pets !== false,
        journal: parsed.journal !== false
      };
    } catch {
      this.featureFlags = { debts: true, gifts: true, pets: true, journal: true };
    }
  }

  setCurrent(vault: Vault): void {
    this.current = vault;
  }

  async createVault(name: string): Promise<Vault> {
    const vault = await api.post<Vault>('/vaults', { name });
    this.vaults = [...this.vaults, vault];
    return vault;
  }
}

export const vaultState = new VaultState();
