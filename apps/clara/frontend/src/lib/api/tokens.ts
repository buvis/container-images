import { api } from '$api/client';
import type { PersonalAccessToken } from '$lib/types/models';

export interface PatCreateInput {
  name: string;
  scopes: string[];
  expires_at?: string | null;
}

export interface PatCreateResponse extends PersonalAccessToken {
  token: string;
}

export const tokensApi = {
  list() {
    return api.get<PersonalAccessToken[]>('/auth/tokens');
  },

  create(data: PatCreateInput) {
    return api.post<PatCreateResponse>('/auth/tokens', data);
  },

  revoke(tokenId: string) {
    return api.del(`/auth/tokens/${tokenId}`);
  }
};
