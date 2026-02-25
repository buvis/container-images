import { api, ApiClientError, getCsrfToken, qs } from '$api/client';
import type { FileRecord } from '$lib/types/models';
import type { PaginatedResponse } from '$lib/types/common';

export const filesApi = {
  list(vaultId: string, params?: { offset?: number; limit?: number; q?: string }) {
    return api.get<PaginatedResponse<FileRecord>>(`/vaults/${vaultId}/files${qs(params ?? {})}`);
  },

  get(vaultId: string, fileId: string) {
    return api.get<FileRecord>(`/vaults/${vaultId}/files/${fileId}`);
  },

  async upload(vaultId: string, file: File) {
    const form = new FormData();
    form.append('file', file);
    const csrf = getCsrfToken();
    const headers: Record<string, string> = {};
    if (csrf) headers['x-csrf-token'] = csrf;
    const res = await fetch(`/api/v1/vaults/${vaultId}/files`, {
      method: 'POST',
      credentials: 'include',
      headers,
      body: form
    });
    if (!res.ok) {
      const data = await res.json();
      throw new ApiClientError(res.status, data.detail ?? 'Upload failed');
    }
    return (await res.json()) as FileRecord;
  },

  download(vaultId: string, fileId: string) {
    window.open(`/api/v1/vaults/${vaultId}/files/${fileId}/download`, '_blank');
  },

  rename(vaultId: string, fileId: string, filename: string) {
    return api.patch<FileRecord>(`/vaults/${vaultId}/files/${fileId}`, { filename });
  },

  del(vaultId: string, fileId: string) {
    return api.del(`/vaults/${vaultId}/files/${fileId}`);
  }
};
