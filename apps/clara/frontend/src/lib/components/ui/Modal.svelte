<script lang="ts">
  import { X } from 'lucide-svelte';
  import type { Snippet } from 'svelte';

  interface Props {
    open?: boolean;
    title: string;
    onclose: () => void;
    children: Snippet;
    footer?: Snippet;
  }

  let { open = true, title, onclose, children, footer }: Props = $props();

  let dialogEl: HTMLDivElement;

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      onclose();
      return;
    }
    if (e.key === 'Tab') {
      const focusable = dialogEl?.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
      );
      if (!focusable?.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  }

  $effect(() => {
    if (!open) return;
    document.body.style.overflow = 'hidden';
    // Focus first focusable element
    const el = dialogEl?.querySelector<HTMLElement>(
      'input, textarea, select, button:not([aria-label="Close"])'
    );
    el?.focus();
    return () => {
      document.body.style.overflow = '';
    };
  });
</script>

{#if open}
  <div
    bind:this={dialogEl}
    class="fixed inset-0 z-50 flex items-center justify-center p-4"
    role="dialog"
    aria-modal="true"
    aria-label={title}
    onkeydown={handleKeydown}
  >
    <!-- Backdrop -->
    <button
      class="absolute inset-0 bg-black/60 backdrop-blur-sm"
      onclick={onclose}
      aria-label="Close"
    ></button>

    <!-- Panel -->
    <div class="relative z-10 w-full max-w-lg rounded-xl border border-neutral-700 bg-neutral-900 shadow-2xl">
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-neutral-800 px-5 py-4">
        <h3 class="text-lg font-semibold text-white">{title}</h3>
        <button
          onclick={onclose}
          class="rounded-lg p-1 text-neutral-400 transition hover:bg-neutral-800 hover:text-white"
          aria-label="Close"
        >
          <X size={18} />
        </button>
      </div>

      <!-- Body -->
      <div class="px-5 py-4">
        {@render children()}
      </div>

      <!-- Footer -->
      {#if footer}
        <div class="flex items-center justify-end gap-3 border-t border-neutral-800 px-5 py-4">
          {@render footer()}
        </div>
      {/if}
    </div>
  </div>
{/if}
