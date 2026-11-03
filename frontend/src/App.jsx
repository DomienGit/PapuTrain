import { useEffect, useState } from 'react'
import { api, clearToken, getToken, setToken } from './api'

const inputClass =
  'w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-base ' +
  'outline-none focus:border-zinc-900'

function LoginScreen({ onLoggedIn }) {
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault() // formularz ma nie przeładowywać strony
    setBusy(true)
    setError('')
    const form = new FormData(event.target)
    try {
      const data = await api('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          username: form.get('username'),
          password: form.get('password'),
        }),
      })
      setToken(data.access_token)
      const me = await api('/api/auth/me') // potwierdzenie, że token działa
      onLoggedIn(me.username)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-dvh items-center justify-center bg-zinc-100 px-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-sm"
      >
        <h1 className="mb-1 text-2xl font-bold text-zinc-900">PapuTrain</h1>
        <p className="mb-6 text-sm text-zinc-500">Zaloguj się, żeby grzebać w planach</p>

        <label className="mb-1 block text-sm font-medium text-zinc-700" htmlFor="username">
          Login
        </label>
        <input
          id="username"
          name="username"
          autoComplete="username"
          required
          className={inputClass}
        />

        <label className="mt-4 mb-1 block text-sm font-medium text-zinc-700" htmlFor="password">
          Hasło
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          className={inputClass}
        />

        {error && (
          <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={busy}
          className="mt-6 w-full rounded-lg bg-zinc-900 py-2.5 text-white transition-colors hover:bg-zinc-700 disabled:opacity-50"
        >
          {busy ? 'Loguję…' : 'Zaloguj się'}
        </button>
      </form>
    </div>
  )
}

function HomeScreen({ username, onLogout }) {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center bg-zinc-100 px-4">
      <div className="w-full max-w-sm rounded-2xl bg-white p-6 text-center shadow-sm">
        <h1 className="text-2xl font-bold text-zinc-900">PapuTrain</h1>
        <p className="mt-2 text-zinc-600">
          Cześć, <span className="font-semibold">{username}</span>!
        </p>
        <p className="mt-4 text-sm text-zinc-500">
          Tu stanie główny ekran aplikacji — onboarding i plany (kolejne etapy).
        </p>
        <button
          onClick={onLogout}
          className="mt-6 rounded-lg border border-zinc-300 px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-100"
        >
          Wyloguj się
        </button>
      </div>
    </div>
  )
}

export default function App() {
  const [username, setUsername] = useState(null)
  const [checking, setChecking] = useState(Boolean(getToken()))

  // Po wczytaniu strony: mamy zapisany token? Zapytaj API, czy nadal ważny.
  useEffect(() => {
    if (!getToken()) return
    api('/api/auth/me')
      .then((data) => setUsername(data.username))
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

  return username ? (
    <HomeScreen username={username} onLogout={() => { clearToken(); setUsername(null) }} />
  ) : (
    <LoginScreen onLoggedIn={setUsername} />
  )
}
