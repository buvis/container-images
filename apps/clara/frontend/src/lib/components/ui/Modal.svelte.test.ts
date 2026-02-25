import { render, screen, fireEvent } from '@testing-library/svelte';
import { createRawSnippet } from 'svelte';
import Modal from './Modal.svelte';

const body = createRawSnippet(() => ({
  render: () => `<p>Modal content</p>`
}));

const footer = createRawSnippet(() => ({
  render: () => `<button>Save</button>`
}));

describe('Modal', () => {
  it('renders when open', () => {
    render(Modal, { open: true, title: 'Test', onclose: vi.fn(), children: body });
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Test')).toBeInTheDocument();
    expect(screen.getByText('Modal content')).toBeInTheDocument();
  });

  it('hidden when open=false', () => {
    render(Modal, { open: false, title: 'Test', onclose: vi.fn(), children: body });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('calls onclose when Escape pressed', async () => {
    const onclose = vi.fn();
    render(Modal, { open: true, title: 'Test', onclose, children: body });
    await fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' });
    expect(onclose).toHaveBeenCalled();
  });

  it('calls onclose on backdrop click', async () => {
    const onclose = vi.fn();
    render(Modal, { open: true, title: 'Test', onclose, children: body });
    const backdrop = screen.getAllByRole('button', { name: 'Close' })[0];
    await fireEvent.click(backdrop);
    expect(onclose).toHaveBeenCalled();
  });

  it('renders footer snippet', () => {
    render(Modal, { open: true, title: 'Test', onclose: vi.fn(), children: body, footer });
    expect(screen.getByText('Save')).toBeInTheDocument();
  });

  it('has aria-modal and aria-label', () => {
    render(Modal, { open: true, title: 'My Dialog', onclose: vi.fn(), children: body });
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-label', 'My Dialog');
  });
});
