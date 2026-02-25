import { render, screen, waitFor } from '@testing-library/svelte';
import { setVaultParams } from '$tests/helpers';
import { makeTag } from '$tests/fixtures';
import TagsSection from './TagsSection.svelte';

const mockListTags = vi.fn();
const mockAddTag = vi.fn();
const mockRemoveTag = vi.fn();
const mockListAllTags = vi.fn();
const mockCreateTag = vi.fn();

vi.mock('$api/contacts', () => ({
  contactsApi: {
    listTags: (...args: unknown[]) => mockListTags(...args),
    addTag: (...args: unknown[]) => mockAddTag(...args),
    removeTag: (...args: unknown[]) => mockRemoveTag(...args)
  },
  tagsApi: {
    list: (...args: unknown[]) => mockListAllTags(...args),
    create: (...args: unknown[]) => mockCreateTag(...args)
  }
}));

vi.mock('lucide-svelte', () => ({
  Plus: () => {},
  X: () => {}
}));

vi.mock('$components/ui/Button.svelte', () => ({ default: () => {} }));

beforeEach(() => {
  setVaultParams('vault-1', { contactId: 'contact-1' });
  mockListTags.mockReset();
  mockAddTag.mockReset();
  mockRemoveTag.mockReset();
  mockListAllTags.mockReset();
  mockCreateTag.mockReset();
});

describe('TagsSection', () => {
  it('renders items from API', async () => {
    const tag = makeTag({ name: 'Friends' });
    mockListTags.mockResolvedValue([tag]);
    mockListAllTags.mockResolvedValue([tag]);

    render(TagsSection, { vaultId: 'vault-1', contactId: 'contact-1' });

    await waitFor(() => {
      expect(screen.getByText('Friends')).toBeInTheDocument();
    });
  });

  it('shows empty state when no items', async () => {
    mockListTags.mockResolvedValue([]);
    mockListAllTags.mockResolvedValue([]);

    render(TagsSection, { vaultId: 'vault-1', contactId: 'contact-1' });

    await waitFor(() => {
      expect(screen.getByText('No tags yet')).toBeInTheDocument();
    });
  });

  it('has add button', async () => {
    mockListTags.mockResolvedValue([]);
    mockListAllTags.mockResolvedValue([]);

    render(TagsSection, { vaultId: 'vault-1', contactId: 'contact-1' });

    await waitFor(() => {
      expect(screen.getByRole('button')).toBeInTheDocument();
    });
  });
});
