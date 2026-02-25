import { api } from '$api/client';
import type { User, AuthResponse, LoginResponse } from '$api/types';

class AuthState {
  user = $state<User | null>(null);
  loading = $state(true);

  get isAuthenticated(): boolean {
    return this.user !== null;
  }

  async fetchMe(): Promise<void> {
    try {
      this.user = await api.get<User>('/auth/me');
    } catch {
      this.user = null;
    } finally {
      this.loading = false;
    }
  }

  async login(email: string, password: string): Promise<LoginResponse> {
    const res = await api.post<LoginResponse>('/auth/login', { email, password });
    if ('user' in res) {
      this.user = res.user;
    }
    return res;
  }

  async register(email: string, password: string, name: string): Promise<AuthResponse> {
    const res = await api.post<AuthResponse>('/auth/register', { email, password, name });
    this.user = res.user;
    return res;
  }

  async logout(): Promise<void> {
    await api.post('/auth/logout');
    this.user = null;
  }

  async verifyTwoFactor(
    tempToken: string,
    code: string,
    useRecovery = false
  ): Promise<AuthResponse> {
    const path = useRecovery ? '/auth/2fa/recovery' : '/auth/2fa/verify';
    const res = await api.post<AuthResponse>(path, { temp_token: tempToken, code });
    this.user = res.user;
    return res;
  }
}

export const auth = new AuthState();
