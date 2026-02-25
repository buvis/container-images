import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import { createRawSnippet } from 'svelte';
import DataList from './DataList.svelte';
import { paginated } from '$tests/helpers';

const row = createRawSnippet((item: () => { name: string }) => ({
  render: () => `<div>${item().name}</div>`
})) as any;

const header = createRawSnippet(() => ({
  render: () => `<button>Add</button>`
}));

function mockLoad(items: { name: string }[] = []) {
  return vi.fn().mockResolvedValue(paginated(items));
}

describe('DataList', () => {
  it('calls load on mount and renders rows', async () => {
    const items = [{ name: 'Alice' }, { name: 'Bob' }];
    const load = mockLoad(items);
    render(DataList, { load, row });
    await waitFor(() => {
      expect(load).toHaveBeenCalledWith({ offset: 0, limit: 20, search: '', filter: null });
    });
    await waitFor(() => {
      expect(screen.getByText('Alice')).toBeInTheDocument();
      expect(screen.getByText('Bob')).toBeInTheDocument();
    });
  });

  it('shows spinner while loading', async () => {
    let resolveLoad!: (v: any) => void;
    const load = vi.fn().mockReturnValue(new Promise((r) => { resolveLoad = r; }));
    render(DataList, { load, row });
    expect(screen.getByLabelText('Loading')).toBeInTheDocument();
    resolveLoad(paginated([]));
    await waitFor(() => {
      expect(screen.queryByLabelText('Loading')).not.toBeInTheDocument();
    });
  });

  it('shows empty state when no items', async () => {
    const load = mockLoad([]);
    render(DataList, { load, row, emptyTitle: 'No data' });
    await waitFor(() => {
      expect(screen.getByText('No data')).toBeInTheDocument();
    });
  });

  it('renders header snippet', async () => {
    const load = mockLoad([]);
    render(DataList, { load, row, header });
    expect(screen.getByText('Add')).toBeInTheDocument();
  });

  it('search triggers load with search param', async () => {
    const load = mockLoad([]);
    render(DataList, { load, row });
    await waitFor(() => expect(load).toHaveBeenCalled());
    const searchInput = screen.getByPlaceholderText('Search...');
    await fireEvent.input(searchInput, { target: { value: 'test' } });
    await waitFor(() => {
      expect(load).toHaveBeenCalledWith(expect.objectContaining({ search: 'test', offset: 0 }));
    });
  });
});
