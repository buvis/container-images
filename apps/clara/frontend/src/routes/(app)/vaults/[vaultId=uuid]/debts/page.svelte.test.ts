import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import { paginated, setVaultParams } from '$tests/helpers';
import { makeDebt } from '$tests/fixtures';
import DebtsPage from './+page.svelte';

const mockList = vi.fn();
const mockCreate = vi.fn();
const mockUpdate = vi.fn();

vi.mock('$api/debts', () => ({
  debtsApi: {
    list: (...args: unknown[]) => mockList(...args),
    create: (...args: unknown[]) => mockCreate(...args),
    update: (...args: unknown[]) => mockUpdate(...args),
    del: vi.fn()
  }
}));

vi.mock('$state/lookup.svelte', () => ({
  lookup: { contacts: [], loadContacts: vi.fn(), getContactName: () => 'Jane' }
}));

beforeEach(() => {
  mockList.mockReset().mockResolvedValue(paginated([]));
  mockCreate.mockReset();
  mockUpdate.mockReset();
  setVaultParams('v1');
});

describe('Debts list page', () => {
  it('renders debts from API', async () => {
    mockList.mockResolvedValue(paginated([makeDebt({ amount: 100, currency: 'USD' })]));
    render(DebtsPage);
    await waitFor(() => expect(screen.getByText('USD 100')).toBeInTheDocument());
  });

  it('shows empty state', async () => {
    render(DebtsPage);
    await waitFor(() => expect(screen.getByText('No debts')).toBeInTheDocument());
  });

  it('has add debt button', () => {
    render(DebtsPage);
    expect(screen.getByText('Add Debt')).toBeInTheDocument();
  });

  it('has direction filters', () => {
    render(DebtsPage);
    expect(screen.getByText('You Owe')).toBeInTheDocument();
    expect(screen.getByText('Owed to You')).toBeInTheDocument();
    expect(screen.getByText('Settled')).toBeInTheDocument();
  });

  it('opens create modal', async () => {
    render(DebtsPage);
    await fireEvent.click(screen.getByText('Add Debt'));
    await waitFor(() => expect(screen.getByText('New Debt')).toBeInTheDocument());
  });

  it('displays direction badge', async () => {
    mockList.mockResolvedValue(paginated([makeDebt({ direction: 'you_owe', amount: 50 })]));
    render(DebtsPage);
    await waitFor(() => expect(screen.getByText('You owe')).toBeInTheDocument());
  });

  it('shows settle button for unsettled debts', async () => {
    mockList.mockResolvedValue(paginated([makeDebt({ settled: false })]));
    render(DebtsPage);
    await waitFor(() => expect(screen.getByText('Settle')).toBeInTheDocument());
  });
});
