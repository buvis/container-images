import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { goto } from '$app/navigation';
import RegisterPage from './+page.svelte';

const mockRegister = vi.fn();

vi.mock('$state/auth.svelte', () => ({
  auth: {
    register: (...args: unknown[]) => mockRegister(...args)
  }
}));

beforeEach(() => {
  mockRegister.mockReset();
  vi.mocked(goto).mockReset();
});

describe('Register page', () => {
  it('renders create account form', () => {
    render(RegisterPage);
    expect(screen.getByRole('heading', { name: 'Create account' })).toBeInTheDocument();
    expect(screen.getByLabelText('Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
  });

  it('submits and redirects to login on success', async () => {
    mockRegister.mockResolvedValue({ user: {}, access_token: 't', vault_id: null });
    render(RegisterPage);
    await fireEvent.input(screen.getByLabelText('Name'), { target: { value: 'Jane' } });
    await fireEvent.input(screen.getByLabelText('Email'), { target: { value: 'j@b.com' } });
    await fireEvent.input(screen.getByLabelText('Password'), { target: { value: 'pass1234' } });
    await fireEvent.submit(screen.getByRole('button', { name: 'Create account' }).closest('form')!);
    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith('j@b.com', 'pass1234', 'Jane');
      expect(goto).toHaveBeenCalledWith('/auth/login');
    });
  });

  it('displays error on failure', async () => {
    mockRegister.mockRejectedValue({ detail: 'Email already exists' });
    render(RegisterPage);
    await fireEvent.input(screen.getByLabelText('Name'), { target: { value: 'Jane' } });
    await fireEvent.input(screen.getByLabelText('Email'), { target: { value: 'j@b.com' } });
    await fireEvent.input(screen.getByLabelText('Password'), { target: { value: 'pass1234' } });
    await fireEvent.submit(screen.getByRole('button', { name: 'Create account' }).closest('form')!);
    await waitFor(() => {
      expect(screen.getByText('Email already exists')).toBeInTheDocument();
    });
  });

  it('has link to sign in page', () => {
    render(RegisterPage);
    const link = screen.getByText('Sign in');
    expect(link).toHaveAttribute('href', '/auth/login');
  });
});
