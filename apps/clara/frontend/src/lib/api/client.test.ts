import { api, qs, ApiClientError } from './client';
import { goto } from '$app/navigation';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' }
  });
}

beforeEach(() => {
  mockFetch.mockReset();
  vi.mocked(goto).mockReset();
  // Clear cookies
  Object.defineProperty(document, 'cookie', { value: '', writable: true });
});

describe('ApiClient', () => {
  it('GET sends correct request', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ ok: true }));
    const res = await api.get('/test');
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/test', {
      method: 'GET',
      headers: {},
      credentials: 'include',
      body: undefined
    });
    expect(res).toEqual({ ok: true });
  });

  it('POST sends JSON body', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ id: 1 }));
    await api.post('/items', { name: 'test' });
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/items', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: '{"name":"test"}'
    });
  });

  it('includes CSRF header for state-changing requests', async () => {
    document.cookie = 'csrf_token=abc123';
    mockFetch.mockResolvedValue(jsonResponse({}));
    await api.post('/test', {});
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/test',
      expect.objectContaining({
        headers: expect.objectContaining({ 'x-csrf-token': 'abc123' })
      })
    );
  });

  it('401 redirects to login and throws', async () => {
    mockFetch.mockResolvedValue(new Response(null, { status: 401 }));
    await expect(api.get('/protected')).rejects.toThrow(ApiClientError);
    expect(goto).toHaveBeenCalledWith('/auth/login');
  });

  it('204 returns undefined', async () => {
    mockFetch.mockResolvedValue(new Response(null, { status: 204 }));
    const res = await api.del('/items/1');
    expect(res).toBeUndefined();
  });

  it('error response throws with detail', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ detail: 'Not found' }, 404));
    await expect(api.get('/missing')).rejects.toThrow('Not found');
  });
});

describe('qs', () => {
  it('builds query string from params', () => {
    expect(qs({ a: 'one', b: 2 })).toBe('?a=one&b=2');
  });

  it('omits null/undefined/empty values', () => {
    expect(qs({ a: 'ok', b: null, c: undefined, d: '' })).toBe('?a=ok');
  });

  it('returns empty string when no valid params', () => {
    expect(qs({ a: null, b: undefined })).toBe('');
  });
});
