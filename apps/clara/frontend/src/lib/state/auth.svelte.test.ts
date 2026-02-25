import { api } from '$api/client';

vi.mock('$api/client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn()
  }
}));

let AuthState: any;

beforeEach(async () => {
  vi.mocked(api.get).mockReset();
  vi.mocked(api.post).mockReset();
  // Re-import to get fresh class (module-level singleton is shared)
  vi.resetModules();
  const mod = await import('./auth.svelte');
  AuthState = mod.auth;
});

describe('AuthState', () => {
  it('fetchMe sets user state', async () => {
    const user = { id: '1', email: 'a@b.com', name: 'Alice', is_active: true, default_vault_id: null, created_at: '' };
    vi.mocked(api.get).mockResolvedValue(user);
    await AuthState.fetchMe();
    expect(api.get).toHaveBeenCalledWith('/auth/me');
    expect(AuthState.user).toEqual(user);
    expect(AuthState.loading).toBe(false);
  });

  it('fetchMe clears user on error', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('fail'));
    await AuthState.fetchMe();
    expect(AuthState.user).toBeNull();
    expect(AuthState.loading).toBe(false);
  });

  it('login updates auth state', async () => {
    const user = { id: '1', email: 'a@b.com', name: 'Alice', is_active: true, default_vault_id: null, created_at: '' };
    vi.mocked(api.post).mockResolvedValue({ user, access_token: 'tok', vault_id: 'v1' });
    const res = await AuthState.login('a@b.com', 'pass');
    expect(api.post).toHaveBeenCalledWith('/auth/login', { email: 'a@b.com', password: 'pass' });
    expect(AuthState.user).toEqual(user);
    expect(res.vault_id).toBe('v1');
  });

  it('login returns 2fa challenge without setting user', async () => {
    vi.mocked(api.post).mockResolvedValue({ requires_2fa: true, temp_token: 'tok' });
    const res = await AuthState.login('a@b.com', 'pass');
    expect(AuthState.user).toBeNull();
    expect(res.requires_2fa).toBe(true);
  });

  it('logout clears state', async () => {
    // Set user first
    const user = { id: '1', email: 'a@b.com', name: 'Alice', is_active: true, default_vault_id: null, created_at: '' };
    vi.mocked(api.get).mockResolvedValue(user);
    await AuthState.fetchMe();
    expect(AuthState.user).toBeTruthy();
    // Logout
    vi.mocked(api.post).mockResolvedValue(undefined);
    await AuthState.logout();
    expect(api.post).toHaveBeenCalledWith('/auth/logout');
    expect(AuthState.user).toBeNull();
  });

  it('isAuthenticated reflects user presence', async () => {
    expect(AuthState.isAuthenticated).toBe(false);
    const user = { id: '1', email: 'a@b.com', name: 'Alice', is_active: true, default_vault_id: null, created_at: '' };
    vi.mocked(api.get).mockResolvedValue(user);
    await AuthState.fetchMe();
    expect(AuthState.isAuthenticated).toBe(true);
  });
});
