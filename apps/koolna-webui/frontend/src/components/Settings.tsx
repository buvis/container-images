import { useEffect, useState } from 'react'
import {
  bootstrapClaudeAuth,
  type ClaudeAuthStatus,
  type DotfilesDefaults,
  type EnvVar,
  getClaudeAuthStatus,
  getDefaults,
  getEnvDefaults,
  updateDefaults,
  updateEnvDefaults,
} from '../api/koolna'
import { EnvVarEditor } from './EnvVarEditor'

const INPUT_BASE = 'mt-2 w-full rounded-xl border px-4 py-2 text-sm text-white transition focus:outline-none focus:ring-1'
const INPUT_OK = 'border-white/10 bg-slate-900/60 focus:border-sky-400 focus:ring-sky-400'

export function Settings() {
  const [defaults, setDefaults] = useState<DotfilesDefaults>({})
  const [envVars, setEnvVars] = useState<EnvVar[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  const [claudeAuthStatus, setClaudeAuthStatus] = useState<ClaudeAuthStatus | null>(null)
  const [claudeAuthInput, setClaudeAuthInput] = useState('')
  const [claudeAuthEditing, setClaudeAuthEditing] = useState(false)
  const [claudeAuthSubmitting, setClaudeAuthSubmitting] = useState(false)
  const [claudeAuthError, setClaudeAuthError] = useState<string | null>(null)

  const reloadClaudeAuthStatus = () => {
    getClaudeAuthStatus()
      .then((status) => setClaudeAuthStatus(status))
      .catch(() => setClaudeAuthStatus(null))
  }

  useEffect(() => {
    Promise.all([getDefaults(), getEnvDefaults()])
      .then(([d, env]) => {
        setDefaults(d)
        setEnvVars(env.vars)
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load settings'))
      .finally(() => setLoading(false))
    reloadClaudeAuthStatus()
  }, [])

  const handleClaudeAuthSubmit = async () => {
    setClaudeAuthSubmitting(true)
    setClaudeAuthError(null)
    const token = claudeAuthInput.trim()
    if (!token.startsWith('sk-ant-')) {
      setClaudeAuthError('Token should start with sk-ant-')
      setClaudeAuthSubmitting(false)
      return
    }
    try {
      await bootstrapClaudeAuth(token)
      setClaudeAuthInput('')
      setClaudeAuthEditing(false)
      reloadClaudeAuthStatus()
    } catch (err) {
      setClaudeAuthError(err instanceof Error ? err.message : 'Failed to bootstrap Claude authentication')
    } finally {
      setClaudeAuthSubmitting(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    setSaved(false)
    try {
      await Promise.all([
        updateDefaults(defaults),
        updateEnvDefaults({ vars: envVars }),
      ])
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <section className="rounded-2xl border border-white/10 bg-slate-950/60 p-6 shadow-lg shadow-black/40">
        <p className="text-sm text-white/60">Loading settings...</p>
      </section>
    )
  }

  return (
    <section className="space-y-6">
      {error && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-2 text-sm text-rose-200">
          {error}
        </div>
      )}

      <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-6 shadow-lg shadow-black/40">
        <h3 className="mb-4 text-base font-semibold text-white">Dotfiles and defaults</h3>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-semibold text-white/80" htmlFor="settings-dotfiles-repo">
              Dotfiles repository
            </label>
            <input
              id="settings-dotfiles-repo"
              value={defaults.dotfilesRepo ?? ''}
              onChange={(e) => setDefaults({ ...defaults, dotfilesRepo: e.target.value })}
              className={`${INPUT_BASE} ${INPUT_OK}`}
              placeholder="https://github.com/owner/dotfiles"
            />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="text-sm font-semibold text-white/80" htmlFor="settings-dotfiles-method">
                Method
              </label>
              <select
                id="settings-dotfiles-method"
                value={defaults.dotfilesMethod ?? 'none'}
                onChange={(e) => setDefaults({ ...defaults, dotfilesMethod: e.target.value as DotfilesDefaults['dotfilesMethod'] })}
                className={`${INPUT_BASE} ${INPUT_OK}`}
              >
                <option value="none">none</option>
                <option value="bare-git">bare-git</option>
                <option value="clone">clone</option>
                <option value="command">command</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-semibold text-white/80" htmlFor="settings-dotfiles-baredir">
                Bare repo dir
              </label>
              <input
                id="settings-dotfiles-baredir"
                value={defaults.dotfilesBareDir ?? ''}
                onChange={(e) => setDefaults({ ...defaults, dotfilesBareDir: e.target.value })}
                className={`${INPUT_BASE} ${INPUT_OK}`}
                placeholder=".cfg"
              />
            </div>
          </div>
          <div>
            <label className="text-sm font-semibold text-white/80" htmlFor="settings-dotfiles-command">
              Dotfiles command
            </label>
            <input
              id="settings-dotfiles-command"
              value={defaults.dotfilesCommand ?? ''}
              onChange={(e) => setDefaults({ ...defaults, dotfilesCommand: e.target.value })}
              className={`${INPUT_BASE} ${INPUT_OK}`}
              placeholder="curl -Ls https://example.com/setup | bash"
            />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="text-sm font-semibold text-white/80" htmlFor="settings-default-branch">
                Default branch
              </label>
              <input
                id="settings-default-branch"
                value={defaults.defaultBranch ?? ''}
                onChange={(e) => setDefaults({ ...defaults, defaultBranch: e.target.value })}
                className={`${INPUT_BASE} ${INPUT_OK}`}
                placeholder="main"
              />
            </div>
            <div>
              <label className="text-sm font-semibold text-white/80" htmlFor="settings-init-command">
                Init command
              </label>
              <input
                id="settings-init-command"
                value={defaults.initCommand ?? ''}
                onChange={(e) => setDefaults({ ...defaults, initCommand: e.target.value })}
                className={`${INPUT_BASE} ${INPUT_OK}`}
                placeholder="~/.dotfiles/install.sh"
              />
            </div>
          </div>
          <div>
            <label className="text-sm font-semibold text-white/80" htmlFor="settings-ssh-pubkey">
              SSH public key
            </label>
            <p className="mb-1 text-xs text-white/50">
              Added to authorized_keys in the pod. Required for SSHFS workspace mounting.
            </p>
            <textarea
              id="settings-ssh-pubkey"
              value={defaults.sshPublicKey ?? ''}
              onChange={(e) => setDefaults({ ...defaults, sshPublicKey: e.target.value })}
              className={`${INPUT_BASE} ${INPUT_OK} min-h-[4.5rem] resize-y font-mono text-xs`}
              placeholder="Paste contents of ~/.ssh/id_ed25519.pub"
              rows={2}
            />
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-6 shadow-lg shadow-black/40">
        <h3 className="mb-4 text-base font-semibold text-white">Default environment variables</h3>
        <p className="mb-4 text-sm text-white/50">
          These env vars pre-populate every new koolna. Per-koolna overrides are set in the create form.
        </p>
        <EnvVarEditor vars={envVars} onChange={setEnvVars} />
      </div>

      <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-6 shadow-lg shadow-black/40">
        <div className="mb-3 flex items-center gap-3">
          <h3 className="text-base font-semibold text-white">Claude authentication</h3>
          {claudeAuthStatus === null ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/5 px-2 py-0.5 text-xs text-white/50">
              <span className="h-1.5 w-1.5 rounded-full bg-white/30" />
              Broker unreachable
            </span>
          ) : claudeAuthStatus.bootstrapped ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-300">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              Bootstrapped
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2 py-0.5 text-xs text-amber-300">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
              Not bootstrapped
            </span>
          )}
        </div>
        <p className="mb-4 text-sm text-white/60">
          Seeds the in-cluster token broker with a Claude OAuth token. Workspaces
          with &quot;Enable Claude authentication&quot; checked will fetch this token
          at every tmux shell launch. The token is valid for ~1 year. Bootstrap once,
          replace when it expires or is revoked.
        </p>

        {(!claudeAuthStatus?.bootstrapped || claudeAuthEditing) && (
          <div className="space-y-3">
            <div className="rounded-xl border border-white/10 bg-slate-900/40 p-4 text-sm text-white/70">
              <p className="mb-2 font-semibold text-white/80">How to get the token</p>
              <ol className="list-decimal space-y-1 pl-5">
                <li>On a workstation with Claude Pro or Max, run <code className="rounded bg-white/10 px-1">claude setup-token</code>.</li>
                <li>Complete the browser OAuth flow.</li>
                <li>Copy the printed token (starts with <code className="rounded bg-white/10 px-1">sk-ant-</code>) and paste it below.</li>
              </ol>
            </div>

            <input
              type="password"
              value={claudeAuthInput}
              onChange={(e) => setClaudeAuthInput(e.target.value)}
              className={`${INPUT_BASE} ${INPUT_OK} font-mono text-xs`}
              placeholder="sk-ant-oat01-..."
              autoComplete="off"
            />

            {claudeAuthError && (
              <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-2 text-sm text-rose-200">
                {claudeAuthError}
              </div>
            )}

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleClaudeAuthSubmit}
                disabled={claudeAuthSubmitting || !claudeAuthInput.trim()}
                className="inline-flex items-center justify-center rounded-2xl border border-transparent bg-sky-500 px-5 py-2 text-sm font-semibold text-white transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {claudeAuthSubmitting && (
                  <span className="mr-2 h-3 w-3 animate-spin rounded-full border border-t-white border-white/20" />
                )}
                Bootstrap broker
              </button>
              {claudeAuthEditing && (
                <button
                  type="button"
                  onClick={() => {
                    setClaudeAuthEditing(false)
                    setClaudeAuthInput('')
                    setClaudeAuthError(null)
                  }}
                  className="rounded-2xl border border-white/20 bg-white/5 px-5 py-2 text-sm font-semibold text-white transition hover:border-white/40"
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
        )}

        {claudeAuthStatus?.bootstrapped && !claudeAuthEditing && (
          <button
            type="button"
            onClick={() => setClaudeAuthEditing(true)}
            className="text-sm text-sky-400 underline-offset-2 hover:underline"
          >
            Replace credentials
          </button>
        )}
      </div>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="inline-flex items-center justify-center rounded-2xl border border-transparent bg-sky-500 px-5 py-2 text-sm font-semibold text-white transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {saving && (
            <span className="mr-2 h-3 w-3 animate-spin rounded-full border border-t-white border-white/20" />
          )}
          Save settings
        </button>
        {saved && (
          <span className="text-sm text-emerald-400">Saved</span>
        )}
      </div>
    </section>
  )
}

export default Settings
