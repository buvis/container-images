<script lang="ts" generics="T">
  import SearchBar from '$components/data/SearchBar.svelte';
  import Pagination from '$components/data/Pagination.svelte';
  import FilterChips from '$components/data/FilterChips.svelte';
  import Spinner from '$components/ui/Spinner.svelte';
  import EmptyState from '$components/ui/EmptyState.svelte';
  import type { PaginatedResponse } from '$lib/types/common';
  import type { Component, Snippet } from 'svelte';

  interface FilterChip {
    label: string;
    value: string;
  }

  interface Props {
    load: (params: { offset: number; limit: number; search: string; filter: string | null }) => Promise<PaginatedResponse<T>>;
    row: Snippet<[T]>;
    header?: Snippet;
    emptyIcon?: Component<{ size?: number }>;
    emptyTitle?: string;
    emptyDescription?: string;
    searchPlaceholder?: string;
    filters?: FilterChip[];
    limit?: number;
  }

  let {
    load,
    row,
    header,
    emptyIcon,
    emptyTitle = 'Nothing here yet',
    emptyDescription,
    searchPlaceholder = 'Search...',
    filters,
    limit = 20
  }: Props = $props();

  let items = $state<T[]>([]);
  let total = $state(0);
  let offset = $state(0);
  let search = $state('');
  let filter = $state<string | null>(null);
  let loading = $state(false);

  async function fetchData() {
    loading = true;
    try {
      const res = await load({ offset, limit, search, filter });
      items = res.items;
      total = res.meta.total;
    } catch {
      items = [];
      total = 0;
    } finally {
      loading = false;
    }
  }

  function handleSearch(value: string) {
    search = value;
    offset = 0;
    fetchData();
  }

  function handleFilter(value: string | null) {
    filter = value;
    offset = 0;
    fetchData();
  }

  function handlePage(newOffset: number) {
    offset = newOffset;
    fetchData();
  }

  // Expose a refresh function via binding
  export function refresh() {
    fetchData();
  }

  // Initial load
  $effect(() => {
    fetchData();
  });
</script>

<div class="space-y-4">
  <!-- Controls row -->
  <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
    <div class="w-full sm:max-w-xs">
      <SearchBar value={search} placeholder={searchPlaceholder} onchange={handleSearch} />
    </div>
    {#if header}
      <div class="flex items-center gap-2">
        {@render header()}
      </div>
    {/if}
  </div>

  <!-- Filters -->
  {#if filters && filters.length > 0}
    <FilterChips chips={filters} selected={filter} onselect={handleFilter} />
  {/if}

  <!-- Content -->
  {#if loading}
    <div class="flex justify-center py-12">
      <Spinner size="lg" />
    </div>
  {:else if items.length === 0}
    <EmptyState
      icon={emptyIcon}
      title={emptyTitle}
      description={search ? `No results for "${search}"` : emptyDescription}
    />
  {:else}
    <div class="divide-y divide-neutral-800 rounded-xl border border-neutral-800">
      {#each items as item}
        {@render row(item)}
      {/each}
    </div>

    <Pagination {total} {offset} {limit} onchange={handlePage} />
  {/if}
</div>
