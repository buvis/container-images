import { api, qs } from '$api/client';
import type { Debt } from '$lib/types/models';
import type { PaginatedResponse } from '$lib/types/common';

export interface DebtCreateInput {
  contact_id: string;
  direction: 'you_owe' | 'owed_to_you';
  amount: number;
  currency?: string;
  due_date?: string | null;
  settled?: boolean;
  notes?: string | null;
}

export type DebtUpdateInput = Partial<DebtCreateInput>;

export const debtsApi = {
  list(vaultId: string, params?: { settled?: boolean; direction?: string; search?: string; offset?: number; limit?: number }) {
    return api.get<PaginatedResponse<Debt>>(`/vaults/${vaultId}/debts${qs(params ?? {})}`);
  },

  get(vaultId: string, debtId: string) {
    return api.get<Debt>(`/vaults/${vaultId}/debts/${debtId}`);
  },

  create(vaultId: string, data: DebtCreateInput) {
    return api.post<Debt>(`/vaults/${vaultId}/debts`, data);
  },

  update(vaultId: string, debtId: string, data: DebtUpdateInput) {
    return api.patch<Debt>(`/vaults/${vaultId}/debts/${debtId}`, data);
  },

  del(vaultId: string, debtId: string) {
    return api.del(`/vaults/${vaultId}/debts/${debtId}`);
  }
};
