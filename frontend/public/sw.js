/*
 * Service worker PapuTrain — WYŁĄCZNIE powiadomienia push (req 31).
 * Celowo bez obsługi "fetch" i bez cache plików: aplikacja zawsze ładuje się
 * z serwera, więc po deployu telefon od razu dostaje nową wersję.
 */

self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()))

self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {}
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windows) => {
      // Aplikacja otwarta na ekranie → wynik widać od razu, powiadomienie zbędne.
      if (windows.some((w) => w.visibilityState === 'visible')) return
      return self.registration.showNotification(data.title || 'PapuTrain', {
        body: data.body || '',
        icon: '/icons/icon-192.png',
        tag: 'paputrain', // nowe powiadomienie zastępuje poprzednie zamiast się mnożyć
        data: { url: data.url || '/' },
      })
    }),
  )
})

// Kliknięcie w powiadomienie: przełącz na otwartą aplikację albo ją otwórz.
self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const url = event.notification.data?.url || '/'
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windows) => {
      const existing = windows[0]
      if (existing) return existing.focus()
      return self.clients.openWindow(url)
    }),
  )
})
