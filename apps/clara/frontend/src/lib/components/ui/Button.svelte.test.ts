import { render, screen } from '@testing-library/svelte';
import { createRawSnippet } from 'svelte';
import Button from './Button.svelte';

function textSnippet(text: string) {
  return createRawSnippet(() => ({
    render: () => `<span>${text}</span>`
  }));
}

describe('Button', () => {
  it('renders children text', () => {
    render(Button, { children: textSnippet('Click me') });
    expect(screen.getByRole('button')).toHaveTextContent('Click me');
  });

  it('applies primary variant classes by default', () => {
    render(Button, { children: textSnippet('Go') });
    expect(screen.getByRole('button').className).toContain('bg-brand-500');
  });

  it('applies danger variant classes', () => {
    render(Button, { children: textSnippet('Delete'), variant: 'danger' });
    expect(screen.getByRole('button').className).toContain('bg-red-600');
  });

  it('applies secondary variant classes', () => {
    render(Button, { children: textSnippet('Cancel'), variant: 'secondary' });
    expect(screen.getByRole('button').className).toContain('bg-neutral-800');
  });

  it('applies ghost variant classes', () => {
    render(Button, { children: textSnippet('More'), variant: 'ghost' });
    expect(screen.getByRole('button').className).toContain('text-neutral-400');
  });

  it('applies sm size classes', () => {
    render(Button, { children: textSnippet('S'), size: 'sm' });
    expect(screen.getByRole('button').className).toContain('h-8');
  });

  it('applies lg size classes', () => {
    render(Button, { children: textSnippet('L'), size: 'lg' });
    expect(screen.getByRole('button').className).toContain('h-11');
  });

  it('shows spinner and disables when loading', () => {
    render(Button, { children: textSnippet('Save'), loading: true });
    const btn = screen.getByRole('button');
    expect(btn).toBeDisabled();
    expect(btn.querySelector('[aria-label="Loading"]')).toBeTruthy();
  });

  it('disables when disabled prop set', () => {
    render(Button, { children: textSnippet('No'), disabled: true });
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('passes through extra attributes', () => {
    render(Button, { children: textSnippet('T'), type: 'submit' });
    expect(screen.getByRole('button')).toHaveAttribute('type', 'submit');
  });
});
