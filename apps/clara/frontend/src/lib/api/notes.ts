import { api, qs } from '$api/client';
import type { Note } from '$lib/types/models';
import type { PaginatedResponse } from '$lib/types/common';

export interface NoteCreateInput {
  contact_id?: string | null;
  activity_id?: string | null;
  title: string;
  body_markdown?: string;
}

export type NoteUpdateInput = Partial<NoteCreateInput>;

export const notesApi = {
  list(vaultId: string, params?: { offset?: number; limit?: number; contact_id?: string; activity_id?: string; q?: string }) {
    return api.get<PaginatedResponse<Note>>(`/vaults/${vaultId}/notes${qs(params ?? {})}`);
  },

  forContact(vaultId: string, contactId: string, params?: { offset?: number; limit?: number }) {
    return api.get<PaginatedResponse<Note>>(
      `/vaults/${vaultId}/notes${qs({ contact_id: contactId, ...params })}`
    );
  },

  get(vaultId: string, noteId: string) {
    return api.get<Note>(`/vaults/${vaultId}/notes/${noteId}`);
  },

  create(vaultId: string, data: NoteCreateInput) {
    return api.post<Note>(`/vaults/${vaultId}/notes`, data);
  },

  update(vaultId: string, noteId: string, data: NoteUpdateInput) {
    return api.patch<Note>(`/vaults/${vaultId}/notes/${noteId}`, data);
  },

  del(vaultId: string, noteId: string) {
    return api.del(`/vaults/${vaultId}/notes/${noteId}`);
  }
};
