import { useEffect, useState } from 'react'
import { api } from '../api'
import ErrorToast from './ErrorToast'

/**
 * Włącznik powiadomień push (req 31) — Profil → Parametry.
 * Włączenie: zgoda telefonu → subskrypcja w przeglądarce → zapis na serwerze.
 * Subskrypcja jest per urządzenie: włączasz osobno na każdym telefonie.
 */
export default function PushToggle() {
  // 'loading' | 'unsupported' | 'server-off' | 'denied' | 'off' | 'on'
  const [state, setState] = useState('loading')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')

  useEffect(() => {
    async function check() {
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        return setState('unsupported')
      }
      const { public_key } = await api('/api/push/public-key')
      if (!public_key) return setState('server-off')
      if (Notification.permission === 'denied') return setState('denied')
      const registration = await navigator.serviceWorker.ready
      const subscription = await registration.pushManager.getSubscription()
      setState(subscription ? 'on' : 'off')
    }
    check().catch((err) => {
      setError(err.message)
      setState('unsupported')
    })
  }, [])

  async function enable() {
    setBusy(true)
    setError('')
    setInfo('')
    try {
      // Pytanie o zgodę MUSI wyjść z kliknięcia — telefony ignorują je inaczej.
      const permission = await Notification.requestPermission()
      if (permission !== 'granted') {
        setState(permission === 'denied' ? 'denied' : 'off')
        return
      }
      const { public_key } = await api('/api/push/public-key')
      const registration = await navigator.serviceWorker.ready
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true, // wymóg Chrome: każdy push kończy się widocznym powiadomieniem
        applicationServerKey: base64UrlToBytes(public_key),
      })
      await api('/api/push/subscriptions', {
        method: 'POST',
        body: JSON.stringify(subscription.toJSON()),
      })
      setState('on')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function disable() {
    setBusy(true)
    setError('')
    setInfo('')
    try {
      const registration = await navigator.serviceWorker.ready
      const subscription = await registration.pushManager.getSubscription()
      if (subscription) {
        await api('/api/push/subscriptions', {
          method: 'DELETE',
          body: JSON.stringify({ endpoint: subscription.endpoint }),
        })
        await subscription.unsubscribe()
      }
      setState('off')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function sendTest() {
    setBusy(true)
    setError('')
    setInfo('')
    try {
      const { delay_s } = await api('/api/push/test', { method: 'POST' })
      // Przy otwartej aplikacji powiadomienie się nie pokazuje — stąd opóźnienie.
      setInfo(`Zamknij aplikację — powiadomienie przyjdzie za ${delay_s} s.`)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const messages = {
    loading: 'Sprawdzam…',
    unsupported: 'Ta przeglądarka nie obsługuje powiadomień. Na Androidzie użyj Chrome.',
    'server-off': 'Powiadomienia są wyłączone na serwerze (brak kluczy VAPID).',
    denied:
      'Powiadomienia są zablokowane. Odblokuj je dla PapuTrain w ustawieniach telefonu (Aplikacje → PapuTrain → Powiadomienia) albo w Chrome (kłódka przy adresie → Uprawnienia) i wróć tutaj.',
    off: 'Dostaniesz powiadomienie, gdy AI skończy układać plan — także przy zamkniętej aplikacji.',
    on: 'Włączone na tym urządzeniu.',
  }

  const buttonClass =
    'rounded-lg px-3 py-2 text-sm font-medium disabled:opacity-50'

  return (
    <div className="mt-6 rounded-2xl bg-white p-4 shadow-sm">
      <h2 className="font-semibold text-zinc-900">Powiadomienia</h2>
      <p className="mt-1 text-sm text-zinc-600">{messages[state]}</p>
      {info && <p className="mt-2 text-sm text-emerald-700">{info}</p>}

      {state === 'off' && (
        <button
          onClick={enable}
          disabled={busy}
          className={`${buttonClass} mt-3 w-full bg-zinc-900 text-white hover:bg-zinc-700`}
        >
          {busy ? 'Włączam…' : 'Włącz powiadomienia'}
        </button>
      )}
      {state === 'on' && (
        <div className="mt-3 flex gap-2">
          <button
            onClick={sendTest}
            disabled={busy}
            className={`${buttonClass} flex-1 bg-zinc-900 text-white hover:bg-zinc-700`}
          >
            Wyślij testowe
          </button>
          <button
            onClick={disable}
            disabled={busy}
            className={`${buttonClass} flex-1 bg-zinc-100 text-zinc-700 hover:bg-zinc-200`}
          >
            Wyłącz
          </button>
        </div>
      )}
      <ErrorToast message={error} onClose={() => setError('')} />
    </div>
  )
}

// Klucz VAPID przychodzi jako base64url (tekst), a przeglądarka chce bajtów.
function base64UrlToBytes(base64Url) {
  const base64 = (base64Url + '='.repeat((4 - (base64Url.length % 4)) % 4))
    .replace(/-/g, '+')
    .replace(/_/g, '/')
  return Uint8Array.from(atob(base64), (char) => char.charCodeAt(0))
}
