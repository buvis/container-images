import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import { goto } from '$app/navigation';
import { setVaultParams } from '$tests/helpers';
import { makeContact } from '$tests/fixtures';
import ContactDetailPage from './+page.svelte';

const mockGet = vi.fn();
const mockUpdate = vi.fn();
const mockDel = vi.fn();

vi.mock('$api/contacts', () => ({
  contactsApi: {
    get: (...args: unknown[]) => mockGet(...args),
    update: (...args: unknown[]) => mockUpdate(...args),
    del: (...args: unknown[]) => mockDel(...args)
  }
}));

vi.mock('$api/notes', () => ({ notesApi: { forContact: vi.fn().mockResolvedValue({ items: [], meta: { total: 0, offset: 0, limit: 20 } }) } }));
vi.mock('$api/client', () => ({ api: { get: vi.fn().mockResolvedValue({ items: [], meta: { total: 0, offset: 0, limit: 20 } }) } }));
vi.mock('$api/files', () => ({ filesApi: { upload: vi.fn() } }));

vi.mock('$components/contacts/ContactMethodsSection.svelte', () => ({ default: () => {} }));
vi.mock('$components/contacts/AddressesSection.svelte', () => ({ default: () => {} }));
vi.mock('$components/contacts/PetsSection.svelte', () => ({ default: () => {} }));
vi.mock('$components/contacts/TagsSection.svelte', () => ({ default: () => {} }));
vi.mock('$components/contacts/RelationshipsSection.svelte', () => ({ default: () => {} }));
vi.mock('$components/customization/CustomFieldsSection.svelte', () => ({ default: () => {} }));
vi.mock('$components/contacts/ContactTabs.svelte', () => ({ default: () => {} }));

const contact = makeContact({ id: 'c1', first_name: 'Alice', last_name: 'Smith', favorite: false });

beforeEach(() => {
  mockGet.mockReset().mockResolvedValue(contact);
  mockUpdate.mockReset();
  mockDel.mockReset();
  vi.mocked(goto).mockReset();
  setVaultParams('v1', { contactId: 'c1' });
});

describe('Contact detail page', () => {
  it('loads and displays contact', async () => {
    render(ContactDetailPage);
    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('v1', 'c1');
      expect(screen.getByText('Alice Smith')).toBeInTheDocument();
    });
  });

  it('shows spinner while loading', () => {
    mockGet.mockReturnValue(new Promise(() => {}));
    render(ContactDetailPage);
    expect(screen.getByLabelText('Loading')).toBeInTheDocument();
  });

  it('toggles favorite', async () => {
    mockUpdate.mockResolvedValue({ ...contact, favorite: true });
    render(ContactDetailPage);
    await waitFor(() => expect(screen.getByText('Alice Smith')).toBeInTheDocument());
    await fireEvent.click(screen.getByLabelText('Toggle favorite'));
    await waitFor(() => expect(mockUpdate).toHaveBeenCalledWith('v1', 'c1', { favorite: true }));
  });

  it('shows initials avatar when no photo', async () => {
    render(ContactDetailPage);
    await waitFor(() => {
      expect(screen.getByText('AS')).toBeInTheDocument();
    });
  });

  it('displays nickname when present', async () => {
    mockGet.mockResolvedValue({ ...contact, nickname: 'Ali' });
    render(ContactDetailPage);
    await waitFor(() => expect(screen.getByText('"Ali"')).toBeInTheDocument());
  });

  it('shows error on load failure', async () => {
    mockGet.mockRejectedValue(new Error('Network error'));
    render(ContactDetailPage);
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
      expect(screen.getByText('Go back')).toBeInTheDocument();
    });
    expect(screen.queryByLabelText('Loading')).not.toBeInTheDocument();
  });
});
