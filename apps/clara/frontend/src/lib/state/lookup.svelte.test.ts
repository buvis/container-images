import { api } from '$api/client';

vi.mock('$api/client', () => ({
  api: {
    get: vi.fn()
  }
}));

let lookupState: any;

beforeEach(async () => {
  vi.mocked(api.get).mockReset();
  vi.resetModules();
  const mod = await import('./lookup.svelte');
  lookupState = mod.lookup;
});

describe('LookupState', () => {
  it('loadContacts populates lookup', async () => {
    vi.mocked(api.get).mockResolvedValue({
      items: [
        { id: 'c1', first_name: 'Alice', last_name: 'Smith' },
        { id: 'c2', first_name: 'Bob', last_name: 'Jones' }
      ],
      meta: { total: 2, offset: 0, limit: 1000 }
    });
    await lookupState.loadContacts('v1');
    expect(api.get).toHaveBeenCalledWith('/vaults/v1/contacts?limit=1000');
    expect(lookupState.contacts).toEqual([
      { id: 'c1', name: 'Alice Smith' },
      { id: 'c2', name: 'Bob Jones' }
    ]);
  });

  it('loadContacts skips refetch for same vault', async () => {
    vi.mocked(api.get).mockResolvedValue({
      items: [{ id: 'c1', first_name: 'Alice', last_name: 'Smith' }],
      meta: { total: 1, offset: 0, limit: 1000 }
    });
    await lookupState.loadContacts('v1');
    await lookupState.loadContacts('v1');
    expect(api.get).toHaveBeenCalledTimes(1);
  });

  it('loadContacts refetches for different vault', async () => {
    vi.mocked(api.get).mockResolvedValue({
      items: [],
      meta: { total: 0, offset: 0, limit: 1000 }
    });
    await lookupState.loadContacts('v1');
    await lookupState.loadContacts('v2');
    expect(api.get).toHaveBeenCalledTimes(2);
  });

  it('getContactName returns name for known ID', async () => {
    vi.mocked(api.get).mockResolvedValue({
      items: [{ id: 'c1', first_name: 'Alice', last_name: 'Smith' }],
      meta: { total: 1, offset: 0, limit: 1000 }
    });
    await lookupState.loadContacts('v1');
    expect(lookupState.getContactName('c1')).toBe('Alice Smith');
  });

  it('getContactName returns Unknown for missing ID', () => {
    expect(lookupState.getContactName('missing')).toBe('Unknown');
  });

  it('invalidate resets cached data', async () => {
    vi.mocked(api.get).mockResolvedValue({
      items: [{ id: 'c1', first_name: 'Alice', last_name: 'Smith' }],
      meta: { total: 1, offset: 0, limit: 1000 }
    });
    await lookupState.loadContacts('v1');
    expect(lookupState.contacts.length).toBe(1);
    lookupState.invalidate();
    expect(lookupState.contacts).toEqual([]);
    expect(lookupState.activityTypes).toEqual([]);
    // After invalidate, same vault refetches
    vi.mocked(api.get).mockResolvedValue({
      items: [],
      meta: { total: 0, offset: 0, limit: 1000 }
    });
    await lookupState.loadContacts('v1');
    expect(api.get).toHaveBeenCalledTimes(2);
  });

  it('loadContacts clears on error', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('fail'));
    await lookupState.loadContacts('v1');
    expect(lookupState.contacts).toEqual([]);
  });
});
