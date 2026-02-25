import { render, screen } from '@testing-library/svelte';
import { mockPage } from '$tests/setup';
import MobileNav from './MobileNav.svelte';

vi.mock('$state/vault.svelte', () => ({
  vaultState: {
    currentId: 'v1',
    featureFlags: { debts: true, gifts: true, pets: true, journal: true }
  }
}));

beforeEach(() => {
  mockPage.url = new URL('http://localhost/vaults/v1/dashboard');
});

describe('MobileNav', () => {
  it('renders nav items', () => {
    render(MobileNav);
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Contacts')).toBeInTheDocument();
    expect(screen.getByText('Tasks')).toBeInTheDocument();
    expect(screen.getByText('Journal')).toBeInTheDocument();
    expect(screen.getByText('Reminders')).toBeInTheDocument();
  });

  it('highlights active route', () => {
    mockPage.url = new URL('http://localhost/vaults/v1/tasks');
    render(MobileNav);
    const tasksLink = screen.getByText('Tasks').closest('a')!;
    expect(tasksLink.className).toContain('text-brand-400');
    const homeLink = screen.getByText('Home').closest('a')!;
    expect(homeLink.className).not.toContain('text-brand-400');
  });

  it('builds links with vault basePath', () => {
    render(MobileNav);
    const link = screen.getByText('Contacts').closest('a')!;
    expect(link).toHaveAttribute('href', '/vaults/v1/contacts');
  });
});
