import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import { goto } from '$app/navigation';
import { paginated, setVaultParams } from '$tests/helpers';
import { makeContact } from '$tests/fixtures';
import ContactsPage from './+page.svelte';

const mockList = vi.fn();
const mockCreate = vi.fn();

vi.mock('$api/contacts', () => ({
  contactsApi: {
    list: (...args: unknown[]) => mockList(...args),
    create: (...args: unknown[]) => mockCreate(...args)
  }
}));

vi.mock('$components/contacts/ContactCard.svelte', () => ({ default: () => {} }));

beforeEach(() => {
  mockList.mockReset();
  mockCreate.mockReset();
  vi.mocked(goto).mockReset();
  setVaultParams('v1');
});

describe('Contacts list page', () => {
  it('renders contacts from API', async () => {
    const contacts = [makeContact({ first_name: 'Alice', last_name: 'Smith' }), makeContact({ first_name: 'Bob', last_name: 'Jones' })];
    mockList.mockResolvedValue(paginated(contacts));
    render(ContactsPage);
    await waitFor(() => expect(mockList).toHaveBeenCalledWith('v1', expect.anything()));
  });

  it('shows empty state when no contacts', async () => {
    mockList.mockResolvedValue(paginated([]));
    render(ContactsPage);
    await waitFor(() => expect(screen.getByText('No contacts yet')).toBeInTheDocument());
  });

  it('has add contact button', async () => {
    mockList.mockResolvedValue(paginated([]));
    render(ContactsPage);
    expect(screen.getByText('Add Contact')).toBeInTheDocument();
  });

  it('opens create modal and submits', async () => {
    mockList.mockResolvedValue(paginated([]));
    const newContact = makeContact({ id: 'new-id', first_name: 'Jane' });
    mockCreate.mockResolvedValue(newContact);
    render(ContactsPage);
    await fireEvent.click(screen.getByText('Add Contact'));
    await waitFor(() => expect(screen.getByText('New Contact')).toBeInTheDocument());
    await fireEvent.input(screen.getByLabelText('First name'), { target: { value: 'Jane' } });
    const form = document.querySelector('form')!;
    await fireEvent.submit(form);
    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalledWith('v1', expect.objectContaining({ first_name: 'Jane' }));
      expect(goto).toHaveBeenCalledWith('/vaults/v1/contacts/new-id');
    });
  });

  it('has favorites filter', async () => {
    mockList.mockResolvedValue(paginated([]));
    render(ContactsPage);
    expect(screen.getByText('Favorites')).toBeInTheDocument();
  });
});
