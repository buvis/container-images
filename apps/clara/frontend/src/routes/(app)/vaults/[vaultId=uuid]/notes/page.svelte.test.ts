import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import { paginated, setVaultParams } from '$tests/helpers';
import { makeNote } from '$tests/fixtures';
import NotesPage from './+page.svelte';

const mockList = vi.fn();
const mockCreate = vi.fn();

vi.mock('$api/notes', () => ({
  notesApi: {
    list: (...args: unknown[]) => mockList(...args),
    create: (...args: unknown[]) => mockCreate(...args),
    update: vi.fn(),
    del: vi.fn()
  }
}));

vi.mock('$api/contacts', () => ({
  contactsApi: {
    list: vi.fn().mockResolvedValue({ items: [], meta: { total: 0, offset: 0, limit: 20 } })
  }
}));

beforeEach(() => {
  mockList.mockReset().mockResolvedValue(paginated([]));
  mockCreate.mockReset();
  setVaultParams('v1');
});

describe('Notes list page', () => {
  it('renders notes from API', async () => {
    mockList.mockResolvedValue(paginated([makeNote({ title: 'Meeting notes' })]));
    render(NotesPage);
    await waitFor(() => expect(screen.getByText('Meeting notes')).toBeInTheDocument());
  });

  it('shows empty state', async () => {
    render(NotesPage);
    await waitFor(() => expect(screen.getByText('No notes yet')).toBeInTheDocument());
  });

  it('has new note button', () => {
    render(NotesPage);
    expect(screen.getByText('New Note')).toBeInTheDocument();
  });

  it('opens create modal', async () => {
    render(NotesPage);
    await fireEvent.click(screen.getByText('New Note'));
    await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument());
  });

  it('has contact filter dropdown', () => {
    render(NotesPage);
    expect(screen.getByText('All contacts')).toBeInTheDocument();
  });
});
