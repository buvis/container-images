import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import { paginated, setVaultParams } from '$tests/helpers';
import { makeTask } from '$tests/fixtures';
import TasksPage from './+page.svelte';

const mockList = vi.fn();
const mockCreate = vi.fn();
const mockUpdate = vi.fn();
const mockDel = vi.fn();

vi.mock('$api/tasks', () => ({
  tasksApi: {
    list: (...args: unknown[]) => mockList(...args),
    create: (...args: unknown[]) => mockCreate(...args),
    update: (...args: unknown[]) => mockUpdate(...args),
    del: (...args: unknown[]) => mockDel(...args)
  }
}));

vi.mock('$state/lookup.svelte', () => ({
  lookup: { contacts: [], activities: [], loadContacts: vi.fn(), loadActivities: vi.fn() }
}));

beforeEach(() => {
  mockList.mockReset().mockResolvedValue(paginated([]));
  mockCreate.mockReset();
  mockUpdate.mockReset();
  mockDel.mockReset();
  setVaultParams('v1');
});

describe('Tasks list page', () => {
  it('renders tasks from API', async () => {
    const tasks = [makeTask({ title: 'Buy groceries' }), makeTask({ title: 'Call dentist' })];
    mockList.mockResolvedValue(paginated(tasks));
    render(TasksPage);
    await waitFor(() => {
      expect(screen.getByText('Buy groceries')).toBeInTheDocument();
      expect(screen.getByText('Call dentist')).toBeInTheDocument();
    });
  });

  it('shows empty state when no tasks', async () => {
    render(TasksPage);
    await waitFor(() => expect(screen.getByText('No tasks yet')).toBeInTheDocument());
  });

  it('has add task button', async () => {
    render(TasksPage);
    expect(screen.getByText('Add Task')).toBeInTheDocument();
  });

  it('opens create modal and submits', async () => {
    mockCreate.mockResolvedValue(makeTask({ title: 'New task' }));
    render(TasksPage);
    await fireEvent.click(screen.getByText('Add Task'));
    await waitFor(() => expect(screen.getByText('New Task')).toBeInTheDocument());
    await fireEvent.input(screen.getByLabelText('Title'), { target: { value: 'New task' } });
    await fireEvent.submit(document.querySelector('form')!);
    await waitFor(() => expect(mockCreate).toHaveBeenCalledWith('v1', expect.objectContaining({ title: 'New task' })));
  });

  it('has status filters', () => {
    render(TasksPage);
    expect(screen.getByText('Pending')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
    expect(screen.getByText('Done')).toBeInTheDocument();
    expect(screen.getByText('Overdue')).toBeInTheDocument();
  });

  it('displays priority badges', async () => {
    mockList.mockResolvedValue(paginated([makeTask({ title: 'Urgent', priority: 3 })]));
    render(TasksPage);
    await waitFor(() => expect(screen.getByText('High')).toBeInTheDocument());
  });
});
