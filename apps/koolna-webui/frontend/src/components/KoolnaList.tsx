import { useCallback, useEffect, useState } from 'react'
import {
  listKoolnas,
  pauseKoolna,
  resumeKoolna,
  deleteKoolna,
  Koolna,
} from '../api/koolna'

type KoolnaListProps = {
  onTerminal: (name: string, session: string) => void
}

const phaseBadgeStyles: Record<Koolna['phase'], string> = {
  Running: 'border border-emerald-400/40 bg-emerald-500/10 text-emerald-300',
  Pending: 'border border-amber-400/40 bg-amber-500/10 text-amber-300',
  Suspended: 'border border-slate-400/40 bg-slate-500/10 text-slate-300',
  Failed: 'border border-rose-400/40 bg-rose-500/10 text-rose-300',
}

const KoolnaList = ({ onTerminal }: KoolnaListProps) => {
  const [koolnas, setKoolnas] = useState<Koolna[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

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

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-slate-950/60 px-5 py-4 shadow-sm shadow-black/40">
        <div>
          <h2 className="text-lg font-semibold text-white">Koolnas</h2>
          <p className="text-sm text-white/60">Manage active environments.</p>
        </div>
        {loading && (
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-white/70">
            <span className="h-3 w-3 animate-spin rounded-full border border-t-white border-white/20" />
            Refreshing
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/60 bg-rose-500/10 px-4 py-2 text-sm text-rose-200">
          {error}
        </div>
      )}

      <div className="overflow-x-auto rounded-2xl border border-white/10 bg-slate-950/50 shadow-lg shadow-black/40">
        <table className="w-full min-w-[620px] table-auto text-sm text-white">
          <thead className="border-b border-white/10 text-xs uppercase tracking-wider text-white/60">
            <tr>
              <th className="px-4 py-3 text-left">Name</th>
              <th className="px-4 py-3 text-left">Repo</th>
              <th className="px-4 py-3 text-left">Branch</th>
              <th className="px-4 py-3 text-left">Phase</th>
              <th className="px-4 py-3 text-left">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {koolnas.map((koolna) => (
              <tr key={koolna.name} className="hover:bg-white/5">
                <td className="px-4 py-3 font-medium text-white">{koolna.name}</td>
                <td className="px-4 py-3 text-white/70">{koolna.repo}</td>
                <td className="px-4 py-3 text-white/70">{koolna.branch}</td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex items-center justify-center rounded-full px-3 py-1 text-xs font-semibold ${phaseBadgeStyles[koolna.phase]}`}
                  >
                    {koolna.phase}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="rounded-lg border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold text-white transition hover:border-white/20"
                      onClick={() => onTerminal(koolna.name, 'manager')}
                    >
                      Manager
                    </button>
                    <button
                      type="button"
                      className="rounded-lg border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold text-white transition hover:border-white/20"
                      onClick={() => onTerminal(koolna.name, 'worker')}
                    >
                      Worker
                    </button>
                    {koolna.suspended ? (
                      <button
                        type="button"
                        className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-200 transition hover:border-emerald-400/50"
                        onClick={() =>
                          performAction(() => resumeKoolna(koolna.name))
                        }
                      >
                        Resume
                      </button>
                    ) : (
                      <button
                        type="button"
                        className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-200 transition hover:border-amber-400/50"
                        onClick={() =>
                          performAction(() => pauseKoolna(koolna.name))
                        }
                      >
                        Pause
                      </button>
                    )}
                    <button
                      type="button"
                      className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-1 text-xs font-semibold text-rose-200 transition hover:border-rose-400/50"
                      onClick={() => performAction(() => deleteKoolna(koolna.name))}
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {!loading && koolnas.length === 0 && (
              <tr>
                <td className="px-4 py-6 text-center text-sm text-white/60" colSpan={5}>
                  No Koolnas available.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default KoolnaList
