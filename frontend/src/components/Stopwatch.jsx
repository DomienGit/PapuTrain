/**
 * Zakładka "Stoper" (Etap 7, PLAN.md req 20): duży zegar start/stop/reset.
 * Czas włączam RAZ na początku treningu — leci dalej, nawet gdy chodzę
 * po innych zakładkach (stan siedzi w App.jsx, nie tu). Przerwy z planu
 * czytam sam z tego zegara — żadnych timerów odliczających.
 */

// MM:SS, po godzinie H:MM:SS. Używa też pływający pasek w App.jsx.
export function formatTime(ms) {
  const total = Math.floor(ms / 1000)
  const s = String(total % 60).padStart(2, '0')
  const m = String(Math.floor(total / 60) % 60).padStart(2, '0')
  const h = Math.floor(total / 3600)
  return h > 0 ? `${h}:${m}:${s}` : `${m}:${s}`
}

export default function StopWatch({ elapsedMs, running, onStart, onStop, onReset }) {
  return (
    <div className="mx-auto flex w-full max-w-md flex-col items-center px-4 py-10">
      <h1 className="text-xl font-bold text-zinc-900">Stoper</h1>

      <p
        className={`mt-10 font-mono text-6xl font-bold tabular-nums ${
          running ? 'text-zinc-900' : 'text-zinc-400'
        }`}
      >
        {formatTime(elapsedMs)}
      </p>
      <p className="mt-2 text-sm text-zinc-500">
        {running ? 'czas leci…' : elapsedMs > 0 ? 'zatrzymany' : 'gotowy'}
      </p>

      <div className="mt-10 flex w-full gap-2">
        {running ? (
          <button
            onClick={onStop}
            className="flex-1 rounded-xl bg-red-600 py-4 text-lg font-semibold text-white hover:bg-red-500"
          >
            Stop
          </button>
        ) : (
          <button
            onClick={onStart}
            className="flex-1 rounded-xl bg-emerald-600 py-4 text-lg font-semibold text-white hover:bg-emerald-500"
          >
            Start
          </button>
        )}
        <button
          onClick={onReset}
          disabled={elapsedMs === 0}
          className="rounded-xl bg-white px-6 py-4 text-lg font-semibold text-zinc-700 shadow-sm hover:bg-zinc-50 disabled:opacity-50"
        >
          Reset
        </button>
      </div>

      <p className="mt-8 text-center text-xs text-zinc-400">
        Włącz raz na początku treningu — czas leci cały czas, także po wyjściu z tej zakładki.
        Przerwy między seriami czytaj z zegara; wartości z planu są tylko informacją.
      </p>
    </div>
  )
}
