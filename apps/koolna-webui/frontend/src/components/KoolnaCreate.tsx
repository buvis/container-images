import { type FormEvent, useCallback, useEffect, useState } from 'react'
import { createKoolna, type CreateKoolnaRequest, type DotfilesMethod, getDefaults, listBranches } from '../api/koolna'

const IMAGE_OPTIONS = [
  'ghcr.io/buvis/koolna-base:latest',
  'ghcr.io/buvis/koolna-base:python',
  'ghcr.io/buvis/koolna-base:node',
] as const

const NAME_PATTERN = /^[a-z0-9][a-z0-9-]*[a-z0-9]$/
const REPO_PATTERN = /^https:\/\/[^/]+\/.+$/
const DOTFILES_METHODS: DotfilesMethod[] = ['none', 'bare-git', 'clone', 'command']

type FormState = {
  name: string
  repo: string
  branch: string
  image: string
  storage: string
  dotfilesMethod: DotfilesMethod
  dotfilesRepo: string
  dotfilesBareDir: string
  dotfilesCommand: string
  dotfilesInit: string
  privateRepo: boolean
  gitUsername: string
  gitToken: string
  gitName: string
  gitEmail: string
}

type ValidationError = {
  name?: string
  repo?: string
}

interface KoolnaCreateProps {
  onCreated: () => void
  onCancel?: () => void
}

export function KoolnaCreate({ onCreated, onCancel }: KoolnaCreateProps) {
  const [formState, setFormState] = useState<FormState>({
    name: '',
    repo: '',
    branch: 'main',
    image: IMAGE_OPTIONS[0],
    storage: '10Gi',
    dotfilesMethod: 'bare-git',
    dotfilesRepo: '',
    dotfilesBareDir: '',
    dotfilesCommand: '',
    dotfilesInit: '',
    privateRepo: false,
    gitUsername: '',
    gitToken: '',
    gitName: '',
    gitEmail: '',
  })
  const [errors, setErrors] = useState<ValidationError>({})
  const [apiError, setApiError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [branches, setBranches] = useState<string[]>([])

  useEffect(() => {
    getDefaults().then((defaults) => {
      setFormState((prev) => ({
        ...prev,
        branch: defaults.defaultBranch ?? prev.branch,
        dotfilesMethod: defaults.dotfilesMethod ?? prev.dotfilesMethod,
        dotfilesRepo: defaults.dotfilesRepo ?? prev.dotfilesRepo,
        dotfilesBareDir: defaults.dotfilesBareDir ?? prev.dotfilesBareDir,
        dotfilesCommand: defaults.dotfilesCommand ?? prev.dotfilesCommand,
        dotfilesInit: defaults.dotfilesInit ?? prev.dotfilesInit,
      }))
    }).catch(() => {})
  }, [])

  const fetchBranches = useCallback(() => {
    const repo = formState.repo.trim()
    if (!REPO_PATTERN.test(repo)) return
    const secret = formState.privateRepo && formState.gitToken.trim()
      ? `${formState.name}-git`
      : undefined
    listBranches(repo, secret)
      .then((result) => {
        setBranches(result)
        if (!formState.privateRepo && result.length === 0) return
      })
      .catch(() => {
        setBranches([])
        if (!formState.privateRepo) {
          setFormState((prev) => ({ ...prev, privateRepo: true }))
        }
      })
  }, [formState.repo, formState.privateRepo, formState.gitToken, formState.name])

  const handleFieldChange = (field: keyof FormState, value: string | boolean) => {
    setFormState((prev) => ({
      ...prev,
      [field]: value,
    }))
    if (field === 'name' || field === 'repo') {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }))
    }
  }

  const validate = (): boolean => {
    const newErrors: ValidationError = {}
    if (!NAME_PATTERN.test(formState.name)) {
      newErrors.name =
        'Name must be lowercase, may include hyphens, and start/end with an alphanumeric.'
    }
    if (!REPO_PATTERN.test(formState.repo)) {
      newErrors.repo = 'Repo must be a full HTTPS URL (e.g. https://github.com/owner/repo).'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!validate()) {
      return
    }
    setLoading(true)
    setApiError(null)

    const payload: CreateKoolnaRequest = {
      name: formState.name,
      repo: formState.repo,
      branch: formState.branch,
      image: formState.image,
      storage: formState.storage,
    }

    if (formState.dotfilesMethod !== 'none') {
      payload.dotfilesMethod = formState.dotfilesMethod
      if (formState.dotfilesMethod === 'command') {
        if (formState.dotfilesCommand.trim()) {
          payload.dotfilesCommand = formState.dotfilesCommand.trim()
        }
      } else {
        if (formState.dotfilesRepo.trim()) {
          payload.dotfilesRepo = formState.dotfilesRepo.trim()
        }
        if (formState.dotfilesMethod === 'bare-git' && formState.dotfilesBareDir.trim()) {
          payload.dotfilesBareDir = formState.dotfilesBareDir.trim()
        }
      }
      if (formState.dotfilesInit.trim()) {
        payload.dotfilesInit = formState.dotfilesInit.trim()
      }
    }
    if (formState.privateRepo && formState.gitUsername.trim() && formState.gitToken.trim()) {
      payload.gitUsername = formState.gitUsername.trim()
      payload.gitToken = formState.gitToken.trim()
      if (formState.gitName.trim()) payload.gitName = formState.gitName.trim()
      if (formState.gitEmail.trim()) payload.gitEmail = formState.gitEmail.trim()
    }

    try {
      await createKoolna(payload)
      onCreated()
    } catch (error) {
      setApiError(
        error instanceof Error
          ? error.message
          : 'Unable to create Koolna environment right now.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="rounded-2xl border border-white/10 bg-slate-950/60 p-6 shadow-lg shadow-black/40">
      <header className="mb-6">
        <h2 className="text-lg font-semibold text-white">Create a Koolna</h2>
        <p className="text-sm text-white/70">Provision a fresh development stack.</p>
      </header>

      {apiError && (
        <div className="mb-4 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-2 text-sm text-rose-200">
          {apiError}
        </div>
      )}

      <form className="space-y-5" onSubmit={handleSubmit} noValidate>
        <div>
          <label className="text-sm font-semibold text-white/80" htmlFor="koolna-name">
            Name
          </label>
          <input
            id="koolna-name"
            value={formState.name}
            onChange={(event) => handleFieldChange('name', event.target.value)}
            className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/60 px-4 py-2 text-sm text-white transition focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
            placeholder="e.g. my-koolna"
          />
          {errors.name && (
            <p className="mt-1 text-xs text-rose-400">{errors.name}</p>
          )}
        </div>

        <div>
          <label className="text-sm font-semibold text-white/80" htmlFor="koolna-repo">
            Repository
          </label>
          <input
            id="koolna-repo"
            value={formState.repo}
            onChange={(event) => handleFieldChange('repo', event.target.value)}
            className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/60 px-4 py-2 text-sm text-white transition focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
            placeholder="https://github.com/owner/repo"
            onBlur={fetchBranches}
          />
          {errors.repo && (
            <p className="mt-1 text-xs text-rose-400">{errors.repo}</p>
          )}
        </div>

        <div>
          <label className="inline-flex cursor-pointer items-center gap-2">
            <input
              type="checkbox"
              checked={formState.privateRepo}
              onChange={(event) => handleFieldChange('privateRepo', event.target.checked)}
              className="h-4 w-4 rounded border-white/20 bg-slate-900/60 text-sky-500 focus:ring-sky-400"
            />
            <span className="text-sm font-semibold text-white/80">Private repository</span>
          </label>
        </div>

        {formState.privateRepo && (
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="text-sm font-semibold text-white/80" htmlFor="koolna-git-username">
                Username
              </label>
              <input
                id="koolna-git-username"
                value={formState.gitUsername}
                onChange={(event) => handleFieldChange('gitUsername', event.target.value)}
                className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/60 px-4 py-2 text-sm text-white transition focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
                autoComplete="username"
              />
            </div>
            <div>
              <label className="text-sm font-semibold text-white/80" htmlFor="koolna-git-token">
                Personal access token
              </label>
              <input
                id="koolna-git-token"
                type="password"
                value={formState.gitToken}
                onChange={(event) => handleFieldChange('gitToken', event.target.value)}
                className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/60 px-4 py-2 text-sm text-white transition focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
                autoComplete="off"
              />
            </div>
            <div>
              <label className="text-sm font-semibold text-white/80" htmlFor="koolna-git-name">
                Committer name
              </label>
              <input
                id="koolna-git-name"
                value={formState.gitName}
                onChange={(event) => handleFieldChange('gitName', event.target.value)}
                className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/60 px-4 py-2 text-sm text-white transition focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
                placeholder="Jane Doe"
              />
            </div>
            <div>
              <label className="text-sm font-semibold text-white/80" htmlFor="koolna-git-email">
                Committer email
              </label>
              <input
                id="koolna-git-email"
                type="email"
                value={formState.gitEmail}
                onChange={(event) => handleFieldChange('gitEmail', event.target.value)}
                className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/60 px-4 py-2 text-sm text-white transition focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
                placeholder="jane@example.com"
              />
            </div>
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="text-sm font-semibold text-white/80" htmlFor="koolna-branch">
              Branch
            </label>
            <input
              id="koolna-branch"
              list="branch-options"
              value={formState.branch}
              onChange={(event) => handleFieldChange('branch', event.target.value)}
              className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/60 px-4 py-2 text-sm text-white transition focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
            />
            {branches.length > 0 && (
              <datalist id="branch-options">
                {branches.map((b) => (
                  <option key={b} value={b} />
                ))}
              </datalist>
            )}
          </div>

          <div>
            <label className="text-sm font-semibold text-white/80" htmlFor="koolna-storage">
              Storage
            </label>
            <input
              id="koolna-storage"
              value={formState.storage}
              onChange={(event) => handleFieldChange('storage', event.target.value)}
              className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/60 px-4 py-2 text-sm text-white transition focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
            />
          </div>
        </div>

        <div>
          <label className="text-sm font-semibold text-white/80" htmlFor="koolna-image">
            Image
          </label>
          <>
            <input
              id="koolna-image"
              list="image-options"
              value={formState.image}
              onChange={(event) => handleFieldChange('image', event.target.value)}
              className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/60 px-4 py-2 text-sm text-white transition focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
              placeholder="ghcr.io/buvis/koolna-base:latest"
            />
            <datalist id="image-options">
              {IMAGE_OPTIONS.map((option) => (
                <option key={option} value={option} />
              ))}
            </datalist>
          </>
        </div>

        <div>
          <label className="text-sm font-semibold text-white/80" htmlFor="koolna-dotfiles-method">
            Dotfiles
          </label>
          <select
            id="koolna-dotfiles-method"
            value={formState.dotfilesMethod}
            onChange={(event) => handleFieldChange('dotfilesMethod', event.target.value)}
            className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/60 px-4 py-2 text-sm text-white transition focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
          >
            {DOTFILES_METHODS.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>

        {(formState.dotfilesMethod === 'bare-git' || formState.dotfilesMethod === 'clone') && (
          <div className={`grid gap-4 ${formState.dotfilesMethod === 'bare-git' ? 'md:grid-cols-2' : ''}`}>
            <div>
              <label className="text-sm font-semibold text-white/80" htmlFor="koolna-dotfiles-repo">
                Repository
              </label>
              <input
                id="koolna-dotfiles-repo"
                value={formState.dotfilesRepo}
                onChange={(event) => handleFieldChange('dotfilesRepo', event.target.value)}
                className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/60 px-4 py-2 text-sm text-white transition focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
                placeholder="https://github.com/owner/dotfiles"
              />
            </div>

            {formState.dotfilesMethod === 'bare-git' && (
              <div>
                <label className="text-sm font-semibold text-white/80" htmlFor="koolna-dotfiles-baredir">
                  Bare repo dir
                </label>
                <input
                  id="koolna-dotfiles-baredir"
                  value={formState.dotfilesBareDir}
                  onChange={(event) => handleFieldChange('dotfilesBareDir', event.target.value)}
                  className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/60 px-4 py-2 text-sm text-white transition focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
                  placeholder=".cfg"
                />
              </div>
            )}
          </div>
        )}

        {formState.dotfilesMethod === 'command' && (
          <div>
            <label className="text-sm font-semibold text-white/80" htmlFor="koolna-dotfiles-command">
              Command
            </label>
            <input
              id="koolna-dotfiles-command"
              value={formState.dotfilesCommand}
              onChange={(event) => handleFieldChange('dotfilesCommand', event.target.value)}
              className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/60 px-4 py-2 text-sm text-white transition focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
              placeholder="curl -Ls https://example.com/setup | bash"
            />
          </div>
        )}

        {formState.dotfilesMethod !== 'none' && (
          <div>
            <label className="text-sm font-semibold text-white/80" htmlFor="koolna-dotfiles-init">
              Init command (optional)
            </label>
            <input
              id="koolna-dotfiles-init"
              value={formState.dotfilesInit}
              onChange={(event) => handleFieldChange('dotfilesInit', event.target.value)}
              className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/60 px-4 py-2 text-sm text-white transition focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
              placeholder="~/.dotfiles/install.sh"
            />
          </div>
        )}

        <div className="flex flex-wrap gap-3 pt-2">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center justify-center rounded-2xl border border-transparent bg-sky-500 px-5 py-2 text-sm font-semibold text-white transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading && (
              <span className="mr-2 h-3 w-3 animate-spin rounded-full border border-t-white border-white/20" />
            )}
            Create Koolna
          </button>
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="rounded-2xl border border-white/20 bg-white/5 px-5 py-2 text-sm font-semibold text-white transition hover:border-white/40"
            >
              Cancel
            </button>
          )}
        </div>
      </form>
    </section>
  )
}

export default KoolnaCreate
