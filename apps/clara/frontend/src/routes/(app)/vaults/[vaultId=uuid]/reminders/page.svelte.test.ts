import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import { paginated, setVaultParams } from '$tests/helpers';
import { makeReminder } from '$tests/fixtures';
import RemindersPage from './+page.svelte';

const mockList = vi.fn();
const mockCreate = vi.fn();
const mockUpdate = vi.fn();

vi.mock('$api/reminders', () => ({
  remindersApi: {
    list: (...args: unknown[]) => mockList(...args),
    create: (...args: unknown[]) => mockCreate(...args),
    update: (...args: unknown[]) => mockUpdate(...args),
    del: vi.fn()
  }
}));

vi.mock('$state/lookup.svelte', () => ({
  lookup: { contacts: [], loadContacts: vi.fn() }
}));

beforeEach(() => {
  mockList.mockReset().mockResolvedValue(paginated([]));
  mockCreate.mockReset();
  mockUpdate.mockReset();
  setVaultParams('v1');
});

describe('Reminders list page', () => {
  it('renders reminders from API', async () => {
    mockList.mockResolvedValue(paginated([makeReminder({ title: 'Call mom' })]));
    render(RemindersPage);
    await waitFor(() => expect(screen.getByText('Call mom')).toBeInTheDocument());
  });

  it('shows empty state', async () => {
    render(RemindersPage);
    await waitFor(() => expect(screen.getByText('No reminders')).toBeInTheDocument());
  });

  it('has add reminder button', () => {
    render(RemindersPage);
    expect(screen.getByText('Add Reminder')).toBeInTheDocument();
  });

  it('has status filters', () => {
    render(RemindersPage);
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('opens create modal', async () => {
    render(RemindersPage);
    await fireEvent.click(screen.getByText('Add Reminder'));
    await waitFor(() => expect(screen.getByText('New Reminder')).toBeInTheDocument());
  });

  it('shows frequency badges', async () => {
    mockList.mockResolvedValue(paginated([makeReminder({ title: 'Weekly check', frequency_type: 'week' })]));
    render(RemindersPage);
    await waitFor(() => expect(screen.getByText('Weekly')).toBeInTheDocument());
  });

  it('shows Done button for active reminders', async () => {
    mockList.mockResolvedValue(paginated([makeReminder({ title: 'Active one', status: 'active' })]));
    render(RemindersPage);
    await waitFor(() => expect(screen.getByText('Done')).toBeInTheDocument());
  });
});
