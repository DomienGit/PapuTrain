/**
 * Helper do rozmów z API.
 * Trzyma token JWT w localStorage (pamięć przeglądarki przetrwająca
 * zamknięcie karty) i dokleja go do każdego zapytania.
 */

const TOKEN_KEY = 'paputrain_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

/**
 * Wywołanie API z nagłówkiem Authorization. Rzuca Error z polskim
 * komunikatem, gdy odpowiedź nie jest OK (np. 401, 500).
 */
export async function api(path, options = {}) {
  const token = getToken()
  const response = await fetch(path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })
  if (response.status === 401) {
    clearToken() // token wygasł/nieprawidłowy — następnym razem ekran logowania
    throw new Error('Sesja wygasła — zaloguj się ponownie')
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || 'Coś poszło nie tak, spróbuj jeszcze raz')
  }
  return response.json()
}
