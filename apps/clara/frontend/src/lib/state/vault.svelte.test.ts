import { api } from '$api/client';

vi.mock('$api/client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn()
  }
}));

let vault: any;

beforeEach(async () => {
  vi.mocked(api.get).mockReset();
  vi.mocked(api.post).mockReset();
  vi.resetModules();
  const mod = await import('./vault.svelte');
  vault = mod.vaultState;
});

describe('VaultState', () => {
  it('setCurrent updates currentId', () => {
    expect(vault.currentId).toBeNull();
    vault.setCurrent({ id: 'v1', name: 'Test', created_at: '' });
    expect(vault.currentId).toBe('v1');
    expect(vault.current.name).toBe('Test');
  });

  it('fetchVaults populates vaults list', async () => {
    const vaults = [{ id: 'v1', name: 'A', created_at: '' }];
    vi.mocked(api.get).mockResolvedValue(vaults);
    await vault.fetchVaults();
    expect(api.get).toHaveBeenCalledWith('/vaults');
    expect(vault.vaults).toEqual(vaults);
    expect(vault.loading).toBe(false);
  });

  it('fetchVaults clears on error', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('fail'));
    await vault.fetchVaults();
    expect(vault.vaults).toEqual([]);
    expect(vault.loading).toBe(false);
  });

  it('loadFeatureFlags loads and stores flags', async () => {
    vi.mocked(api.get).mockResolvedValue({
      vault_id: 'v1',
      language: 'en',
      date_format: 'Y-m-d',
      time_format: '24h',
      timezone: 'UTC',
      feature_flags: '{"debts":false,"journal":true}'
    });
    await vault.loadFeatureFlags('v1');
    expect(api.get).toHaveBeenCalledWith('/vaults/v1/settings');
    expect(vault.featureFlags.debts).toBe(false);
    expect(vault.featureFlags.journal).toBe(true);
    // Defaults to true when not specified
    expect(vault.featureFlags.gifts).toBe(true);
    expect(vault.featureFlags.pets).toBe(true);
  });

  it('loadFeatureFlags defaults all true on error', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('fail'));
    await vault.loadFeatureFlags('v1');
    expect(vault.featureFlags).toEqual({ debts: true, gifts: true, pets: true, journal: true });
  });

  it('createVault adds to vaults list', async () => {
    const newVault = { id: 'v2', name: 'New', created_at: '' };
    vi.mocked(api.post).mockResolvedValue(newVault);
    const result = await vault.createVault('New');
    expect(api.post).toHaveBeenCalledWith('/vaults', { name: 'New' });
    expect(result).toEqual(newVault);
    expect(vault.vaults).toContainEqual(newVault);
  });
});
