<script lang="ts">
  import Spinner from '$components/ui/Spinner.svelte';
  import type { Snippet } from 'svelte';
  import type { HTMLButtonAttributes } from 'svelte/elements';

  interface Props extends HTMLButtonAttributes {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    loading?: boolean;
    children: Snippet;
  }

  let {
    variant = 'primary',
    size = 'md',
    loading = false,
    children,
    disabled,
    class: className = '',
    ...rest
  }: Props = $props();

  const base = 'inline-flex items-center justify-center rounded-lg font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 focus-visible:ring-offset-neutral-900 disabled:opacity-50 disabled:pointer-events-none';

  const variants: Record<string, string> = {
    primary: 'bg-brand-500 text-white hover:bg-brand-400',
    secondary: 'border border-neutral-700 bg-neutral-800 text-neutral-200 hover:bg-neutral-700 hover:text-white',
    ghost: 'text-neutral-400 hover:bg-neutral-800 hover:text-white',
    danger: 'bg-red-600 text-white hover:bg-red-500'
  };

  const sizes: Record<string, string> = {
    sm: 'h-8 px-3 text-xs gap-1.5',
    md: 'h-9 px-4 text-sm gap-2',
    lg: 'h-11 px-6 text-sm gap-2'
  };
</script>

<button
  class="{base} {variants[variant]} {sizes[size]} {className}"
  disabled={disabled || loading}
  {...rest}
>
  {#if loading}
    <Spinner size="sm" />
  {/if}
  {@render children()}
</button>
