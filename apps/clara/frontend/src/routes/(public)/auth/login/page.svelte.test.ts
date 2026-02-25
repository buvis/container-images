import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { goto } from '$app/navigation';
import LoginPage from './+page.svelte';

const mockLogin = vi.fn();
const mockVerifyTwoFactor = vi.fn();

vi.mock('$state/auth.svelte', () => ({
  auth: {
    login: (...args: unknown[]) => mockLogin(...args),
    verifyTwoFactor: (...args: unknown[]) => mockVerifyTwoFactor(...args)
  }
}));

beforeEach(() => {
  mockLogin.mockReset();
  mockVerifyTwoFactor.mockReset();
  vi.mocked(goto).mockReset();
});

describe('Login page', () => {
  function getLoginForm() {
    return screen.getByRole('button', { name: 'Sign in' }).closest('form')!;
  }

  it('renders sign in form', () => {
    render(LoginPage);
    expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
  });

  it('submits credentials and redirects on success', async () => {
    mockLogin.mockResolvedValue({ user: {}, vault_id: 'v1', access_token: 't' });
    render(LoginPage);
    await fireEvent.input(screen.getByLabelText('Email'), { target: { value: 'a@b.com' } });
    await fireEvent.input(screen.getByLabelText('Password'), { target: { value: 'pass1234' } });
    await fireEvent.submit(getLoginForm());
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('a@b.com', 'pass1234');
      expect(goto).toHaveBeenCalledWith('/vaults/v1/dashboard');
    });
  });

  it('redirects to / when no vault_id', async () => {
    mockLogin.mockResolvedValue({ user: {}, vault_id: null, access_token: 't' });
    render(LoginPage);
    await fireEvent.input(screen.getByLabelText('Email'), { target: { value: 'a@b.com' } });
    await fireEvent.input(screen.getByLabelText('Password'), { target: { value: 'pass1234' } });
    await fireEvent.submit(getLoginForm());
    await waitFor(() => expect(goto).toHaveBeenCalledWith('/'));
  });

  it('displays error on login failure', async () => {
    mockLogin.mockRejectedValue({ detail: 'Invalid credentials' });
    render(LoginPage);
    await fireEvent.input(screen.getByLabelText('Email'), { target: { value: 'a@b.com' } });
    await fireEvent.input(screen.getByLabelText('Password'), { target: { value: 'wrong' } });
    await fireEvent.submit(getLoginForm());
    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
    });
  });

  it('shows 2FA form when requires_2fa', async () => {
    mockLogin.mockResolvedValue({ requires_2fa: true, temp_token: 'tok123' });
    render(LoginPage);
    await fireEvent.input(screen.getByLabelText('Email'), { target: { value: 'a@b.com' } });
    await fireEvent.input(screen.getByLabelText('Password'), { target: { value: 'pass1234' } });
    await fireEvent.submit(getLoginForm());
    await waitFor(() => {
      expect(screen.getByText('Two-factor verification')).toBeInTheDocument();
      expect(screen.getByLabelText('Authenticator code')).toBeInTheDocument();
    });
  });

  it('submits 2FA code and redirects', async () => {
    mockLogin.mockResolvedValue({ requires_2fa: true, temp_token: 'tok123' });
    mockVerifyTwoFactor.mockResolvedValue({ user: {}, vault_id: 'v1', access_token: 't' });
    render(LoginPage);
    // Login first
    await fireEvent.input(screen.getByLabelText('Email'), { target: { value: 'a@b.com' } });
    await fireEvent.input(screen.getByLabelText('Password'), { target: { value: 'pass1234' } });
    await fireEvent.submit(getLoginForm());
    await waitFor(() => expect(screen.getByText('Two-factor verification')).toBeInTheDocument());
    // Enter 2FA code
    await fireEvent.input(screen.getByLabelText('Authenticator code'), { target: { value: '123456' } });
    await fireEvent.submit(screen.getByText('Verify').closest('form')!);
    await waitFor(() => {
      expect(mockVerifyTwoFactor).toHaveBeenCalledWith('tok123', '123456', false);
      expect(goto).toHaveBeenCalledWith('/vaults/v1/dashboard');
    });
  });

  it('toggles recovery code mode', async () => {
    mockLogin.mockResolvedValue({ requires_2fa: true, temp_token: 'tok123' });
    render(LoginPage);
    await fireEvent.input(screen.getByLabelText('Email'), { target: { value: 'a@b.com' } });
    await fireEvent.input(screen.getByLabelText('Password'), { target: { value: 'pass1234' } });
    await fireEvent.submit(getLoginForm());
    await waitFor(() => expect(screen.getByText('Two-factor verification')).toBeInTheDocument());
    await fireEvent.click(screen.getByText('Use recovery code'));
    expect(screen.getByLabelText('Recovery code')).toBeInTheDocument();
  });
});
