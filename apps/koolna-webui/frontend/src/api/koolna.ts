export type KoolnaPhase = 'Running' | 'Pending' | 'Suspended' | 'Failed'

export interface Koolna {
  name: string
  repo: string
  branch: string
  phase: KoolnaPhase
  ip?: string
  suspended: boolean
  sshPublicKey?: string
}

export type DotfilesMethod = 'none' | 'bare-git' | 'clone' | 'command'

export interface CreateKoolnaRequest {
  name: string
  repo: string
  branch?: string
  dotfilesRepo?: string
  dotfilesMethod?: DotfilesMethod
  dotfilesBareDir?: string
  dotfilesCommand?: string
  initCommand?: string
  shell?: string
  image?: string
  storage?: string | number
  username?: string
  uid?: number
  homePath?: string
  gitUsername?: string
  gitToken?: string
  gitName?: string
  gitEmail?: string
  sshPublicKey?: string
}

export interface DotfilesDefaults {
  dotfilesRepo?: string
  dotfilesMethod?: DotfilesMethod
  dotfilesBareDir?: string
  dotfilesCommand?: string
  initCommand?: string
  defaultBranch?: string
  sshPublicKey?: string
}

const API_BASE = '/api/koolnas'

async function parseResponse<T>(response: Response): Promise<T> {
  const text = await response.text()
  if (!response.ok) {
    let detail = text || response.statusText
    try {
      const body = text ? JSON.parse(text) : null
      if (body && typeof body === 'object') {
        const record = body as Record<string, unknown>
        detail = typeof record.error === 'string'
          ? record.error
          : typeof record.detail === 'string'
            ? record.detail
            : typeof record.message === 'string'
              ? record.message
              : JSON.stringify(record)
      }
    } catch {
      detail = text || response.statusText
    }
    throw new Error(`Request failed (${response.status}): ${detail}`)
  }

  if (!text) {
    return undefined as unknown as T
  }

  try {
    return JSON.parse(text) as T
  } catch (err) {
    throw new Error(`Unable to parse JSON response: ${(err as Error).message}`)
  }
}

function jsonHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
  }
}

function koolnaUrl(name?: string, suffix?: string): string {
  const base = name ? `${API_BASE}/${encodeURIComponent(name)}` : API_BASE
  return suffix ? `${base}/${suffix}` : base
}

export async function getDefaults(): Promise<DotfilesDefaults> {
  const response = await fetch('/api/defaults')
  return parseResponse<DotfilesDefaults>(response)
}

export async function updateDefaults(defaults: DotfilesDefaults): Promise<DotfilesDefaults> {
  const response = await fetch('/api/defaults', {
    method: 'PUT',
    headers: jsonHeaders(),
    body: JSON.stringify(defaults),
  })
  return parseResponse<DotfilesDefaults>(response)
}

export async function listBranches(repo: string, secret?: string): Promise<string[]> {
  const params = new URLSearchParams({ repo })
  if (secret) params.set('secret', secret)
  const response = await fetch(`/api/branches?${params}`)
  return parseResponse<string[]>(response)
}

export async function listKoolnas(): Promise<Koolna[]> {
  const response = await fetch(API_BASE)
  return parseResponse<Koolna[]>(response)
}

export async function getKoolna(name: string): Promise<Koolna> {
  const response = await fetch(koolnaUrl(name))
  return parseResponse<Koolna>(response)
}

export async function createKoolna(req: CreateKoolnaRequest): Promise<Koolna> {
  const response = await fetch(API_BASE, {
    method: 'POST',
    headers: jsonHeaders(),
    body: JSON.stringify(req),
  })
  return parseResponse<Koolna>(response)
}

export async function deleteKoolna(name: string): Promise<void> {
  const response = await fetch(koolnaUrl(name), {
    method: 'DELETE',
  })
  await parseResponse<void>(response)
}

export async function pauseKoolna(name: string): Promise<void> {
  const response = await fetch(koolnaUrl(name, 'pause'), {
    method: 'POST',
  })
  await parseResponse<void>(response)
}

export async function resumeKoolna(name: string): Promise<void> {
  const response = await fetch(koolnaUrl(name, 'resume'), {
    method: 'POST',
  })
  await parseResponse<void>(response)
}

export async function checkoutBranch(
  name: string,
  branch: string,
): Promise<{ branch: string; output: string }> {
  const response = await fetch(koolnaUrl(name, 'checkout'), {
    method: 'POST',
    headers: jsonHeaders(),
    body: JSON.stringify({ branch }),
  })
  return parseResponse<{ branch: string; output: string }>(response)
}

export function mountScriptUrl(name: string): string {
  return koolnaUrl(name, 'mount-script')
}

export async function getBranch(
  name: string,
): Promise<{ branch: string }> {
  const response = await fetch(koolnaUrl(name, 'branch'))
  return parseResponse<{ branch: string }>(response)
}
