import { useEffect, useState } from 'react'
import {
  type DotfilesDefaults,
  type DotfilesMethod,
  type EnvVar,
  getDefaults,
  getEnvDefaults,
  updateDefaults,
  updateEnvDefaults,
} from '../api/koolna'
import { EnvVarEditor } from './EnvVarEditor'

const IMAGE_OPTIONS = [
  'ghcr.io/buvis/koolna-dev:latest',
  'ghcr.io/buvis/koolna-base:latest',
  'ghcr.io/buvis/koolna-base:python',
  'ghcr.io/buvis/koolna-base:node',
] as const

const DOTFILES_METHODS: DotfilesMethod[] = ['none', 'bare-git', 'clone', 'command']

const INPUT_BASE = 'mt-2 w-full rounded-xl border px-4 py-2 text-sm text-text transition focus:outline-none focus:ring-1'
const INPUT_OK = 'border-border bg-surface focus:border-accent focus:ring-accent'

export function Settings() {
  const [defaults, setDefaults] = useState<DotfilesDefaults>({})
  const [envVars, setEnvVars] = useState<EnvVar[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    Promise.all([getDefaults(), getEnvDefaults()])
      .then(([d, env]) => {
        setDefaults(d)
        setEnvVars(env.vars)
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Failed to load settings'))
      .finally(() => setLoading(false))
  }, [])

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
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <section className="rounded-2xl border border-border bg-surface p-6 shadow-lg shadow-black/40">
        <p className="text-sm text-text-muted">Loading settings...</p>
      </section>
    )
  }

  return (
    <section className="space-y-5">
      {error && (
        <div className="rounded-xl border border-danger/40 bg-danger/10 px-4 py-2 text-sm text-danger">
          {error}
        </div>
      )}

      <div className="rounded-2xl border border-border bg-surface p-6 shadow-lg shadow-black/40">
        <h3 className="mb-4 text-base font-semibold text-text">Defaults</h3>
        <p className="mb-4 text-sm text-text-muted">
          These values pre-populate the create form for every new koolna.
        </p>
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="text-sm font-semibold text-text-muted" htmlFor="settings-git-name">
                Committer name
              </label>
              <input
                id="settings-git-name"
                value={defaults.gitName ?? ''}
                onChange={(e) => setDefaults({ ...defaults, gitName: e.target.value })}
                className={`${INPUT_BASE} ${INPUT_OK}`}
                placeholder="Jane Doe"
              />
            </div>
            <div>
              <label className="text-sm font-semibold text-text-muted" htmlFor="settings-git-email">
                Committer email
              </label>
              <input
                id="settings-git-email"
                type="email"
                value={defaults.gitEmail ?? ''}
                onChange={(e) => setDefaults({ ...defaults, gitEmail: e.target.value })}
                className={`${INPUT_BASE} ${INPUT_OK}`}
                placeholder="jane@example.com"
              />
            </div>
            <div>
              <label className="text-sm font-semibold text-text-muted" htmlFor="settings-git-username">
                Username
              </label>
              <input
                id="settings-git-username"
                value={defaults.gitUsername ?? ''}
                onChange={(e) => setDefaults({ ...defaults, gitUsername: e.target.value })}
                className={`${INPUT_BASE} ${INPUT_OK}`}
                autoComplete="username"
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="text-sm font-semibold text-text-muted" htmlFor="settings-default-branch">
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
              <label className="text-sm font-semibold text-text-muted" htmlFor="settings-storage">
                Storage
              </label>
              <input
                id="settings-storage"
                value={defaults.storage ?? ''}
                onChange={(e) => setDefaults({ ...defaults, storage: e.target.value })}
                className={`${INPUT_BASE} ${INPUT_OK}`}
                placeholder="10Gi"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-semibold text-text-muted" htmlFor="settings-image">
              Image
            </label>
            <input
              id="settings-image"
              list="settings-image-options"
              value={defaults.image ?? ''}
              onChange={(e) => setDefaults({ ...defaults, image: e.target.value })}
              className={`${INPUT_BASE} ${INPUT_OK}`}
              placeholder="ghcr.io/buvis/koolna-dev:latest"
            />
            <datalist id="settings-image-options">
              {IMAGE_OPTIONS.map((option) => (
                <option key={option} value={option} />
              ))}
            </datalist>
          </div>

          <div>
            <label className="text-sm font-semibold text-text-muted" htmlFor="settings-ssh-pubkey">
              SSH public key
            </label>
            <p className="mb-1 text-xs text-text-muted">
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

          <div>
            <label className="text-sm font-semibold text-text-muted">
              Environment variables
            </label>
            <div className="mt-2">
              <EnvVarEditor vars={envVars} onChange={setEnvVars} />
            </div>
          </div>

          <div>
            <label className="text-sm font-semibold text-text-muted" htmlFor="settings-dotfiles-method">
              Dotfiles
            </label>
            <select
              id="settings-dotfiles-method"
              value={defaults.dotfilesMethod ?? 'none'}
              onChange={(e) => setDefaults({ ...defaults, dotfilesMethod: e.target.value as DotfilesMethod })}
              className={`${INPUT_BASE} ${INPUT_OK}`}
            >
              {DOTFILES_METHODS.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          {(defaults.dotfilesMethod === 'bare-git' || defaults.dotfilesMethod === 'clone') && (
            <div className={`grid gap-4 ${defaults.dotfilesMethod === 'bare-git' ? 'sm:grid-cols-2' : ''}`}>
              <div>
                <label className="text-sm font-semibold text-text-muted" htmlFor="settings-dotfiles-repo">
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

              {defaults.dotfilesMethod === 'bare-git' && (
                <div>
                  <label className="text-sm font-semibold text-text-muted" htmlFor="settings-dotfiles-baredir">
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
              )}
            </div>
          )}

          {defaults.dotfilesMethod === 'command' && (
            <div>
              <label className="text-sm font-semibold text-text-muted" htmlFor="settings-dotfiles-command">
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
          )}

          <div>
            <label className="text-sm font-semibold text-text-muted" htmlFor="settings-init-command">
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
      </div>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="inline-flex items-center justify-center rounded-2xl border border-transparent bg-accent px-5 py-2 text-sm font-semibold text-white transition hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-60"
        >
          {saving && (
            <span className="mr-2 h-3 w-3 animate-spin rounded-full border border-t-white border-white/20" />
          )}
          Save settings
        </button>
        {saved && (
          <span className="text-sm text-phase-running">Saved</span>
        )}
      </div>
    </section>
  )
}

export default Settings
