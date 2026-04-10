import { BrowserRouter, Route, Routes, useNavigate, useParams } from 'react-router-dom'
import KoolnaCreate from './components/KoolnaCreate'
import KoolnaList from './components/KoolnaList'
import Settings from './components/Settings'
import { Terminal } from './components/Terminal'
import './App.css'

const layoutWrapper = 'min-h-screen bg-bg px-4 py-8'
const contentWrapper = 'mx-auto flex max-w-5xl flex-col gap-6'

const CogwheelIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
    <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z" />
  </svg>
)

const HomePage = () => {
  const navigate = useNavigate()

  return (
    <main className={layoutWrapper}>
      <div className={`${contentWrapper} relative`}>
        <button
          type="button"
          className="absolute right-0 top-0 flex h-10 w-10 items-center justify-center rounded-xl text-text-muted transition hover:text-accent"
          onClick={() => navigate('/settings')}
          title="Settings"
          aria-label="Settings"
        >
          <CogwheelIcon />
        </button>
        <header className="rounded-2xl border border-border bg-surface px-6 py-5 shadow-lg shadow-black/40">
          <p className="text-sm uppercase tracking-wide text-accent">Koolna</p>
          <h1 className="text-3xl font-semibold text-text">Environment library</h1>
          <p className="text-sm text-text-muted">Manage live Koolna sessions from one console.</p>
        </header>
        <KoolnaList
          onCreate={() => navigate('/create')}
          onTerminal={(name, session) => { window.open(`/terminal/${name}/${session}`, '_blank', 'noopener'); }}
        />
      </div>
    </main>
  )
}

const CreatePage = () => {
  const navigate = useNavigate()

  return (
    <main className={layoutWrapper}>
      <div className={contentWrapper}>
        <header className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-border bg-surface px-6 py-5 shadow-lg shadow-black/40">
          <div>
            <p className="text-sm uppercase tracking-wide text-accent">Create</p>
            <h1 className="text-3xl font-semibold text-text">Provision a Koolna</h1>
          </div>
          <button
            type="button"
            className="rounded-2xl border border-border bg-surface-raised px-5 py-2 text-sm font-semibold text-text transition hover:border-text-muted"
            onClick={() => navigate(-1)}
          >
            Back
          </button>
        </header>
        <KoolnaCreate onCreated={() => navigate('/')} onCancel={() => navigate(-1)} />
      </div>
    </main>
  )
}

const SettingsPage = () => {
  const navigate = useNavigate()

  return (
    <main className={layoutWrapper}>
      <div className={contentWrapper}>
        <header className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-border bg-surface px-6 py-5 shadow-lg shadow-black/40">
          <div>
            <p className="text-sm uppercase tracking-wide text-accent">Settings</p>
            <h1 className="text-3xl font-semibold text-text">Koolna defaults</h1>
          </div>
          <button
            type="button"
            className="rounded-2xl border border-border bg-surface-raised px-5 py-2 text-sm font-semibold text-text transition hover:border-text-muted"
            onClick={() => navigate(-1)}
          >
            Back
          </button>
        </header>
        <Settings />
      </div>
    </main>
  )
}

const TerminalPage = () => {
  const { name, session } = useParams<{ name: string; session: string }>()

  if (!name || !session) {
    return (
      <main className={layoutWrapper}>
        <div className={contentWrapper}>
          <div className="rounded-2xl border border-border bg-surface px-6 py-5 text-sm text-text-muted">
            Missing terminal parameters.
          </div>
        </div>
      </main>
    )
  }

  return (
    <Terminal name={name} session={session} />
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/create" element={<CreatePage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/terminal/:name/:session" element={<TerminalPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
