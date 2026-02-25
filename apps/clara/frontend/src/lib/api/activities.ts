import { api, qs } from '$api/client';
import type { Activity, ActivityType } from '$lib/types/models';
import type { PaginatedResponse } from '$lib/types/common';

export interface ParticipantInput {
  contact_id: string;
  role?: string;
}

export interface ActivityCreateInput {
  activity_type_id?: string | null;
  title: string;
  description?: string | null;
  happened_at: string;
  location?: string | null;
  participants?: ParticipantInput[];
}

export type ActivityUpdateInput = Partial<ActivityCreateInput>;

export interface ActivityTypeCreateInput {
  name: string;
  icon?: string;
  color?: string;
}

export type ActivityTypeUpdateInput = Partial<ActivityTypeCreateInput>;

export const activitiesApi = {
  list(vaultId: string, params?: { offset?: number; limit?: number; q?: string }) {
    return api.get<PaginatedResponse<Activity>>(`/vaults/${vaultId}/activities${qs(params ?? {})}`);
  },

  get(vaultId: string, activityId: string) {
    return api.get<Activity>(`/vaults/${vaultId}/activities/${activityId}`);
  },

  create(vaultId: string, data: ActivityCreateInput) {
    return api.post<Activity>(`/vaults/${vaultId}/activities`, data);
  },

  update(vaultId: string, activityId: string, data: ActivityUpdateInput) {
    return api.patch<Activity>(`/vaults/${vaultId}/activities/${activityId}`, data);
  },

  del(vaultId: string, activityId: string) {
    return api.del(`/vaults/${vaultId}/activities/${activityId}`);
  },

  forContact(vaultId: string, contactId: string, params?: { offset?: number; limit?: number }) {
    return api.get<PaginatedResponse<Activity>>(`/vaults/${vaultId}/contacts/${contactId}/activities${qs(params ?? {})}`);
  },

  listTypes(vaultId: string, params?: { offset?: number; limit?: number }) {
    return api.get<PaginatedResponse<ActivityType>>(`/vaults/${vaultId}/activities/types${qs(params ?? {})}`);
  },

  createType(vaultId: string, data: ActivityTypeCreateInput) {
    return api.post<ActivityType>(`/vaults/${vaultId}/activities/types`, data);
  },

  updateType(vaultId: string, typeId: string, data: ActivityTypeUpdateInput) {
    return api.patch<ActivityType>(`/vaults/${vaultId}/activities/types/${typeId}`, data);
  },

  deleteType(vaultId: string, typeId: string) {
    return api.del(`/vaults/${vaultId}/activities/types/${typeId}`);
  }
};
