import { api, qs } from '$api/client';
import type { Template, TemplatePage, TemplateModule, CustomField, CustomFieldValue } from '$lib/types/models';
import type { PaginatedResponse } from '$lib/types/common';

export interface TemplateCreateInput {
  name: string;
  description?: string | null;
}

export type TemplateUpdateInput = Partial<TemplateCreateInput>;

export interface CustomFieldCreateInput {
  scope: string;
  name: string;
  slug: string;
  data_type: string;
  config_json?: string | null;
}

export interface TemplatePageCreateInput {
  slug: string;
  name: string;
  order?: number;
}

export interface TemplateModuleCreateInput {
  module_type: string;
  order?: number;
  config_json?: string | null;
}

export const customizationApi = {
  listTemplates(vaultId: string, params?: { offset?: number; limit?: number }) {
    return api.get<PaginatedResponse<Template>>(`/vaults/${vaultId}/templates${qs(params ?? {})}`);
  },

  getTemplate(vaultId: string, templateId: string) {
    return api.get<Template>(`/vaults/${vaultId}/templates/${templateId}`);
  },

  createTemplate(vaultId: string, data: TemplateCreateInput) {
    return api.post<Template>(`/vaults/${vaultId}/templates`, data);
  },

  updateTemplate(vaultId: string, templateId: string, data: TemplateUpdateInput) {
    return api.patch<Template>(`/vaults/${vaultId}/templates/${templateId}`, data);
  },

  deleteTemplate(vaultId: string, templateId: string) {
    return api.del(`/vaults/${vaultId}/templates/${templateId}`);
  },

  listCustomFields(vaultId: string, params?: { offset?: number; limit?: number; scope?: string }) {
    return api.get<PaginatedResponse<CustomField>>(`/vaults/${vaultId}/custom-fields/definitions${qs(params ?? {})}`);
  },

  createCustomField(vaultId: string, data: CustomFieldCreateInput) {
    return api.post<CustomField>(`/vaults/${vaultId}/custom-fields/definitions`, data);
  },

  updateCustomField(vaultId: string, fieldId: string, data: Partial<CustomFieldCreateInput>) {
    return api.patch<CustomField>(`/vaults/${vaultId}/custom-fields/definitions/${fieldId}`, data);
  },

  deleteCustomField(vaultId: string, fieldId: string) {
    return api.del(`/vaults/${vaultId}/custom-fields/definitions/${fieldId}`);
  },

  // Pages
  addPage(vaultId: string, templateId: string, data: TemplatePageCreateInput) {
    return api.post<TemplatePage>(`/vaults/${vaultId}/templates/${templateId}/pages`, data);
  },

  updatePage(vaultId: string, pageId: string, data: Partial<TemplatePageCreateInput>) {
    return api.patch<TemplatePage>(`/vaults/${vaultId}/templates/pages/${pageId}`, data);
  },

  deletePage(vaultId: string, pageId: string) {
    return api.del(`/vaults/${vaultId}/templates/pages/${pageId}`);
  },

  // Modules
  addModule(vaultId: string, pageId: string, data: TemplateModuleCreateInput) {
    return api.post<TemplateModule>(`/vaults/${vaultId}/templates/pages/${pageId}/modules`, data);
  },

  updateModule(vaultId: string, moduleId: string, data: Partial<TemplateModuleCreateInput>) {
    return api.patch<TemplateModule>(`/vaults/${vaultId}/templates/modules/${moduleId}`, data);
  },

  deleteModule(vaultId: string, moduleId: string) {
    return api.del(`/vaults/${vaultId}/templates/modules/${moduleId}`);
  },

  // Custom field values
  getFieldValues(vaultId: string, entityType: string, entityId: string) {
    return api.get<CustomFieldValue[]>(`/vaults/${vaultId}/custom-fields/values/${entityType}/${entityId}`);
  },

  setFieldValue(vaultId: string, data: { definition_id: string; entity_type: string; entity_id: string; value_json: string }) {
    return api.put<CustomFieldValue>(`/vaults/${vaultId}/custom-fields/values`, data);
  },

  deleteFieldValue(vaultId: string, valueId: string) {
    return api.del(`/vaults/${vaultId}/custom-fields/values/${valueId}`);
  }
};
