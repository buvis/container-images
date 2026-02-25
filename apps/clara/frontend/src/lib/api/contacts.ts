import { api, qs } from '$api/client';
import type {
  Address,
  Contact,
  ContactMethod,
  ContactRelationship,
  Pet,
  RelationshipType,
  Tag
} from '$lib/types/models';
import type { PaginatedResponse } from '$lib/types/common';

export interface ContactCreateInput {
  first_name: string;
  last_name?: string;
  nickname?: string | null;
  birthdate?: string | null;
  gender?: string | null;
  pronouns?: string | null;
  notes_summary?: string | null;
  favorite?: boolean;
}

export type ContactUpdateInput = Partial<ContactCreateInput> & {
  photo_file_id?: string | null;
};

export const contactsApi = {
  list(
    vaultId: string,
    params?: { q?: string; favorites?: boolean; offset?: number; limit?: number }
  ) {
    return api.get<PaginatedResponse<Contact>>(
      `/vaults/${vaultId}/contacts${qs(params ?? {})}`
    );
  },

  get(vaultId: string, contactId: string) {
    return api.get<Contact>(`/vaults/${vaultId}/contacts/${contactId}`);
  },

  create(vaultId: string, data: ContactCreateInput) {
    return api.post<Contact>(`/vaults/${vaultId}/contacts`, data);
  },

  update(vaultId: string, contactId: string, data: ContactUpdateInput) {
    return api.patch<Contact>(`/vaults/${vaultId}/contacts/${contactId}`, data);
  },

  del(vaultId: string, contactId: string) {
    return api.del(`/vaults/${vaultId}/contacts/${contactId}`);
  },

  // --- Contact Methods ---
  listMethods(vaultId: string, contactId: string) {
    return api.get<ContactMethod[]>(
      `/vaults/${vaultId}/contacts/${contactId}/methods`
    );
  },
  createMethod(
    vaultId: string,
    contactId: string,
    data: { type: string; value: string; label?: string }
  ) {
    return api.post<ContactMethod>(
      `/vaults/${vaultId}/contacts/${contactId}/methods`,
      data
    );
  },
  updateMethod(
    vaultId: string,
    contactId: string,
    methodId: string,
    data: { type?: string; value?: string; label?: string }
  ) {
    return api.patch<ContactMethod>(
      `/vaults/${vaultId}/contacts/${contactId}/methods/${methodId}`,
      data
    );
  },
  deleteMethod(vaultId: string, contactId: string, methodId: string) {
    return api.del(`/vaults/${vaultId}/contacts/${contactId}/methods/${methodId}`);
  },

  // --- Addresses ---
  listAddresses(vaultId: string, contactId: string) {
    return api.get<Address[]>(`/vaults/${vaultId}/contacts/${contactId}/addresses`);
  },
  createAddress(
    vaultId: string,
    contactId: string,
    data: {
      label?: string;
      line1?: string;
      line2?: string | null;
      city?: string;
      postal_code?: string;
      country?: string;
    }
  ) {
    return api.post<Address>(
      `/vaults/${vaultId}/contacts/${contactId}/addresses`,
      data
    );
  },
  updateAddress(
    vaultId: string,
    contactId: string,
    addressId: string,
    data: {
      label?: string;
      line1?: string;
      line2?: string | null;
      city?: string;
      postal_code?: string;
      country?: string;
    }
  ) {
    return api.patch<Address>(
      `/vaults/${vaultId}/contacts/${contactId}/addresses/${addressId}`,
      data
    );
  },
  deleteAddress(vaultId: string, contactId: string, addressId: string) {
    return api.del(
      `/vaults/${vaultId}/contacts/${contactId}/addresses/${addressId}`
    );
  },

  // --- Pets ---
  listPets(vaultId: string, contactId: string) {
    return api.get<Pet[]>(`/vaults/${vaultId}/contacts/${contactId}/pets`);
  },
  createPet(
    vaultId: string,
    contactId: string,
    data: { name: string; species?: string; birthdate?: string | null; notes?: string | null }
  ) {
    return api.post<Pet>(`/vaults/${vaultId}/contacts/${contactId}/pets`, data);
  },
  updatePet(
    vaultId: string,
    contactId: string,
    petId: string,
    data: { name?: string; species?: string; birthdate?: string | null; notes?: string | null }
  ) {
    return api.patch<Pet>(
      `/vaults/${vaultId}/contacts/${contactId}/pets/${petId}`,
      data
    );
  },
  deletePet(vaultId: string, contactId: string, petId: string) {
    return api.del(`/vaults/${vaultId}/contacts/${contactId}/pets/${petId}`);
  },

  // --- Tags ---
  listTags(vaultId: string, contactId: string) {
    return api.get<Tag[]>(`/vaults/${vaultId}/contacts/${contactId}/tags`);
  },
  addTag(vaultId: string, contactId: string, tagId: string) {
    return api.post<Tag>(`/vaults/${vaultId}/contacts/${contactId}/tags`, {
      tag_id: tagId
    });
  },
  removeTag(vaultId: string, contactId: string, tagId: string) {
    return api.del(`/vaults/${vaultId}/contacts/${contactId}/tags/${tagId}`);
  },

  // --- Relationships ---
  listRelationships(vaultId: string, contactId: string) {
    return api.get<ContactRelationship[]>(
      `/vaults/${vaultId}/contacts/${contactId}/relationships`
    );
  },
  createRelationship(
    vaultId: string,
    contactId: string,
    data: { other_contact_id: string; relationship_type_id: string }
  ) {
    return api.post<ContactRelationship>(
      `/vaults/${vaultId}/contacts/${contactId}/relationships`,
      data
    );
  },
  deleteRelationship(vaultId: string, contactId: string, relationshipId: string) {
    return api.del(
      `/vaults/${vaultId}/contacts/${contactId}/relationships/${relationshipId}`
    );
  }
};

// --- Vault-level Tags ---
export const tagsApi = {
  list(vaultId: string) {
    return api.get<Tag[]>(`/vaults/${vaultId}/tags`);
  },
  create(vaultId: string, data: { name: string; color?: string }) {
    return api.post<Tag>(`/vaults/${vaultId}/tags`, data);
  }
};

// --- Relationship Types ---
export const relationshipTypesApi = {
  list(vaultId: string) {
    return api.get<RelationshipType[]>(`/vaults/${vaultId}/relationship-types`);
  },
  create(
    vaultId: string,
    data: { name: string; inverse_type_id?: string | null }
  ) {
    return api.post<RelationshipType>(
      `/vaults/${vaultId}/relationship-types`,
      data
    );
  },
  update(
    vaultId: string,
    typeId: string,
    data: { name?: string; inverse_type_id?: string | null }
  ) {
    return api.patch<RelationshipType>(
      `/vaults/${vaultId}/relationship-types/${typeId}`,
      data
    );
  },
  del(vaultId: string, typeId: string) {
    return api.del(`/vaults/${vaultId}/relationship-types/${typeId}`);
  }
};
