import { api } from '$api/client';
import type { Contact, Activity, ActivityType } from '$api/types';
import type { PaginatedResponse } from '$lib/types/common';

interface ContactLookup {
  id: string;
  name: string;
}

interface ActivityLookup {
  id: string;
  title: string;
}

class LookupState {
  contacts = $state<ContactLookup[]>([]);
  activities = $state<ActivityLookup[]>([]);
  activityTypes = $state<ActivityType[]>([]);
  private contactsVaultId: string | null = null;
  private activitiesVaultId: string | null = null;
  private activityTypesVaultId: string | null = null;

  async loadContacts(vaultId: string): Promise<void> {
    if (this.contactsVaultId === vaultId) return;
    try {
      const res = await api.get<PaginatedResponse<Contact>>(
        `/vaults/${vaultId}/contacts?limit=1000`
      );
      this.contacts = res.items.map((c) => ({
        id: c.id,
        name: `${c.first_name} ${c.last_name}`.trim()
      }));
      this.contactsVaultId = vaultId;
    } catch {
      this.contacts = [];
    }
  }

  async loadActivities(vaultId: string): Promise<void> {
    if (this.activitiesVaultId === vaultId) return;
    try {
      const res = await api.get<PaginatedResponse<Activity>>(
        `/vaults/${vaultId}/activities?limit=1000`
      );
      this.activities = res.items.map((a) => ({
        id: a.id,
        title: a.title
      }));
      this.activitiesVaultId = vaultId;
    } catch {
      this.activities = [];
    }
  }

  async loadActivityTypes(vaultId: string): Promise<void> {
    if (this.activityTypesVaultId === vaultId) return;
    try {
      const res = await api.get<PaginatedResponse<ActivityType>>(
        `/vaults/${vaultId}/activities/types?limit=1000`
      );
      this.activityTypes = res.items;
      this.activityTypesVaultId = vaultId;
    } catch {
      this.activityTypes = [];
    }
  }

  getContactName(id: string): string {
    return this.contacts.find((c) => c.id === id)?.name ?? 'Unknown';
  }

  invalidate(): void {
    this.contactsVaultId = null;
    this.activitiesVaultId = null;
    this.activityTypesVaultId = null;
    this.contacts = [];
    this.activities = [];
    this.activityTypes = [];
  }
}

export const lookup = new LookupState();
