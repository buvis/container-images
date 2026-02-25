import { render, screen, waitFor } from '@testing-library/svelte';
import { setVaultParams } from '$tests/helpers';
import { makePet } from '$tests/fixtures';
import PetsSection from './PetsSection.svelte';

const mockListPets = vi.fn();
const mockCreatePet = vi.fn();
const mockUpdatePet = vi.fn();
const mockDeletePet = vi.fn();

vi.mock('$api/contacts', () => ({
  contactsApi: {
    listPets: (...args: unknown[]) => mockListPets(...args),
    createPet: (...args: unknown[]) => mockCreatePet(...args),
    updatePet: (...args: unknown[]) => mockUpdatePet(...args),
    deletePet: (...args: unknown[]) => mockDeletePet(...args)
  }
}));

vi.mock('lucide-svelte', () => ({
  Plus: () => {},
  Trash2: () => {},
  PawPrint: () => {}
}));

vi.mock('$components/ui/Button.svelte', () => ({ default: () => {} }));

beforeEach(() => {
  setVaultParams('vault-1', { contactId: 'contact-1' });
  mockListPets.mockReset();
  mockCreatePet.mockReset();
  mockUpdatePet.mockReset();
  mockDeletePet.mockReset();
});

describe('PetsSection', () => {
  it('renders items from API', async () => {
    const pet = makePet({ name: 'Luna', species: 'Dog' });
    mockListPets.mockResolvedValue([pet]);

    render(PetsSection, { vaultId: 'vault-1', contactId: 'contact-1' });

    await waitFor(() => {
      expect(screen.getByText('Luna')).toBeInTheDocument();
      expect(screen.getByText('Dog')).toBeInTheDocument();
    });
  });

  it('shows empty state when no items', async () => {
    mockListPets.mockResolvedValue([]);

    render(PetsSection, { vaultId: 'vault-1', contactId: 'contact-1' });

    await waitFor(() => {
      expect(screen.getByText('No pets yet')).toBeInTheDocument();
    });
  });

  it('has add button', async () => {
    mockListPets.mockResolvedValue([]);

    render(PetsSection, { vaultId: 'vault-1', contactId: 'contact-1' });

    await waitFor(() => {
      expect(screen.getByRole('button')).toBeInTheDocument();
    });
  });
});
