import { render, screen } from '@testing-library/svelte';
import { mockPage } from '$tests/setup';
import Sidebar from './Sidebar.svelte';

const mockLoadFeatureFlags = vi.fn();

vi.mock('$state/vault.svelte', () => ({
  vaultState: {
    currentId: 'v1',
    featureFlags: { debts: true, gifts: true, pets: true, journal: true },
    loadFeatureFlags: (...args: unknown[]) => mockLoadFeatureFlags(...args)
  }
}));

beforeEach(() => {
  mockLoadFeatureFlags.mockReset();
  mockPage.url = new URL('http://localhost/vaults/v1/dashboard');
});

describe('Sidebar', () => {
  it('renders nav items', () => {
    render(Sidebar);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Contacts')).toBeInTheDocument();
    expect(screen.getByText('Tasks')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('renders CLARA brand link', () => {
    render(Sidebar);
    expect(screen.getByText('CLARA')).toBeInTheDocument();
  });

  it('highlights active route', () => {
    mockPage.url = new URL('http://localhost/vaults/v1/contacts');
    render(Sidebar);
    const contactsLink = screen.getByText('Contacts').closest('a')!;
    expect(contactsLink.className).toContain('bg-brand-500/10');
    const tasksLink = screen.getByText('Tasks').closest('a')!;
    expect(tasksLink.className).not.toContain('bg-brand-500/10');
  });

  it('hides items when feature flag disabled', async () => {
    const { vaultState } = await import('$state/vault.svelte');
    (vaultState as any).featureFlags = { debts: false, gifts: false, pets: true, journal: false };
    render(Sidebar);
    expect(screen.queryByText('Debts')).not.toBeInTheDocument();
    expect(screen.queryByText('Gifts')).not.toBeInTheDocument();
    expect(screen.queryByText('Journal')).not.toBeInTheDocument();
    // Non-flagged items still visible
    expect(screen.getByText('Contacts')).toBeInTheDocument();
  });

  it('shows flagged items when enabled', async () => {
    const { vaultState } = await import('$state/vault.svelte');
    (vaultState as any).featureFlags = { debts: true, gifts: true, pets: true, journal: true };
    render(Sidebar);
    expect(screen.getByText('Debts')).toBeInTheDocument();
    expect(screen.getByText('Gifts')).toBeInTheDocument();
    expect(screen.getByText('Journal')).toBeInTheDocument();
  });

  it('builds links with vault basePath', () => {
    render(Sidebar);
    const link = screen.getByText('Contacts').closest('a')!;
    expect(link).toHaveAttribute('href', '/vaults/v1/contacts');
  });
});
