import { api } from '$api/client';
import type {
  AuthResponse,
  LoginResponse,
  TwoFactorConfirmRequest,
  TwoFactorSetupResponse,
  TwoFactorVerifyRequest,
  User
} from '$api/types';

export const authApi = {
  login(email: string, password: string): Promise<LoginResponse> {
    return api.post<LoginResponse>('/auth/login', { email, password });
  },

  register(email: string, password: string, name: string): Promise<AuthResponse> {
    return api.post<AuthResponse>('/auth/register', { email, password, name });
  },

  logout(): Promise<void> {
    return api.post('/auth/logout');
  },

  me(): Promise<User> {
    return api.get<User>('/auth/me');
  },

  setupTwoFactor(): Promise<TwoFactorSetupResponse> {
    return api.post<TwoFactorSetupResponse>('/auth/2fa/setup');
  },

  confirmTwoFactor(data: TwoFactorConfirmRequest): Promise<{ ok: boolean }> {
    return api.post<{ ok: boolean }>('/auth/2fa/confirm', data);
  },

  verifyTwoFactor(data: TwoFactorVerifyRequest): Promise<AuthResponse> {
    return api.post<AuthResponse>('/auth/2fa/verify', data);
  },

  recoverTwoFactor(data: TwoFactorVerifyRequest): Promise<AuthResponse> {
    return api.post<AuthResponse>('/auth/2fa/recovery', data);
  },

  disableTwoFactor(): Promise<{ ok: boolean }> {
    return api.del<{ ok: boolean }>('/auth/2fa');
  }
};
