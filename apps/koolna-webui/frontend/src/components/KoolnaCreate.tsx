import { type FormEvent, useCallback, useEffect, useRef, useState } from 'react'
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
  gitUsername: string
  gitToken: string
  gitName: string
  gitEmail: string
}

type ValidatableField = 'name' | 'repo' | 'branch' | 'image' | 'storage'
  | 'gitName' | 'gitEmail' | 'gitUsername' | 'gitToken' | 'dotfilesBareDir'

const FIELD_HELP: Record<ValidatableField, string> = {
  name: 'Unique identifier for your environment. Lowercase alphanumeric with hyphens, must start and end with a letter or digit.',
  repo: 'Git repository to clone into your workspace. Must be a full HTTPS URL.',
  branch: 'Branch to check out after cloning.',
  image: 'Container image that runs your development environment.',
  storage: 'Persistent volume size for your workspace data.',
  gitName: 'Used as git user.name for commits made in this environment.',
  gitEmail: 'Used as git user.email for commits made in this environment.',
  gitUsername: 'Git service username for authenticating repository access.',
  gitToken: 'Authentication token for pulling and pushing to the repository.',
  dotfilesBareDir: 'Directory name where the bare git repository is checked out.',
}

function isFieldInvalid(field: ValidatableField, state: FormState): boolean {
  switch (field) {
    case 'name':
      return !NAME_PATTERN.test(state.name)
    case 'repo':
      return !REPO_PATTERN.test(state.repo)
    case 'dotfilesBareDir':
      return state.dotfilesMethod === 'bare-git' && !!state.dotfilesRepo.trim() && !state.dotfilesBareDir.trim()
    default:
      return !state[field].trim()
  }
}

const INPUT_BASE = 'mt-2 w-full rounded-xl border px-4 py-2 text-sm text-white transition focus:outline-none focus:ring-1'
const INPUT_OK = 'border-white/10 bg-slate-900/60 focus:border-sky-400 focus:ring-sky-400'
const INPUT_ERR = 'border-rose-500/60 bg-rose-500/5 focus:border-rose-400 focus:ring-rose-400'

function FieldHelp({ field }: { field: ValidatableField }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  return (
    <div className="relative inline-block" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="ml-1.5 inline-flex h-4 w-4 items-center justify-center rounded-full bg-rose-500/20 text-[0.625rem] leading-none text-rose-300 transition hover:bg-rose-500/30 hover:text-rose-200"
        aria-label={`Help for ${field}`}
      >
        ?
      </button>
      {open && (
        <div className="absolute left-1/2 top-full z-50 mt-2 w-56 -translate-x-1/2 rounded-lg border border-white/10 bg-slate-800 px-3 py-2 text-xs text-white/80 shadow-xl">
          <div className="absolute -top-1 left-1/2 h-2 w-2 -translate-x-1/2 rotate-45 border-l border-t border-white/10 bg-slate-800" />
          {FIELD_HELP[field]}
        </div>
      )}
    </div>
  )
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
    gitUsername: '',
    gitToken: '',
    gitName: '',
    gitEmail: '',
  })
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<ValidatableField, true>>>({})
  const [touched, setTouched] = useState<Partial<Record<ValidatableField, true>>>({})
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
    const secret = formState.gitToken.trim()
      ? `${formState.name}-git`
      : undefined
    listBranches(repo, secret)
      .then((result) => setBranches(result))
      .catch(() => setBranches([]))
  }, [formState.repo, formState.gitToken, formState.name])

  const revalidate = (field: ValidatableField, state: FormState) => {
    setFieldErrors((prev) => {
      const next = { ...prev }
      if (isFieldInvalid(field, state)) {
        next[field] = true
      } else {
        delete next[field]
      }
      return next
    })
  }

  const handleFieldChange = (field: keyof FormState, value: string) => {
    const newState = { ...formState, [field]: value }
    setFormState(newState)
    if (touched[field as ValidatableField]) {
      revalidate(field as ValidatableField, newState)
    }
    if ((field === 'dotfilesRepo' || field === 'dotfilesMethod') && touched.dotfilesBareDir) {
      revalidate('dotfilesBareDir', newState)
    }
  }

  const handleBlur = (field: ValidatableField) => {
    setTouched((prev) => ({ ...prev, [field]: true }))
    revalidate(field, formState)
  }

  const inputClass = (field: ValidatableField) =>
    `${INPUT_BASE} ${touched[field] && fieldErrors[field] ? INPUT_ERR : INPUT_OK}`

  const showHelp = (field: ValidatableField) =>
    !!(touched[field] && fieldErrors[field])

  const validate = (): boolean => {
    const fields: ValidatableField[] = [
      'name', 'repo', 'branch', 'image', 'storage',
      'gitName', 'gitEmail', 'gitUsername', 'gitToken',
    ]
    if (formState.dotfilesMethod === 'bare-git' && formState.dotfilesRepo.trim()) {
      fields.push('dotfilesBareDir')
    }
    const newErrors: Partial<Record<ValidatableField, true>> = {}
    const newTouched: Partial<Record<ValidatableField, true>> = {}
    for (const field of fields) {
      newTouched[field] = true
      if (isFieldInvalid(field, formState)) {
        newErrors[field] = true
      }
    }
    setTouched((prev) => ({ ...prev, ...newTouched }))
    setFieldErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!validate()) return
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
    if (formState.gitName.trim()) payload.gitName = formState.gitName.trim()
    if (formState.gitEmail.trim()) payload.gitEmail = formState.gitEmail.trim()
    if (formState.gitUsername.trim()) payload.gitUsername = formState.gitUsername.trim()
    if (formState.gitToken.trim()) payload.gitToken = formState.gitToken.trim()

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
          <div className="flex items-center">
            <label className="text-sm font-semibold text-white/80" htmlFor="koolna-name">
              Name
            </label>
            {showHelp('name') && <FieldHelp field="name" />}
          </div>
          <input
            id="koolna-name"
            value={formState.name}
            onChange={(event) => handleFieldChange('name', event.target.value)}
            onBlur={() => handleBlur('name')}
            className={inputClass('name')}
            placeholder="e.g. my-koolna"
          />
        </div>

        <div>
          <div className="flex items-center">
            <label className="text-sm font-semibold text-white/80" htmlFor="koolna-repo">
              Repository
            </label>
            {showHelp('repo') && <FieldHelp field="repo" />}
          </div>
          <input
            id="koolna-repo"
            value={formState.repo}
            onChange={(event) => handleFieldChange('repo', event.target.value)}
            onBlur={() => { handleBlur('repo'); fetchBranches() }}
            className={inputClass('repo')}
            placeholder="https://github.com/owner/repo"
          />
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <div className="flex items-center">
              <label className="text-sm font-semibold text-white/80" htmlFor="koolna-git-name">
                Committer name
              </label>
              {showHelp('gitName') && <FieldHelp field="gitName" />}
            </div>
            <input
              id="koolna-git-name"
              value={formState.gitName}
              onChange={(event) => handleFieldChange('gitName', event.target.value)}
              onBlur={() => handleBlur('gitName')}
              className={inputClass('gitName')}
              placeholder="Jane Doe"
            />
          </div>
          <div>
            <div className="flex items-center">
              <label className="text-sm font-semibold text-white/80" htmlFor="koolna-git-email">
                Committer email
              </label>
              {showHelp('gitEmail') && <FieldHelp field="gitEmail" />}
            </div>
            <input
              id="koolna-git-email"
              type="email"
              value={formState.gitEmail}
              onChange={(event) => handleFieldChange('gitEmail', event.target.value)}
              onBlur={() => handleBlur('gitEmail')}
              className={inputClass('gitEmail')}
              placeholder="jane@example.com"
            />
          </div>
          <div>
            <div className="flex items-center">
              <label className="text-sm font-semibold text-white/80" htmlFor="koolna-git-username">
                Username
              </label>
              {showHelp('gitUsername') && <FieldHelp field="gitUsername" />}
            </div>
            <input
              id="koolna-git-username"
              value={formState.gitUsername}
              onChange={(event) => handleFieldChange('gitUsername', event.target.value)}
              onBlur={() => handleBlur('gitUsername')}
              className={inputClass('gitUsername')}
              autoComplete="username"
            />
          </div>
          <div>
            <div className="flex items-center">
              <label className="text-sm font-semibold text-white/80" htmlFor="koolna-git-token">
                Personal access token
              </label>
              {showHelp('gitToken') && <FieldHelp field="gitToken" />}
            </div>
            <input
              id="koolna-git-token"
              type="password"
              value={formState.gitToken}
              onChange={(event) => handleFieldChange('gitToken', event.target.value)}
              onBlur={() => handleBlur('gitToken')}
              className={inputClass('gitToken')}
              autoComplete="off"
            />
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <div className="flex items-center">
              <label className="text-sm font-semibold text-white/80" htmlFor="koolna-branch">
                Branch
              </label>
              {showHelp('branch') && <FieldHelp field="branch" />}
            </div>
            <input
              id="koolna-branch"
              list="branch-options"
              value={formState.branch}
              onChange={(event) => handleFieldChange('branch', event.target.value)}
              onBlur={() => handleBlur('branch')}
              className={inputClass('branch')}
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
            <div className="flex items-center">
              <label className="text-sm font-semibold text-white/80" htmlFor="koolna-storage">
                Storage
              </label>
              {showHelp('storage') && <FieldHelp field="storage" />}
            </div>
            <input
              id="koolna-storage"
              value={formState.storage}
              onChange={(event) => handleFieldChange('storage', event.target.value)}
              onBlur={() => handleBlur('storage')}
              className={inputClass('storage')}
            />
          </div>
        </div>

        <div>
          <div className="flex items-center">
            <label className="text-sm font-semibold text-white/80" htmlFor="koolna-image">
              Image
            </label>
            {showHelp('image') && <FieldHelp field="image" />}
          </div>
          <>
            <input
              id="koolna-image"
              list="image-options"
              value={formState.image}
              onChange={(event) => handleFieldChange('image', event.target.value)}
              onBlur={() => handleBlur('image')}
              className={inputClass('image')}
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
            className={`${INPUT_BASE} ${INPUT_OK}`}
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
                className={`${INPUT_BASE} ${INPUT_OK}`}
                placeholder="https://github.com/owner/dotfiles"
              />
            </div>

            {formState.dotfilesMethod === 'bare-git' && (
              <div>
                <div className="flex items-center">
                  <label className="text-sm font-semibold text-white/80" htmlFor="koolna-dotfiles-baredir">
                    Bare repo dir
                  </label>
                  {showHelp('dotfilesBareDir') && <FieldHelp field="dotfilesBareDir" />}
                </div>
                <input
                  id="koolna-dotfiles-baredir"
                  value={formState.dotfilesBareDir}
                  onChange={(event) => handleFieldChange('dotfilesBareDir', event.target.value)}
                  onBlur={() => handleBlur('dotfilesBareDir')}
                  className={inputClass('dotfilesBareDir')}
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
              className={`${INPUT_BASE} ${INPUT_OK}`}
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
              className={`${INPUT_BASE} ${INPUT_OK}`}
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
