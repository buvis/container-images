import { api, qs } from '$api/client';
import type { Reminder } from '$lib/types/models';
import type { PaginatedResponse } from '$lib/types/common';

export interface ReminderCreateInput {
  contact_id?: string | null;
  title: string;
  description?: string | null;
  next_expected_date: string;
  frequency_type?: string;
  frequency_number?: number;
}

export type ReminderUpdateInput = Partial<ReminderCreateInput> & { status?: string };

export const remindersApi = {
  list(vaultId: string, params?: { status?: string; search?: string; offset?: number; limit?: number }) {
    return api.get<PaginatedResponse<Reminder>>(`/vaults/${vaultId}/reminders${qs(params ?? {})}`);
  },

  get(vaultId: string, reminderId: string) {
    return api.get<Reminder>(`/vaults/${vaultId}/reminders/${reminderId}`);
  },

  create(vaultId: string, data: ReminderCreateInput) {
    return api.post<Reminder>(`/vaults/${vaultId}/reminders`, data);
  },

  update(vaultId: string, reminderId: string, data: ReminderUpdateInput) {
    return api.patch<Reminder>(`/vaults/${vaultId}/reminders/${reminderId}`, data);
  },

  del(vaultId: string, reminderId: string) {
    return api.del(`/vaults/${vaultId}/reminders/${reminderId}`);
  }
};
