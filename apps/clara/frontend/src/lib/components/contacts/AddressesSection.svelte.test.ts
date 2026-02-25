import { render, screen, waitFor } from '@testing-library/svelte';
import { setVaultParams } from '$tests/helpers';
import { makeAddress } from '$tests/fixtures';
import AddressesSection from './AddressesSection.svelte';

const mockListAddresses = vi.fn();
const mockCreateAddress = vi.fn();
const mockUpdateAddress = vi.fn();
const mockDeleteAddress = vi.fn();

vi.mock('$api/contacts', () => ({
  contactsApi: {
    listAddresses: (...args: unknown[]) => mockListAddresses(...args),
    createAddress: (...args: unknown[]) => mockCreateAddress(...args),
    updateAddress: (...args: unknown[]) => mockUpdateAddress(...args),
    deleteAddress: (...args: unknown[]) => mockDeleteAddress(...args)
  }
}));

vi.mock('lucide-svelte', () => ({
  Plus: () => {},
  Trash2: () => {},
  MapPin: () => {}
}));

vi.mock('$components/ui/Button.svelte', () => ({ default: () => {} }));

beforeEach(() => {
  setVaultParams('vault-1', { contactId: 'contact-1' });
  mockListAddresses.mockReset();
  mockCreateAddress.mockReset();
  mockUpdateAddress.mockReset();
  mockDeleteAddress.mockReset();
});

describe('AddressesSection', () => {
  it('renders items from API', async () => {
    const address = makeAddress({
      line1: '221B Baker Street',
      city: 'London',
      postal_code: 'NW1',
      country: 'UK'
    });
    mockListAddresses.mockResolvedValue([address]);

    render(AddressesSection, { vaultId: 'vault-1', contactId: 'contact-1' });

    await waitFor(() => {
      expect(screen.getByText('221B Baker Street, London, NW1, UK')).toBeInTheDocument();
    });
  });

  it('shows empty state when no items', async () => {
    mockListAddresses.mockResolvedValue([]);

    render(AddressesSection, { vaultId: 'vault-1', contactId: 'contact-1' });

    await waitFor(() => {
      expect(screen.getByText('No addresses yet')).toBeInTheDocument();
    });
  });

  it('has add button', async () => {
    mockListAddresses.mockResolvedValue([]);

    render(AddressesSection, { vaultId: 'vault-1', contactId: 'contact-1' });

    await waitFor(() => {
      expect(screen.getByRole('button')).toBeInTheDocument();
    });
  });
});
