export interface PaginationMeta {
  total: number;
  offset: number;
  limit: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  meta: PaginationMeta;
}

export interface ApiError {
  detail: string;
}
