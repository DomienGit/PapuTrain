import { useEffect, useState } from 'react'
import { api, clearToken, getToken } from './api'
import EquipmentExercises from './pages/EquipmentExercises'
import Home from './pages/Home'
import Login from './pages/Login'
import Onboarding from './pages/Onboarding'

/**
 * Rdzeń aplikacji: pilnuje sesji (token) i przełącza ekrany.
 * Router jest niepotrzebny — kilka widoków obsłużymy stanem (tab).
 */
export default function App() {
  const [username, setUsername] = useState(null)
  const [checking, setChecking] = useState(Boolean(getToken()))
  const [needsOnboarding, setNeedsOnboarding] = useState(false)
  const [tab, setTab] = useState('home') // 'home' | 'equipment'

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

  function handleLogout() {
    clearToken()
    setUsername(null)
    setNeedsOnboarding(false)
    setTab('home')
  }

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
      {tab === 'home' ? <Home username={username} /> : <EquipmentExercises />}

      <nav className="fixed inset-x-0 bottom-0 flex border-t border-zinc-200 bg-white">
        <NavItem active={tab === 'home'} label="Główny" onClick={() => setTab('home')} />
        <NavItem
          active={tab === 'equipment'}
          label="Sprzęt i ćwiczenia"
          onClick={() => setTab('equipment')}
        />
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
