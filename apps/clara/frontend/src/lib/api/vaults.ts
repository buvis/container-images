import { api } from '$api/client';
import type { Vault, VaultSettings, Member } from '$lib/types/models';

export interface VaultCreateInput {
  name: string;
}

export interface MemberInviteInput {
  email: string;
  role?: string;
}

export interface VaultSettingsUpdateInput {
  language?: string;
  date_format?: string;
  time_format?: string;
  timezone?: string;
  feature_flags?: string;
}

export const vaultsApi = {
  list() {
    return api.get<Vault[]>('/vaults');
  },

  get(vaultId: string) {
    return api.get<Vault>(`/vaults/${vaultId}`);
  },

  create(data: VaultCreateInput) {
    return api.post<Vault>('/vaults', data);
  },

  del(vaultId: string) {
    return api.del(`/vaults/${vaultId}`);
  },

  rename(vaultId: string, name: string) {
    return api.patch<Vault>(`/vaults/${vaultId}`, { name });
  },

  // Settings
  getSettings(vaultId: string) {
    return api.get<VaultSettings>(`/vaults/${vaultId}/settings`);
  },

  updateSettings(vaultId: string, data: VaultSettingsUpdateInput) {
    return api.patch<VaultSettings>(`/vaults/${vaultId}/settings`, data);
  },

  // Members
  listMembers(vaultId: string) {
    return api.get<Member[]>(`/vaults/${vaultId}/members`);
  },

  inviteMember(vaultId: string, data: MemberInviteInput) {
    return api.post<Member>(`/vaults/${vaultId}/members`, data);
  },

  updateMemberRole(vaultId: string, userId: string, role: string) {
    return api.patch<Member>(`/vaults/${vaultId}/members/${userId}`, { role });
  },

  removeMember(vaultId: string, userId: string) {
    return api.del(`/vaults/${vaultId}/members/${userId}`);
  }
};
