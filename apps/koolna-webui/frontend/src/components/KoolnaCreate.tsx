import { FormEvent, useState } from 'react'
import { createKoolna, CreateKoolnaRequest } from '../api/koolna'

const IMAGE_OPTIONS = [
  'ghcr.io/buvis/koolna-base:latest',
  'ghcr.io/buvis/koolna-node:latest',
] as const

const NAME_PATTERN = /^[a-z0-9][a-z0-9-]*[a-z0-9]$/
const REPO_PATTERN = /^[\w-]+\/[\w.-]+$/

type FormState = {
  name: string
  repo: string
  branch: string
  image: string
  storage: string
  dotfilesRepo: string
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
    dotfilesRepo: '',
  })
  const [errors, setErrors] = useState<ValidationError>({})
  const [apiError, setApiError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleFieldChange = (field: keyof FormState, value: string) => {
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
      newErrors.repo = 'Repo must look like owner/repository.'
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

    if (formState.dotfilesRepo.trim()) {
      payload.dotfilesRepo = formState.dotfilesRepo.trim()
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
            placeholder="owner/repository"
          />
          {errors.repo && (
            <p className="mt-1 text-xs text-rose-400">{errors.repo}</p>
          )}
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="text-sm font-semibold text-white/80" htmlFor="koolna-branch">
              Branch
            </label>
            <input
              id="koolna-branch"
              value={formState.branch}
              onChange={(event) => handleFieldChange('branch', event.target.value)}
              className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/60 px-4 py-2 text-sm text-white transition focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
            />
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
          <select
            id="koolna-image"
            value={formState.image}
            onChange={(event) => handleFieldChange('image', event.target.value)}
            className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-white transition focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
          >
            {IMAGE_OPTIONS.map((option) => (
              <option key={option} value={option} className="bg-slate-900/70">
                {option}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm font-semibold text-white/80" htmlFor="koolna-dotfiles">
            Dotfiles (optional)
          </label>
          <input
            id="koolna-dotfiles"
            value={formState.dotfilesRepo}
            onChange={(event) => handleFieldChange('dotfilesRepo', event.target.value)}
            className="mt-2 w-full rounded-xl border border-white/10 bg-slate-900/60 px-4 py-2 text-sm text-white transition focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
            placeholder="owner/dotfiles-repo"
          />
        </div>

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
