import { render, screen, waitFor } from '@testing-library/svelte';
import { mockPage } from '$tests/setup';
import Topbar from './Topbar.svelte';

const mockList = vi.fn();
const mockUnreadCount = vi.fn();

vi.mock('$api/notifications', () => ({
  notificationsApi: {
    list: (...args: unknown[]) => mockList(...args),
    unreadCount: (...args: unknown[]) => mockUnreadCount(...args),
    markRead: vi.fn(),
    markAllRead: vi.fn()
  }
}));

vi.mock('$state/auth.svelte', () => ({
  auth: {
    user: { name: 'Alice', email: 'alice@test.com' },
    logout: vi.fn()
  }
}));

vi.mock('$state/vault.svelte', () => ({
  vaultState: {
    currentId: 'v1',
    vaults: [
      { id: 'v1', name: 'Personal', created_at: '' },
      { id: 'v2', name: 'Work', created_at: '' }
    ],
    setCurrent: vi.fn()
  }
}));

beforeEach(() => {
  mockList.mockReset().mockResolvedValue([]);
  mockUnreadCount.mockReset().mockResolvedValue({ count: 0 });
  mockPage.params = { vaultId: 'v1' };
});

describe('Topbar', () => {
  it('shows vault name in dropdown', async () => {
    render(Topbar, { ontogglesidebar: vi.fn() });
    await waitFor(() => {
      expect(screen.getByDisplayValue('Personal')).toBeInTheDocument();
    });
  });

  it('shows user name', () => {
    render(Topbar, { ontogglesidebar: vi.fn() });
    expect(screen.getByText('Alice')).toBeInTheDocument();
  });

  it('shows notification badge count', async () => {
    mockUnreadCount.mockResolvedValue({ count: 5 });
    render(Topbar, { ontogglesidebar: vi.fn() });
    await waitFor(() => {
      expect(screen.getByText('5')).toBeInTheDocument();
    });
  });

  it('caps badge at 99+', async () => {
    mockUnreadCount.mockResolvedValue({ count: 150 });
    render(Topbar, { ontogglesidebar: vi.fn() });
    await waitFor(() => {
      expect(screen.getByText('99+')).toBeInTheDocument();
    });
  });

  it('hides badge when zero unread', async () => {
    render(Topbar, { ontogglesidebar: vi.fn() });
    await waitFor(() => {
      expect(mockUnreadCount).toHaveBeenCalled();
    });
    expect(screen.queryByText('0')).not.toBeInTheDocument();
  });

  it('shows user initial in avatar', () => {
    render(Topbar, { ontogglesidebar: vi.fn() });
    expect(screen.getByText('A')).toBeInTheDocument();
  });
});
