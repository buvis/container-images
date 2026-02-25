import { render, screen, waitFor } from '@testing-library/svelte';
import { setVaultParams } from '$tests/helpers';
import { makeTask } from '$tests/fixtures';
import TaskDetailPage from './+page.svelte';

const mockGet = vi.fn();
const mockUpdate = vi.fn();
const mockDel = vi.fn();

vi.mock('$api/tasks', () => ({
  tasksApi: {
    get: (...args: unknown[]) => mockGet(...args),
    update: (...args: unknown[]) => mockUpdate(...args),
    del: (...args: unknown[]) => mockDel(...args)
  }
}));

vi.mock('$state/lookup.svelte', () => ({
  lookup: { contacts: [], activities: [], loadContacts: vi.fn(), loadActivities: vi.fn(), getContactName: () => 'Unknown' }
}));

vi.mock('$components/customization/CustomFieldsSection.svelte', () => ({ default: () => {} }));

const task = makeTask({ id: 't1', title: 'Fix bug', status: 'pending', priority: 2, description: 'Details here' });

beforeEach(() => {
  mockGet.mockReset().mockResolvedValue(task);
  mockUpdate.mockReset();
  mockDel.mockReset();
  setVaultParams('v1', { taskId: 't1' });
});

describe('Task detail page', () => {
  it('loads and displays task', async () => {
    render(TaskDetailPage);
    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('v1', 't1');
      expect(screen.getByText('Fix bug')).toBeInTheDocument();
    });
  });

  it('shows spinner while loading', () => {
    mockGet.mockReturnValue(new Promise(() => {}));
    render(TaskDetailPage);
    expect(screen.getByLabelText('Loading')).toBeInTheDocument();
  });

  it('displays status and priority badges', async () => {
    render(TaskDetailPage);
    await waitFor(() => {
      expect(screen.getByText('pending')).toBeInTheDocument();
      expect(screen.getByText('Medium')).toBeInTheDocument();
    });
  });

  it('displays description', async () => {
    render(TaskDetailPage);
    await waitFor(() => expect(screen.getByText('Details here')).toBeInTheDocument());
  });

  it('shows no description message when empty', async () => {
    mockGet.mockResolvedValue({ ...task, description: null });
    render(TaskDetailPage);
    await waitFor(() => expect(screen.getByText('No description provided.')).toBeInTheDocument());
  });

  it('shows error on load failure', async () => {
    mockGet.mockRejectedValue(new Error('Network error'));
    render(TaskDetailPage);
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
      expect(screen.getByText('Go back')).toBeInTheDocument();
    });
    expect(screen.queryByLabelText('Loading')).not.toBeInTheDocument();
  });
});
