import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import { goto } from '$app/navigation';
import { paginated, setVaultParams } from '$tests/helpers';
import { makeJournalEntry } from '$tests/fixtures';
import JournalPage from './+page.svelte';

const mockList = vi.fn();
const mockCreate = vi.fn();

vi.mock('$api/journal', () => ({
  journalApi: {
    list: (...args: unknown[]) => mockList(...args),
    create: (...args: unknown[]) => mockCreate(...args)
  }
}));

beforeEach(() => {
  mockList.mockReset().mockResolvedValue(paginated([]));
  mockCreate.mockReset();
  vi.mocked(goto).mockReset();
  setVaultParams('v1');
});

describe('Journal list page', () => {
  it('renders journal entries', async () => {
    const entries = [makeJournalEntry({ title: 'Good day' })];
    mockList.mockResolvedValue(paginated(entries));
    render(JournalPage);
    await waitFor(() => expect(screen.getByText('Good day')).toBeInTheDocument());
  });

  it('shows empty state', async () => {
    render(JournalPage);
    await waitFor(() => expect(screen.getByText('No journal entries yet')).toBeInTheDocument());
  });

  it('has new entry button', () => {
    render(JournalPage);
    expect(screen.getByText('New Entry')).toBeInTheDocument();
  });

  it('opens create modal and submits', async () => {
    const entry = makeJournalEntry({ id: 'j1' });
    mockCreate.mockResolvedValue(entry);
    render(JournalPage);
    await fireEvent.click(screen.getByText('New Entry'));
    await waitFor(() => expect(screen.getByText('New Journal Entry')).toBeInTheDocument());
    await fireEvent.submit(document.querySelector('form')!);
    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalled();
      expect(goto).toHaveBeenCalledWith('/vaults/v1/journal/j1');
    });
  });

  it('displays mood emojis', async () => {
    mockList.mockResolvedValue(paginated([makeJournalEntry({ title: 'Happy', mood: 5 })]));
    render(JournalPage);
    await waitFor(() => expect(screen.getByText('\u{1F604}')).toBeInTheDocument());
  });
});
