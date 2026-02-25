import { render, screen, waitFor } from '@testing-library/svelte';
import { setVaultParams } from '$tests/helpers';
import { makeActivity } from '$tests/fixtures';
import ActivityDetailPage from './+page.svelte';

const mockGet = vi.fn();

vi.mock('$api/activities', () => ({
  activitiesApi: {
    get: (...args: unknown[]) => mockGet(...args),
    update: vi.fn(),
    del: vi.fn()
  }
}));

vi.mock('$state/lookup.svelte', () => ({
  lookup: {
    contacts: [],
    activityTypes: [],
    loadContacts: vi.fn(),
    loadActivityTypes: vi.fn(),
    getContactName: () => 'Unknown'
  }
}));

vi.mock('$components/activities/ParticipantsEditor.svelte', () => ({ default: () => {} }));
vi.mock('$components/customization/CustomFieldsSection.svelte', () => ({ default: () => {} }));

const activity = makeActivity({ id: 'a1', title: 'Team meeting', description: 'Weekly sync', location: 'Office' });

beforeEach(() => {
  mockGet.mockReset().mockResolvedValue(activity);
  setVaultParams('v1', { activityId: 'a1' });
});

describe('Activity detail page', () => {
  it('loads and displays activity', async () => {
    render(ActivityDetailPage);
    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('v1', 'a1');
      expect(screen.getByText('Team meeting')).toBeInTheDocument();
    });
  });

  it('shows spinner while loading', () => {
    mockGet.mockReturnValue(new Promise(() => {}));
    render(ActivityDetailPage);
    expect(screen.getByLabelText('Loading')).toBeInTheDocument();
  });

  it('displays location and description', async () => {
    render(ActivityDetailPage);
    await waitFor(() => {
      expect(screen.getByText('Office')).toBeInTheDocument();
      expect(screen.getByText('Weekly sync')).toBeInTheDocument();
    });
  });

  it('shows error on load failure', async () => {
    mockGet.mockRejectedValue(new Error('Network error'));
    render(ActivityDetailPage);
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
      expect(screen.getByText('Go back')).toBeInTheDocument();
    });
    expect(screen.queryByLabelText('Loading')).not.toBeInTheDocument();
  });
});
