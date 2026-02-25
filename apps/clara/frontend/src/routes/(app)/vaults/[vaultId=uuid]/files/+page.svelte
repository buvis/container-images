<script lang="ts">
  import { page } from '$app/state';
  import { filesApi } from '$api/files';
  import DataList from '$components/data/DataList.svelte';
  import Button from '$components/ui/Button.svelte';
  import { Upload, Download, Trash2, FolderOpen } from 'lucide-svelte';
  import type { FileRecord } from '$lib/types/models';

  const vaultId = $derived(page.params.vaultId!);

  let dataList: DataList<FileRecord>;
  let uploading = $state(false);
  let editingId = $state<string | null>(null);
  let editFilename = $state('');

  async function loadFiles(params: { offset: number; limit: number; search: string; filter: string | null }) {
    return filesApi.list(vaultId, {
      offset: params.offset,
      limit: params.limit,
      q: params.search || undefined
    });
  }

  async function handleUpload(e: Event) {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    uploading = true;
    try {
      await filesApi.upload(vaultId, file);
      dataList.refresh();
    } finally {
      uploading = false;
      input.value = '';
    }
  }

  function startRename(file: FileRecord) {
    editingId = file.id;
    editFilename = file.filename;
  }

  async function handleRename(fileId: string) {
    if (!editFilename.trim()) return;
    await filesApi.rename(vaultId, fileId, editFilename.trim());
    editingId = null;
    dataList.refresh();
  }

  function cancelRename() {
    editingId = null;
  }

  async function handleDelete(file: FileRecord) {
    await filesApi.del(vaultId, file.id);
    dataList.refresh();
  }

  function formatSize(size: number): string {
    if (size < 1024) return `${size} B`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
    if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(1)} MB`;
    return `${(size / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  }

  function formatDate(value: string): string {
    return new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  }
</script>

<svelte:head><title>Files</title></svelte:head>

<div class="space-y-4">
  <input id="file-upload" type="file" class="hidden" onchange={handleUpload} />

    <DataList
      bind:this={dataList}
      load={loadFiles}
      searchPlaceholder="Search files..."
      emptyIcon={FolderOpen}
      emptyTitle="No files uploaded"
      emptyDescription="Upload files to store documents and attachments"
    >
      {#snippet header()}
        <Button onclick={() => document.getElementById('file-upload')?.click()} loading={uploading}>
          <Upload size={16} />
          Upload File
        </Button>
      {/snippet}
      {#snippet row(item: FileRecord)}
        <div class="flex items-center gap-3 px-4 py-3">
          <div class="min-w-0 flex-1">
            {#if editingId === item.id}
              <input
                type="text"
                bind:value={editFilename}
                onkeydown={(e) => {
                  if (e.key === 'Enter') handleRename(item.id);
                  if (e.key === 'Escape') cancelRename();
                }}
                onblur={() => cancelRename()}
                class="w-full rounded border border-brand-500 bg-neutral-800 px-2 py-0.5 text-sm text-white outline-none"
                autofocus
              />
            {:else}
              <button onclick={() => startRename(item)} class="truncate text-sm font-medium text-white hover:text-brand-400 text-left">
                {item.filename}
              </button>
            {/if}
            <p class="truncate text-xs text-neutral-500">{item.mime_type}</p>
          </div>
          <div class="hidden text-xs text-neutral-500 sm:block">{formatSize(item.size_bytes)}</div>
          <div class="hidden text-xs text-neutral-500 md:block">{formatDate(item.created_at)}</div>
          <div class="flex items-center gap-1">
            <Button size="sm" variant="ghost" onclick={() => filesApi.download(vaultId, item.id)}>
              <Download size={14} />
            </Button>
            <Button size="sm" variant="ghost" onclick={() => handleDelete(item)}>
              <Trash2 size={14} />
            </Button>
          </div>
        </div>
      {/snippet}
    </DataList>
</div>
