import { render, screen, waitFor } from '@testing-library/svelte';
import { setVaultParams } from '$tests/helpers';
import { makeJournalEntry } from '$tests/fixtures';
import JournalDetailPage from './+page.svelte';

const mockGet = vi.fn();

vi.mock('$api/journal', () => ({
  journalApi: {
    get: (...args: unknown[]) => mockGet(...args),
    update: vi.fn(),
    del: vi.fn()
  }
}));

const entry = makeJournalEntry({ id: 'j1', title: 'Reflections', body_markdown: 'Today was good', mood: 4 });

beforeEach(() => {
  mockGet.mockReset().mockResolvedValue(entry);
  setVaultParams('v1', { entryId: 'j1' });
});

describe('Journal detail page', () => {
  it('loads and displays entry', async () => {
    render(JournalDetailPage);
    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('v1', 'j1');
      expect(screen.getByText('Reflections')).toBeInTheDocument();
    });
  });

  it('shows spinner while loading', () => {
    mockGet.mockReturnValue(new Promise(() => {}));
    render(JournalDetailPage);
    expect(screen.getByLabelText('Loading')).toBeInTheDocument();
  });

  it('displays body content', async () => {
    render(JournalDetailPage);
    await waitFor(() => expect(screen.getByText('Today was good')).toBeInTheDocument());
  });

  it('displays mood emoji', async () => {
    render(JournalDetailPage);
    await waitFor(() => expect(screen.getByText('\u{1F642}')).toBeInTheDocument());
  });

  it('shows error on load failure', async () => {
    mockGet.mockRejectedValue(new Error('Network error'));
    render(JournalDetailPage);
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
      expect(screen.getByText('Go back')).toBeInTheDocument();
    });
    expect(screen.queryByLabelText('Loading')).not.toBeInTheDocument();
  });
});
