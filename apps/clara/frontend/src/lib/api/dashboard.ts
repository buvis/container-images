import { api } from '$api/client';
import type { Reminder, Activity, Task, Contact } from '#lib/types/models.ts';
import type { PaginatedResponse } from '#lib/types/common.ts';

export const dashboardApi = {
  upcomingReminders(vaultId: string) {
    return api.get<PaginatedResponse<Reminder>>(
      `/vaults/${vaultId}/reminders?status=active&limit=10`
    );
  },

  recentActivities(vaultId: string) {
    return api.get<PaginatedResponse<Activity>>(
      `/vaults/${vaultId}/activities?limit=5`
    );
  },

  overdueTasks(vaultId: string) {
    return api.get<PaginatedResponse<Task>>(
      `/vaults/${vaultId}/tasks?overdue=true&limit=10`
    );
  },

  recentContacts(vaultId: string) {
    return api.get<PaginatedResponse<Contact>>(
      `/vaults/${vaultId}/contacts?limit=10`
    );
  }
};
