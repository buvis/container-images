import { api, qs } from '$api/client';
import type { JournalEntry } from '$lib/types/models';
import type { PaginatedResponse } from '$lib/types/common';

export interface JournalEntryCreateInput {
  entry_date: string;
  title?: string;
  body_markdown?: string;
  mood?: number | null;
}

export type JournalEntryUpdateInput = Partial<JournalEntryCreateInput>;

export const journalApi = {
  list(vaultId: string, params?: { search?: string; offset?: number; limit?: number }) {
    return api.get<PaginatedResponse<JournalEntry>>(`/vaults/${vaultId}/journal${qs(params ?? {})}`);
  },

  get(vaultId: string, entryId: string) {
    return api.get<JournalEntry>(`/vaults/${vaultId}/journal/${entryId}`);
  },

  create(vaultId: string, data: JournalEntryCreateInput) {
    return api.post<JournalEntry>(`/vaults/${vaultId}/journal`, data);
  },

  update(vaultId: string, entryId: string, data: JournalEntryUpdateInput) {
    return api.patch<JournalEntry>(`/vaults/${vaultId}/journal/${entryId}`, data);
  },

  del(vaultId: string, entryId: string) {
    return api.del(`/vaults/${vaultId}/journal/${entryId}`);
  }
};
