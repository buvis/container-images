import { render, screen, waitFor } from '@testing-library/svelte';
import { setVaultParams } from '$tests/helpers';
import { makeContactMethod } from '$tests/fixtures';
import ContactMethodsSection from './ContactMethodsSection.svelte';

const mockListMethods = vi.fn();
const mockCreateMethod = vi.fn();
const mockUpdateMethod = vi.fn();
const mockDeleteMethod = vi.fn();

vi.mock('$api/contacts', () => ({
  contactsApi: {
    listMethods: (...args: unknown[]) => mockListMethods(...args),
    createMethod: (...args: unknown[]) => mockCreateMethod(...args),
    updateMethod: (...args: unknown[]) => mockUpdateMethod(...args),
    deleteMethod: (...args: unknown[]) => mockDeleteMethod(...args)
  }
}));

vi.mock('lucide-svelte', () => ({
  Plus: () => {},
  Trash2: () => {},
  Phone: () => {},
  Mail: () => {},
  Globe: () => {}
}));

vi.mock('$components/ui/Button.svelte', () => ({ default: () => {} }));

beforeEach(() => {
  setVaultParams('vault-1', { contactId: 'contact-1' });
  mockListMethods.mockReset();
  mockCreateMethod.mockReset();
  mockUpdateMethod.mockReset();
  mockDeleteMethod.mockReset();
});

describe('ContactMethodsSection', () => {
  it('renders items from API', async () => {
    const method = makeContactMethod({ value: 'jane@test.dev', type: 'email' });
    mockListMethods.mockResolvedValue([method]);

    render(ContactMethodsSection, { vaultId: 'vault-1', contactId: 'contact-1' });

    await waitFor(() => {
      expect(screen.getByText('jane@test.dev')).toBeInTheDocument();
    });
  });

  it('shows empty state when no items', async () => {
    mockListMethods.mockResolvedValue([]);

    render(ContactMethodsSection, { vaultId: 'vault-1', contactId: 'contact-1' });

    await waitFor(() => {
      expect(screen.getByText('No contact methods yet')).toBeInTheDocument();
    });
  });

  it('has add button', async () => {
    mockListMethods.mockResolvedValue([]);

    render(ContactMethodsSection, { vaultId: 'vault-1', contactId: 'contact-1' });

    await waitFor(() => {
      expect(screen.getByRole('button')).toBeInTheDocument();
    });
  });
});
