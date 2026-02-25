<script lang="ts">
  import Shell from '$components/layout/Shell.svelte';

  let { children } = $props();
</script>

<Shell>
  {@render children()}
</Shell>
