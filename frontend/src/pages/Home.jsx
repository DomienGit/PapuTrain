import { useEffect, useState } from 'react'
import { api } from '../api'

/**
 * Ekran główny. Etap 5: pokazuje aktywny plan albo szkic wygenerowany przez AI
 * (z przyciskiem "Generuj plan"). Panel zatwierdzania i edycji szkicu — Etap 6.
 */
export default function Home({ username }) {
  const [plan, setPlan] = useState(null) // null = brak planu; {status, workouts...}
  const [loaded, setLoaded] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    // Najpierw aktywny plan, potem szkic — 404 oznacza "nie ma", to nie błąd.
    api('/api/plans/active')
      .then(setPlan)
      .catch(() =>
        api('/api/plans/draft')
          .then(setPlan)
          .catch(() => {})
          .finally(() => setLoaded(true)),
      )
      .finally(() => setLoaded(true))
  }, [])

  async function generate() {
    setBusy(true)
    setError('')
    try {
      const draft = await api('/api/plans/generate', { method: 'POST' })
      setPlan(draft)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto w-full max-w-md px-4 py-6">
      <h1 className="text-xl font-bold text-zinc-900">PapuTrain</h1>
      <p className="mt-0.5 text-sm text-zinc-500">Cześć, {username}!</p>

      {error && (
        <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
      )}

      {plan ? (
        <PlanView plan={plan} />
      ) : loaded ? (
        <div className="mt-6 rounded-2xl bg-white p-5 text-center shadow-sm">
          <p className="text-sm text-zinc-500">
            Nie masz jeszcze planu na ten tydzień. AI ułoży go z Twojego profilu i sprzętu.
          </p>
          <button
            onClick={generate}
            disabled={busy}
            className="mt-4 w-full rounded-lg bg-zinc-900 py-2.5 font-medium text-white hover:bg-zinc-700 disabled:opacity-50"
          >
            {busy ? 'AI układa plan… (może chwilę potrwać)' : 'Generuj plan na ten tydzień'}
          </button>
        </div>
      ) : (
        <p className="mt-6 text-center text-sm text-zinc-500">Ładowanie…</p>
      )}
    </div>
  )
}

function PlanView({ plan }) {
  const isDraft = plan.status === 'draft'
  return (
    <div className="mt-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-zinc-900">
          {plan.week_title || `Tydzień ${plan.week_number}`}
        </h2>
        {isDraft && (
          <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-700">
            szkic
          </span>
        )}
      </div>

      {plan.coach_note && (
        <p className="mt-2 rounded-xl bg-white p-3 text-sm text-zinc-600 shadow-sm">
          <span className="font-medium">Trener: </span>
          {plan.coach_note}
        </p>
      )}

      <div className="mt-3 space-y-4">
        {plan.workouts.map((workout) => (
          <section key={workout.id} className="rounded-xl bg-white p-4 shadow-sm">
            <h3 className="font-semibold text-zinc-900">
              {workout.name}
              {workout.rest_between_exercises_s != null && (
                <span className="ml-2 text-xs font-normal text-zinc-500">
                  przerwa między ćwiczeniami: {workout.rest_between_exercises_s} s
                </span>
              )}
            </h3>
            <ul className="mt-3 divide-y divide-zinc-100">
              {workout.exercises.map((exercise) => (
                <li key={exercise.id} className="py-2">
                  <div className="flex justify-between gap-2">
                    <span className="text-zinc-900">{exercise.name}</span>
                    <span className="shrink-0 text-sm text-zinc-500">
                      {exercise.sets} × {exercise.reps}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-500">
                    przerwa {exercise.rest_between_sets_s} s
                    {exercise.note && ` · ${exercise.note}`}
                  </p>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>

      {isDraft && (
        <p className="mt-4 rounded-xl bg-amber-50 p-3 text-xs text-amber-700">
          To szkic. Zatwierdzanie i ręczna edycja pojawią się w kolejnym etapie.
        </p>
      )}
    </div>
  )
}
