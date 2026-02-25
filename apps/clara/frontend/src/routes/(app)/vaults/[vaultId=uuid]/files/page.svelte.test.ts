import { render, screen, waitFor } from '@testing-library/svelte';
import { paginated, setVaultParams } from '$tests/helpers';
import { makeFileRecord } from '$tests/fixtures';
import FilesPage from './+page.svelte';

const mockList = vi.fn();

vi.mock('$api/files', () => ({
  filesApi: {
    list: (...args: unknown[]) => mockList(...args),
    upload: vi.fn(),
    download: vi.fn(),
    rename: vi.fn(),
    del: vi.fn()
  }
}));

beforeEach(() => {
  mockList.mockReset().mockResolvedValue(paginated([]));
  setVaultParams('v1');
});

describe('Files list page', () => {
  it('renders files from API', async () => {
    mockList.mockResolvedValue(paginated([makeFileRecord({ filename: 'report.pdf', mime_type: 'application/pdf', size_bytes: 2048 })]));
    render(FilesPage);
    await waitFor(() => {
      expect(screen.getByText('report.pdf')).toBeInTheDocument();
      expect(screen.getByText('application/pdf')).toBeInTheDocument();
    });
  });

  it('shows empty state', async () => {
    render(FilesPage);
    await waitFor(() => expect(screen.getByText('No files uploaded')).toBeInTheDocument());
  });

  it('has upload button', () => {
    render(FilesPage);
    expect(screen.getByText('Upload File')).toBeInTheDocument();
  });

  it('displays file size', async () => {
    mockList.mockResolvedValue(paginated([makeFileRecord({ filename: 'big.zip', size_bytes: 1048576 })]));
    render(FilesPage);
    await waitFor(() => expect(screen.getByText('1.0 MB')).toBeInTheDocument());
  });
});
