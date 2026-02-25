import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import { paginated, setVaultParams } from '$tests/helpers';
import { makeGift } from '$tests/fixtures';
import GiftsPage from './+page.svelte';

const mockList = vi.fn();
const mockCreate = vi.fn();

vi.mock('$api/gifts', () => ({
  giftsApi: {
    list: (...args: unknown[]) => mockList(...args),
    create: (...args: unknown[]) => mockCreate(...args),
    update: vi.fn(),
    del: vi.fn()
  }
}));

vi.mock('$state/lookup.svelte', () => ({
  lookup: { contacts: [], loadContacts: vi.fn() }
}));

beforeEach(() => {
  mockList.mockReset().mockResolvedValue(paginated([]));
  mockCreate.mockReset();
  setVaultParams('v1');
});

describe('Gifts list page', () => {
  it('renders gifts from API', async () => {
    mockList.mockResolvedValue(paginated([makeGift({ name: 'Book' })]));
    render(GiftsPage);
    await waitFor(() => expect(screen.getByText('Book')).toBeInTheDocument());
  });

  it('shows empty state', async () => {
    render(GiftsPage);
    await waitFor(() => expect(screen.getByText('No gifts yet')).toBeInTheDocument());
  });

  it('has add gift button', () => {
    render(GiftsPage);
    expect(screen.getByText('Add Gift')).toBeInTheDocument();
  });

  it('has direction filters', () => {
    render(GiftsPage);
    expect(screen.getByText('Given')).toBeInTheDocument();
    expect(screen.getByText('Received')).toBeInTheDocument();
    expect(screen.getByText('Ideas')).toBeInTheDocument();
  });

  it('opens create modal', async () => {
    render(GiftsPage);
    await fireEvent.click(screen.getByText('Add Gift'));
    await waitFor(() => expect(screen.getByText('New Gift')).toBeInTheDocument());
  });

  it('displays direction badge', async () => {
    mockList.mockResolvedValue(paginated([makeGift({ name: 'Flowers', direction: 'given' })]));
    render(GiftsPage);
    await waitFor(() => expect(screen.getByText('given')).toBeInTheDocument());
  });
});
