import { api, qs } from '$api/client';
import type { Task } from '$lib/types/models';
import type { PaginatedResponse } from '$lib/types/common';

export interface TaskCreateInput {
  title: string;
  description?: string | null;
  due_date?: string | null;
  status?: string;
  priority?: number;
  contact_id?: string | null;
  activity_id?: string | null;
}

export type TaskUpdateInput = Partial<TaskCreateInput>;

export const tasksApi = {
  list(vaultId: string, params?: { status?: string; overdue?: boolean; search?: string; offset?: number; limit?: number }) {
    return api.get<PaginatedResponse<Task>>(`/vaults/${vaultId}/tasks${qs(params ?? {})}`);
  },

  get(vaultId: string, taskId: string) {
    return api.get<Task>(`/vaults/${vaultId}/tasks/${taskId}`);
  },

  create(vaultId: string, data: TaskCreateInput) {
    return api.post<Task>(`/vaults/${vaultId}/tasks`, data);
  },

  update(vaultId: string, taskId: string, data: TaskUpdateInput) {
    return api.patch<Task>(`/vaults/${vaultId}/tasks/${taskId}`, data);
  },

  del(vaultId: string, taskId: string) {
    return api.del(`/vaults/${vaultId}/tasks/${taskId}`);
  }
};
