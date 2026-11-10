import { useEffect, useState } from 'react'
import { api, getToken } from './api'
import StopWatch, { formatTime } from './components/Stopwatch'
import EquipmentExercises from './pages/EquipmentExercises'
import Home from './pages/Home'
import Login from './pages/Login'
import Onboarding from './pages/Onboarding'

/**
 * Rdzeń aplikacji: pilnuje sesji (token), przełącza ekrany (stan, bez routera)
 * i trzyma stan stopera — dzięki temu czas leci niezależnie od zakładek.
 */
export default function App() {
  const [username, setUsername] = useState(null)
  const [checking, setChecking] = useState(Boolean(getToken()))
  const [needsOnboarding, setNeedsOnboarding] = useState(false)
  const [tab, setTab] = useState('trening') // 'trening' | 'stoper' | 'profil' (req 26)

  // Stoper (Etap 7): baseMs = zebrany czas z poprzednich "kolejek",
  // startedAt = moment ostatniego startu. Wyświetlany czas to suma.
  const [stopwatch, setStopwatch] = useState({ running: false, baseMs: 0, startedAt: null })
  const [, setTick] = useState(0) // sekundowy "tik" wymusza przerysowanie zegara

  function startStopwatch() {
    setStopwatch((s) =>
      s.running ? s : { running: true, baseMs: s.baseMs, startedAt: Date.now() },
    )
  }

  function stopStopwatch() {
    setStopwatch((s) => ({
      running: false,
      baseMs: s.baseMs + (s.running ? Date.now() - s.startedAt : 0),
      startedAt: null,
    }))
  }

  function resetStopwatch() {
    setStopwatch({ running: false, baseMs: 0, startedAt: null })
  }

  useEffect(() => {
    if (!stopwatch.running) return
    const interval = setInterval(() => setTick((t) => t + 1), 1000)
    return () => clearInterval(interval)
  }, [stopwatch.running])

  const elapsedMs = stopwatch.baseMs + (stopwatch.running ? Date.now() - stopwatch.startedAt : 0)

  // Sprawdzenie profilu decyduje o pokazaniu kreatora pierwszego uruchomienia.
  function checkProfile() {
    return api('/api/profile').then((profile) => setNeedsOnboarding(profile === null))
  }

  // Po wejściu na stronę: sprawdzamy token (o ile jest), a potem profil.
  // Brak profilu => kreator pierwszego uruchomienia (PLAN.md: onboarding).
  useEffect(() => {
    if (!getToken()) return
    api('/api/auth/me')
      .then((me) => {
        setUsername(me.username)
        return checkProfile()
      })
      .catch(() => {}) // api() sam wyczyścił nieaktualny token
      .finally(() => setChecking(false))
  }, [])

  if (checking) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-zinc-100 text-zinc-500">
        Sprawdzam sesję…
      </div>
    )
  }

  if (!username)
    return (
      <Login
        onLoggedIn={(name) => {
          setUsername(name)
          checkProfile().catch(() => {})
        }}
      />
    )
  if (needsOnboarding) return <Onboarding onDone={() => setNeedsOnboarding(false)} />

  return (
    <div className="min-h-dvh bg-zinc-100 pb-20">
      {tab === 'trening' && <Home username={username} />}
      {tab === 'profil' && <EquipmentExercises />}
      {tab === 'stoper' && (
        <StopWatch
          elapsedMs={elapsedMs}
          running={stopwatch.running}
          onStart={startStopwatch}
          onStop={stopStopwatch}
          onReset={resetStopwatch}
        />
      )}

      {/* Pływający pasek stopera — widoczny na każdej zakładce podczas treningu
          (PLAN.md req 20). Klik otwiera pełny zegar. */}
      {elapsedMs > 0 && (
        <button
          onClick={() => setTab('stoper')}
          className="fixed inset-x-4 bottom-16 z-10 mx-auto flex max-w-md items-center justify-center gap-2 rounded-full bg-zinc-900 px-4 py-2 text-sm font-medium text-white shadow-lg"
        >
          <span className={`size-2 rounded-full ${stopwatch.running ? 'animate-pulse bg-emerald-400' : 'bg-zinc-500'}`} />
          {formatTime(elapsedMs)}
          <span className="text-zinc-400">{stopwatch.running ? 'stoper leci' : 'zatrzymany'}</span>
        </button>
      )}

      <nav className="fixed inset-x-0 bottom-0 flex border-t border-zinc-200 bg-white">
        <NavItem active={tab === 'trening'} label="Trening" onClick={() => setTab('trening')} />
        <NavItem active={tab === 'stoper'} label="Stoper" onClick={() => setTab('stoper')} />
        <NavItem active={tab === 'profil'} label="Profil" onClick={() => setTab('profil')} />
      </nav>
    </div>
  )
}

function NavItem({ active, label, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 py-3 text-center text-sm font-medium transition-colors ${
        active ? 'text-zinc-900' : 'text-zinc-400 hover:text-zinc-600'
      }`}
    >
      {label}
    </button>
  )
}
