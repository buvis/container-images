<script lang="ts">
  interface Props {
    variant?: 'default' | 'success' | 'warning' | 'danger';
    text: string;
  }

  let { variant = 'default', text }: Props = $props();

  const variants: Record<string, string> = {
    default: 'bg-neutral-800 text-neutral-300',
    success: 'bg-emerald-950/50 text-emerald-400',
    warning: 'bg-amber-950/50 text-amber-400',
    danger: 'bg-red-950/50 text-red-400'
  };
</script>

<span
  class="inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium {variants[variant]}"
>
  {text}
</span>
