import { BrowserRouter, Route, Routes, useNavigate, useParams } from 'react-router-dom'
import KoolnaCreate from './components/KoolnaCreate'
import KoolnaList from './components/KoolnaList'
import { Terminal } from './components/Terminal'
import './App.css'

const layoutWrapper = 'min-h-screen bg-slate-950 px-4 py-8'
const contentWrapper = 'mx-auto flex max-w-5xl flex-col gap-6'

const HomePage = () => {
  const navigate = useNavigate()

  return (
    <main className={`${layoutWrapper}`}>
      <div className={`${contentWrapper}`}>
        <header className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-white/10 bg-slate-950/70 px-6 py-5 shadow-lg shadow-black/40">
          <div>
            <p className="text-sm uppercase tracking-wide text-sky-500">Koolna</p>
            <h1 className="text-3xl font-semibold text-white">Environment library</h1>
            <p className="text-sm text-white/60">Manage live Koolna sessions from one console.</p>
          </div>
          <button
            type="button"
            className="rounded-2xl border border-transparent bg-sky-500 px-5 py-2 text-sm font-semibold text-white transition hover:bg-sky-400"
            onClick={() => navigate('/create')}
          >
            New Koolna
          </button>
        </header>
        <KoolnaList onTerminal={(name, session) => navigate(`/terminal/${name}/${session}`)} />
      </div>
    </main>
  )
}

const CreatePage = () => {
  const navigate = useNavigate()

  return (
    <main className={`${layoutWrapper}`}>
      <div className={`${contentWrapper}`}>
        <header className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-white/10 bg-slate-950/70 px-6 py-5 shadow-lg shadow-black/40">
          <div>
            <p className="text-sm uppercase tracking-wide text-sky-500">Create</p>
            <h1 className="text-3xl font-semibold text-white">Provision a Koolna</h1>
          </div>
          <button
            type="button"
            className="rounded-2xl border border-white/10 bg-white/5 px-5 py-2 text-sm font-semibold text-white transition hover:border-white/40"
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

const TerminalPage = () => {
  const { name, session } = useParams<{ name: string; session: string }>()
  const navigate = useNavigate()

  if (!name || !session) {
    return (
      <main className={`${layoutWrapper}`}>
        <div className={`${contentWrapper}`}>
          <div className="rounded-2xl border border-white/10 bg-slate-950/70 px-6 py-5 text-sm text-white/60">
            Missing terminal parameters.
          </div>
        </div>
      </main>
    )
  }

  return (
    <Terminal name={name} session={session} onBack={() => navigate('/')} />
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/create" element={<CreatePage />} />
        <Route path="/terminal/:name/:session" element={<TerminalPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
