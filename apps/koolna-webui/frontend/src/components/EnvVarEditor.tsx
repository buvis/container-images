import { useState } from 'react'
import type { EnvVar } from '../api/koolna'

const INPUT_BASE = 'w-full rounded-xl border px-4 py-2 text-sm text-white transition focus:outline-none focus:ring-1'
const INPUT_OK = 'border-white/10 bg-slate-900/60 focus:border-sky-400 focus:ring-sky-400'
const INPUT_ERR = 'border-rose-500/60 bg-rose-500/5 focus:border-rose-400 focus:ring-rose-400'
const NAME_PATTERN = /^[A-Z_][A-Z0-9_]*$/

interface EnvVarEditorProps {
  vars: EnvVar[]
  onChange: (vars: EnvVar[]) => void
  defaults?: EnvVar[]
}

export function EnvVarEditor({ vars, onChange, defaults }: EnvVarEditorProps) {
  const [showValues, setShowValues] = useState<Record<number, boolean>>({})

  const defaultNames = new Set(defaults?.map((d) => d.name) ?? [])

  const updateVar = (index: number, field: 'name' | 'value', val: string) => {
    const updated = [...vars]
    updated[index] = { ...updated[index], [field]: val }
    onChange(updated)
  }

  const removeVar = (index: number) => {
    onChange(vars.filter((_, i) => i !== index))
    setShowValues((prev) => {
      const next = { ...prev }
      delete next[index]
      return next
    })
  }

  const addVar = () => {
    onChange([...vars, { name: '', value: '' }])
  }

  const toggleShow = (index: number) => {
    setShowValues((prev) => ({ ...prev, [index]: !prev[index] }))
  }

  const isNameInvalid = (name: string) => name.length > 0 && !NAME_PATTERN.test(name)

  return (
    <div className="space-y-3">
      {vars.length === 0 ? (
        <p className="text-sm text-white/40">No environment variables</p>
      ) : (
        vars.map((v, i) => (
          <div key={i} className="flex items-start gap-2">
            <div className="flex-1">
              <div className="flex items-center gap-1">
                <input
                  value={v.name}
                  onChange={(e) => updateVar(i, 'name', e.target.value.toUpperCase())}
                  placeholder="VAR_NAME"
                  className={`${INPUT_BASE} ${isNameInvalid(v.name) ? INPUT_ERR : INPUT_OK} font-mono text-xs`}
                />
                {defaultNames.has(v.name) && (
                  <span className="shrink-0 rounded-md bg-sky-500/20 px-1.5 py-0.5 text-[0.625rem] font-medium text-sky-300">
                    default
                  </span>
                )}
              </div>
              {isNameInvalid(v.name) && (
                <p className="mt-1 text-xs text-rose-400">Must match A-Z, 0-9, _ (start with letter or _)</p>
              )}
            </div>
            <div className="flex-1">
              <input
                type={showValues[i] ? 'text' : 'password'}
                value={v.value}
                onChange={(e) => updateVar(i, 'value', e.target.value)}
                placeholder="value"
                className={`${INPUT_BASE} ${INPUT_OK} font-mono text-xs`}
              />
            </div>
            <button
              type="button"
              onClick={() => toggleShow(i)}
              className="mt-1 shrink-0 rounded-lg border border-white/10 bg-white/5 px-2 py-1.5 text-xs text-white/60 transition hover:border-white/30 hover:text-white"
              title={showValues[i] ? 'Hide value' : 'Show value'}
            >
              {showValues[i] ? 'Hide' : 'Show'}
            </button>
            <button
              type="button"
              onClick={() => removeVar(i)}
              className="mt-1 shrink-0 rounded-lg border border-rose-500/30 bg-rose-500/10 px-2 py-1.5 text-xs text-rose-300 transition hover:border-rose-500/60 hover:bg-rose-500/20"
              title="Remove variable"
            >
              Remove
            </button>
          </div>
        ))
      )}
      <button
        type="button"
        onClick={addVar}
        className="rounded-xl border border-dashed border-white/20 bg-white/5 px-4 py-2 text-sm text-white/60 transition hover:border-white/40 hover:text-white"
      >
        + Add variable
      </button>
    </div>
  )
}

export default EnvVarEditor
