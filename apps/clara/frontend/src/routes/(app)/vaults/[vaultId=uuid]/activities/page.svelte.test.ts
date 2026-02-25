import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import { paginated, setVaultParams } from '$tests/helpers';
import { makeActivity } from '$tests/fixtures';
import ActivitiesPage from './+page.svelte';

const mockList = vi.fn();
const mockCreate = vi.fn();
const mockDel = vi.fn();

vi.mock('$api/activities', () => ({
  activitiesApi: {
    list: (...args: unknown[]) => mockList(...args),
    create: (...args: unknown[]) => mockCreate(...args),
    update: vi.fn(),
    del: (...args: unknown[]) => mockDel(...args)
  }
}));

vi.mock('$state/lookup.svelte', () => ({
  lookup: { contacts: [], activityTypes: [], loadContacts: vi.fn(), loadActivityTypes: vi.fn() }
}));

vi.mock('$components/activities/ParticipantsEditor.svelte', () => ({ default: () => {} }));

beforeEach(() => {
  mockList.mockReset().mockResolvedValue(paginated([]));
  mockCreate.mockReset();
  mockDel.mockReset();
  setVaultParams('v1');
});

describe('Activities list page', () => {
  it('renders activities from API', async () => {
    const activities = [makeActivity({ title: 'Lunch with Bob' })];
    mockList.mockResolvedValue(paginated(activities));
    render(ActivitiesPage);
    await waitFor(() => expect(screen.getByText('Lunch with Bob')).toBeInTheDocument());
  });

  it('shows empty state when no activities', async () => {
    render(ActivitiesPage);
    await waitFor(() => expect(screen.getByText('No activities yet')).toBeInTheDocument());
  });

  it('has add activity button', () => {
    render(ActivitiesPage);
    expect(screen.getByText('Add Activity')).toBeInTheDocument();
  });

  it('opens create modal', async () => {
    render(ActivitiesPage);
    await fireEvent.click(screen.getByText('Add Activity'));
    await waitFor(() => expect(screen.getByText('New Activity')).toBeInTheDocument());
  });
});
