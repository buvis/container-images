import { api } from '$api/client';
import type { Notification } from '$lib/types/models';

export interface UnreadCount {
  count: number;
}

export const notificationsApi = {
  list(vaultId: string) {
    return api.get<Notification[]>(`/vaults/${vaultId}/notifications`);
  },

  unreadCount(vaultId: string) {
    return api.get<UnreadCount>(`/vaults/${vaultId}/notifications/unread-count`);
  },

  markRead(vaultId: string, notificationId: string) {
    return api.patch<Notification>(
      `/vaults/${vaultId}/notifications/${notificationId}`,
      { read: true }
    );
  },

  markUnread(vaultId: string, notificationId: string) {
    return api.patch<Notification>(
      `/vaults/${vaultId}/notifications/${notificationId}`,
      { read: false }
    );
  },

  markAllRead(vaultId: string) {
    return api.post(`/vaults/${vaultId}/notifications/mark-all-read`);
  },

  delete(vaultId: string, notificationId: string) {
    return api.del(`/vaults/${vaultId}/notifications/${notificationId}`);
  },

  clearRead(vaultId: string) {
    return api.del(`/vaults/${vaultId}/notifications/clear-read`);
  }
};
