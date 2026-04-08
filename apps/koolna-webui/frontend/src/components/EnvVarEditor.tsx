import { useRef, useState } from 'react'
import type { EnvVar } from '../api/koolna'

const INPUT_BASE = 'h-11 w-full rounded-xl border px-4 py-2 text-sm text-text transition focus:outline-none focus:ring-1 sm:h-auto'
const INPUT_OK = 'border-border bg-surface focus:border-accent focus:ring-accent'
const INPUT_ERR = 'border-danger/60 bg-danger/5 focus:border-danger focus:ring-danger'
const NAME_PATTERN = /^[A-Z_][A-Z0-9_]*$/

interface Row {
  id: number
  name: string
  value: string
}

interface EnvVarEditorProps {
  vars: EnvVar[]
  onChange: (vars: EnvVar[]) => void
  defaults?: EnvVar[]
}

function toEnvVars(rows: Row[]): EnvVar[] {
  return rows.map((r) => ({ name: r.name, value: r.value }))
}

export function EnvVarEditor({ vars, onChange, defaults }: EnvVarEditorProps) {
  const nextId = useRef(vars.length)
  const [rows, setRows] = useState<Row[]>(() =>
    vars.map((v, i) => ({ id: i, name: v.name, value: v.value }))
  )

  const defaultNames = new Set(defaults?.map((d) => d.name) ?? [])

  const emit = (updated: Row[]) => {
    setRows(updated)
    onChange(toEnvVars(updated))
  }

  const updateRow = (id: number, field: 'name' | 'value', val: string) => {
    emit(rows.map((r) => (r.id === id ? { ...r, [field]: val } : r)))
  }

  const removeRow = (id: number) => {
    emit(rows.filter((r) => r.id !== id))
  }

  const addRow = () => {
    const id = nextId.current++
    emit([...rows, { id, name: '', value: '' }])
  }

  const isNameInvalid = (name: string) => name.length > 0 && !NAME_PATTERN.test(name)

  return (
    <div className="space-y-3">
      {rows.length === 0 ? (
        <p className="text-sm text-text-muted">No environment variables</p>
      ) : (
        rows.map((row) => (
          <div key={row.id} className="flex items-start gap-2">
            <div className="flex-1">
              <div className="flex items-center gap-1">
                <input
                  value={row.name}
                  onChange={(e) => updateRow(row.id, 'name', e.target.value.toUpperCase())}
                  placeholder="VAR_NAME"
                  className={`${INPUT_BASE} ${isNameInvalid(row.name) ? INPUT_ERR : INPUT_OK} font-mono text-xs`}
                />
                {defaultNames.has(row.name) && (
                  <span className="shrink-0 rounded-md bg-accent/20 px-1.5 py-0.5 text-[0.625rem] font-medium text-accent">
                    default
                  </span>
                )}
              </div>
              {isNameInvalid(row.name) && (
                <p className="mt-1 text-xs text-danger">Must match A-Z, 0-9, _ (start with letter or _)</p>
              )}
            </div>
            <div className="flex-1">
              <input
                value={row.value}
                onChange={(e) => updateRow(row.id, 'value', e.target.value)}
                placeholder="value"
                className={`${INPUT_BASE} ${INPUT_OK} font-mono text-xs`}
              />
            </div>
            <button
              type="button"
              onClick={() => removeRow(row.id)}
              className="mt-1 shrink-0 rounded-lg border border-danger/30 bg-danger/10 px-2 py-1.5 text-xs text-danger transition hover:border-danger/60 hover:bg-danger/20"
              title="Remove variable"
            >
              Remove
            </button>
          </div>
        ))
      )}
      <button
        type="button"
        onClick={addRow}
        className="rounded-xl border border-dashed border-border bg-surface px-4 py-2 text-sm text-text-muted transition hover:border-text-muted hover:text-text"
      >
        + Add variable
      </button>
    </div>
  )
}

export default EnvVarEditor
