import { useCallback, useEffect, useState } from 'react'
import {
  listKoolnas,
  pauseKoolna,
  resumeKoolna,
  deleteKoolna,
  mountScriptUrl,
  type Koolna,
} from '../api/koolna'

type KoolnaListProps = {
  onCreate: () => void
  onTerminal: (name: string, session: string) => void
}

const phaseBadgeStyles: Record<Koolna['phase'], string> = {
  Running: 'border border-phase-running/40 bg-phase-running/10 text-phase-running',
  Pending: 'border border-phase-pending/40 bg-phase-pending/10 text-phase-pending',
  Suspended: 'border border-phase-suspended/40 bg-phase-suspended/10 text-phase-suspended',
  Failed: 'border border-phase-failed/40 bg-phase-failed/10 text-phase-failed',
}

const PauseIcon = () => (
  <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
    <path d="M5.75 3a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-1.5 0V3.75A.75.75 0 0 1 5.75 3Zm8.5 0a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-1.5 0V3.75a.75.75 0 0 1 .75-.75Z" />
  </svg>
)

const PlayIcon = () => (
  <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
    <path d="M6.3 2.84A1.5 1.5 0 0 0 4 4.11v11.78a1.5 1.5 0 0 0 2.3 1.27l9.344-5.891a1.5 1.5 0 0 0 0-2.538L6.3 2.841Z" />
  </svg>
)

const MountIcon = () => (
  <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
    <path d="M3.75 3A1.75 1.75 0 0 0 2 4.75v3.26a3.235 3.235 0 0 1 1.75-.51h12.5c.644 0 1.245.188 1.75.51V6.75A1.75 1.75 0 0 0 16.25 5h-4.836a.25.25 0 0 1-.177-.073L9.823 3.513A1.75 1.75 0 0 0 8.586 3H3.75ZM3.75 9A1.75 1.75 0 0 0 2 10.75v4.5c0 .966.784 1.75 1.75 1.75h12.5A1.75 1.75 0 0 0 18 15.25v-4.5A1.75 1.75 0 0 0 16.25 9H3.75Zm7.28 2.47a.75.75 0 0 0-1.06 0l-2 2a.75.75 0 1 0 1.06 1.06l.72-.72V16a.75.75 0 0 0 1.5 0v-2.19l.72.72a.75.75 0 1 0 1.06-1.06l-2-2Z" />
  </svg>
)

const TrashIcon = () => (
  <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
    <path fillRule="evenodd" d="M8.75 1A2.75 2.75 0 0 0 6 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 1 0 .23 1.482l.149-.022.841 10.518A2.75 2.75 0 0 0 7.596 19h4.807a2.75 2.75 0 0 0 2.742-2.53l.841-10.519.149.023a.75.75 0 0 0 .23-1.482A41.03 41.03 0 0 0 14 4.193V3.75A2.75 2.75 0 0 0 11.25 1h-2.5ZM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4ZM8.58 7.72a.75.75 0 0 0-1.5.06l.3 7.5a.75.75 0 1 0 1.5-.06l-.3-7.5Zm4.34.06a.75.75 0 1 0-1.5-.06l-.3 7.5a.75.75 0 1 0 1.5.06l.3-7.5Z" clipRule="evenodd" />
  </svg>
)

type KoolnaActionsProps = {
  koolna: Koolna
  onTerminal: (name: string, session: string) => void
  onPause: () => void
  onResume: () => void
  onMount: () => void
  onDelete: () => void
}

const KoolnaActions = ({ koolna, onTerminal, onPause, onResume, onMount, onDelete }: KoolnaActionsProps) => (
  <div className="flex flex-wrap items-center gap-2">
    <button
      type="button"
      className="rounded-lg border border-border bg-surface-raised px-3 py-1 text-xs font-semibold text-text transition hover:border-text-muted disabled:opacity-40 disabled:pointer-events-none"
      onClick={() => onTerminal(koolna.name, 'manager')}
      disabled={koolna.phase !== 'Running'}
    >
      Manager
    </button>
    <button
      type="button"
      className="rounded-lg border border-border bg-surface-raised px-3 py-1 text-xs font-semibold text-text transition hover:border-text-muted disabled:opacity-40 disabled:pointer-events-none"
      onClick={() => onTerminal(koolna.name, 'worker')}
      disabled={koolna.phase !== 'Running'}
    >
      Worker
    </button>
    {koolna.suspended ? (
      <button
        type="button"
        className="flex h-11 w-11 items-center justify-center rounded-lg border border-phase-running/30 bg-phase-running/10 text-phase-running transition hover:border-phase-running/50 sm:h-8 sm:w-8"
        onClick={onResume}
        title="Resume"
        aria-label="Resume"
      >
        <PlayIcon />
      </button>
    ) : (
      <button
        type="button"
        className="flex h-11 w-11 items-center justify-center rounded-lg border border-warning/30 bg-warning/10 text-warning transition hover:border-warning/50 sm:h-8 sm:w-8"
        onClick={onPause}
        title="Pause"
        aria-label="Pause"
      >
        <PauseIcon />
      </button>
    )}
    <button
      type="button"
      className="flex h-11 w-11 items-center justify-center rounded-lg border border-accent/30 bg-accent/10 text-accent transition hover:border-accent/50 disabled:opacity-40 disabled:pointer-events-none sm:h-8 sm:w-8"
      onClick={onMount}
      disabled={koolna.phase !== 'Running' || !koolna.sshPublicKey}
      title={koolna.phase !== 'Running' ? 'Pod not running' : !koolna.sshPublicKey ? 'Set SSH public key in Settings to enable mounting' : 'Mount'}
      aria-label="Mount"
    >
      <MountIcon />
    </button>
    <button
      type="button"
      className="flex h-11 w-11 items-center justify-center rounded-lg border border-danger/30 bg-danger/10 text-danger transition hover:border-danger/50 sm:h-8 sm:w-8"
      onClick={onDelete}
      title="Delete"
      aria-label="Delete"
    >
      <TrashIcon />
    </button>
  </div>
)

const KoolnaList = ({ onCreate, onTerminal }: KoolnaListProps) => {
  const [koolnas, setKoolnas] = useState<Koolna[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [mountTarget, setMountTarget] = useState<string | null>(null)

  const loadKoolnas = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const fetched = await listKoolnas()
      setKoolnas(fetched)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to load Koolnas at this time.',
      )
    } finally {
      setLoading(false)
    }
  }, [])

  const performAction = useCallback(
    async (action: () => Promise<void>) => {
      setError(null)
      try {
        await action()
        await loadKoolnas()
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Something went wrong handling that action.',
        )
      }
    },
    [loadKoolnas],
  )

  useEffect(() => {
    loadKoolnas()
    const interval = setInterval(() => {
      loadKoolnas()
    }, 10000)
    return () => clearInterval(interval)
  }, [loadKoolnas])

  const actionProps = (koolna: Koolna) => ({
    koolna,
    onTerminal,
    onPause: () => performAction(() => pauseKoolna(koolna.name)),
    onResume: () => performAction(() => resumeKoolna(koolna.name)),
    onMount: () => setMountTarget(koolna.name),
    onDelete: () => performAction(() => deleteKoolna(koolna.name)),
  })

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between rounded-2xl border border-border bg-surface px-5 py-4 shadow-sm shadow-black/40">
        <div>
          <h2 className="text-lg font-semibold text-text">Koolnas</h2>
          <p className="text-sm text-text-muted">Manage active environments.</p>
        </div>
        <div className="flex items-center gap-3">
          {loading && (
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
              <span className="h-3 w-3 animate-spin rounded-full border border-t-text border-border" />
              Refreshing
            </div>
          )}
          <button
            type="button"
            className="hidden rounded-2xl border border-transparent bg-create px-4 py-2 text-sm font-semibold text-white transition hover:bg-create-hover sm:inline-flex"
            onClick={onCreate}
          >
            New Koolna
          </button>
        </div>
      </div>

      <button
        type="button"
        className="w-full rounded-2xl border border-transparent bg-create px-4 py-2 text-sm font-semibold text-white transition hover:bg-create-hover sm:hidden"
        onClick={onCreate}
      >
        New Koolna
      </button>

      {error && (
        <div className="rounded-xl border border-danger/60 bg-danger/10 px-4 py-2 text-sm text-danger">
          {error}
        </div>
      )}

      {/* Desktop table */}
      <div className="hidden overflow-x-auto rounded-2xl border border-border bg-surface shadow-lg shadow-black/40 sm:block">
        <table className="w-full min-w-[620px] table-auto text-sm text-text">
          <thead className="border-b border-border text-xs uppercase tracking-wider text-text-muted">
            <tr>
              <th className="px-4 py-3 text-left">Name</th>
              <th className="px-4 py-3 text-left">Repo</th>
              <th className="px-4 py-3 text-left">Branch</th>
              <th className="px-4 py-3 text-left">Phase</th>
              <th className="px-4 py-3 text-left">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/30">
            {koolnas.map((koolna) => (
              <tr key={koolna.name} className="hover:bg-surface-raised/50">
                <td className="px-4 py-3 font-medium text-text">{koolna.name}</td>
                <td className="px-4 py-3 text-text-muted">
                  <button
                    type="button"
                    onClick={() => window.open(koolna.repo, '_blank', 'noopener,noreferrer')}
                    className="cursor-pointer text-left underline decoration-text-muted/30 underline-offset-2 transition hover:text-text hover:decoration-text-muted/60"
                  >
                    {koolna.repo}
                  </button>
                </td>
                <td className="px-4 py-3 text-text-muted">{koolna.branch}</td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex items-center justify-center rounded-full px-3 py-1 text-xs font-semibold ${phaseBadgeStyles[koolna.phase]}`}
                  >
                    {koolna.phase}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <KoolnaActions {...actionProps(koolna)} />
                </td>
              </tr>
            ))}
            {!loading && koolnas.length === 0 && (
              <tr>
                <td className="px-4 py-6 text-center text-sm text-text-muted" colSpan={5}>
                  No Koolnas available.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="space-y-3 sm:hidden">
        {koolnas.map((koolna) => (
          <div key={koolna.name} className="rounded-2xl border border-border bg-surface p-4 shadow-lg shadow-black/40">
            <div className="mb-3 flex items-start justify-between gap-2">
              <div className="min-w-0">
                <h3 className="font-medium text-text">{koolna.name}</h3>
                <p className="truncate text-xs text-text-muted">{koolna.repo}</p>
                <p className="text-xs text-text-muted">{koolna.branch}</p>
              </div>
              <span
                className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${phaseBadgeStyles[koolna.phase]}`}
              >
                {koolna.phase}
              </span>
            </div>
            <KoolnaActions {...actionProps(koolna)} />
          </div>
        ))}
        {!loading && koolnas.length === 0 && (
          <div className="rounded-2xl border border-border bg-surface px-4 py-6 text-center text-sm text-text-muted">
            No Koolnas available.
          </div>
        )}
      </div>

      {/* Mount modal */}
      {mountTarget && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm sm:items-center"
          onClick={() => setMountTarget(null)}
        >
          <div
            className="flex h-full w-full flex-col bg-bg p-6 sm:h-auto sm:max-w-lg sm:rounded-2xl sm:border sm:border-border sm:bg-surface sm:shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between sm:block">
              <h3 className="text-lg font-semibold text-text">
                Mount {mountTarget}
              </h3>
              <button
                type="button"
                onClick={() => setMountTarget(null)}
                className="flex h-11 w-11 items-center justify-center rounded-lg text-text-muted transition hover:text-text sm:hidden"
                title="Close"
                aria-label="Close"
              >
                <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
                  <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
                </svg>
              </button>
            </div>
            <div className="mt-4 flex-1">
              <p className="mb-3 text-sm text-text-muted">
                Download the mount script, make it executable, and run it.
              </p>
              <div className="mb-4 rounded-xl border border-border bg-surface-raised p-4 font-mono text-xs text-text-muted">
                <p>chmod +x mount-{mountTarget}.sh</p>
                <p>./mount-{mountTarget}.sh</p>
              </div>
              <p className="mb-4 text-sm text-text-muted">
                To unmount, press Ctrl+C in the script terminal or run:
              </p>
              <div className="mb-6 rounded-xl border border-border bg-surface-raised p-4 font-mono text-xs text-text-muted">
                <p># macOS</p>
                <p>umount ~/mnt/koolna/{mountTarget}</p>
                <p># Linux</p>
                <p>fusermount -u ~/mnt/koolna/{mountTarget}</p>
              </div>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <a
                href={mountScriptUrl(mountTarget)}
                download
                className="inline-flex w-full items-center justify-center rounded-2xl border border-transparent bg-accent px-5 py-2 text-sm font-semibold text-white transition hover:bg-accent-hover sm:w-auto"
              >
                Download script
              </a>
              <button
                type="button"
                onClick={() => setMountTarget(null)}
                className="hidden rounded-2xl border border-border bg-surface-raised px-5 py-2 text-sm font-semibold text-text transition hover:border-text-muted sm:inline-flex"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default KoolnaList
