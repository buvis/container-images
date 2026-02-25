import type { PaginatedResponse } from '$lib/types/common';
import { mockPage } from './setup';

/** Set vault route params for vault-scoped tests */
export function setVaultParams(vaultId: string, extra?: Record<string, string>) {
  mockPage.params = { vaultId, ...extra };
}

/** Build a PaginatedResponse from an array of items */
export function paginated<T>(items: T[], total?: number): PaginatedResponse<T> {
  return {
    items,
    meta: { total: total ?? items.length, offset: 0, limit: 20 }
  };
}
