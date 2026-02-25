import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

// Mock $app/navigation
vi.mock('$app/navigation', () => ({
  goto: vi.fn(),
  invalidate: vi.fn(),
  invalidateAll: vi.fn(),
  afterNavigate: vi.fn(),
  beforeNavigate: vi.fn(),
  onNavigate: vi.fn()
}));

// Mock $app/state — mutable so tests can set params/url
export const mockPage = {
  params: {} as Record<string, string>,
  url: new URL('http://localhost'),
  route: { id: '' },
  status: 200,
  error: null,
  data: {},
  form: null
};

vi.mock('$app/state', () => ({
  page: mockPage
}));
