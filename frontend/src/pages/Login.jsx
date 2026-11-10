import { useState } from 'react'
import { api, setToken } from '../api'

/**
 * Ekran logowania (PLAN.md: ekran 1). Dwa tryby (req 27):
 * - "login": login + hasło. Konto utworzone BEZ hasła dostaje z backendu
 *   {"setup_required": true} — przechodzimy do trybu "setup".
 * - "setup": ustawienie pierwszego hasła (hasło + powtórzenie). Po sukcesie
 *   backend od razu loguje (zwraca token).
 */
export default function Login({ onLoggedIn }) {
  const [mode, setMode] = useState('login') // 'login' | 'setup'
  const [username, setUsername] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function finishLogin(token) {
    setToken(token)
    const me = await api('/api/auth/me') // potwierdzenie, że token działa
    onLoggedIn(me.username)
  }

  async function handleLogin(event) {
    event.preventDefault() // formularz ma nie przeładowywać strony
    setBusy(true)
    setError('')
    const form = new FormData(event.target)
    const name = form.get('username')?.toString() ?? ''
    try {
      const data = await api('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          username: name,
          password: form.get('password')?.toString() ?? '',
        }),
      })
      if (data.setup_required) {
        // Konto bez hasła (req 27): pokazujemy ekran ustawiania hasła.
        setUsername(name)
        setMode('setup')
        return
      }
      await finishLogin(data.access_token)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleSetup(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    const form = new FormData(event.target)
    const password = form.get('password')?.toString() ?? ''
    const repeat = form.get('repeat')?.toString() ?? ''
    if (password !== repeat) {
      setError('Hasła nie są identyczne.')
      setBusy(false)
      return
    }
    try {
      const data = await api('/api/auth/set-password', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      })
      await finishLogin(data.access_token)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const inputClass =
    'w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-base outline-none focus:border-zinc-900'

  return (
    <div className="flex min-h-dvh items-center justify-center bg-zinc-100 px-4">
      {mode === 'login' ? (
        <form
          onSubmit={handleLogin}
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
      ) : (
        <form
          onSubmit={handleSetup}
          className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-sm"
        >
          <h1 className="mb-1 text-2xl font-bold text-zinc-900">Ustaw hasło</h1>
          <p className="mb-6 text-sm text-zinc-500">
            Konto <span className="font-medium text-zinc-700">{username}</span> nie ma
            jeszcze hasła. Ustaw je (min. 8 znaków) — posłuży do kolejnych logowań.
          </p>

          <label className="mb-1 block text-sm font-medium text-zinc-700" htmlFor="new-password">
            Nowe hasło
          </label>
          <input
            id="new-password"
            name="password"
            type="password"
            autoComplete="new-password"
            minLength={8}
            required
            className={inputClass}
          />

          <label className="mt-4 mb-1 block text-sm font-medium text-zinc-700" htmlFor="repeat-password">
            Powtórz hasło
          </label>
          <input
            id="repeat-password"
            name="repeat"
            type="password"
            autoComplete="new-password"
            minLength={8}
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
            {busy ? 'Zapisuję…' : 'Zapisz hasło i zaloguj'}
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('login')
              setError('')
            }}
            className="mt-3 w-full text-sm text-zinc-500 underline-offset-2 hover:text-zinc-700 hover:underline"
          >
            ← Wróć do logowania
          </button>
        </form>
      )}
    </div>
  )
}
