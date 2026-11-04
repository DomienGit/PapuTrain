import { useEffect, useState } from 'react'
import { api } from '../api'

/**
 * Zakładka "Historia" (Etap 8, PLAN.md ekran 7): lista archiwalnych planów,
 * kliknięcie pokazuje pełny plan — tylko do wglądu, bez akcji.
 */
export default function History() {
  const [plans, setPlans] = useState(null)
  const [openPlan, setOpenPlan] = useState(null) // pełny plan po kliknięciu
  const [error, setError] = useState('')

  useEffect(() => {
    api('/api/plans/archived')
      .then(setPlans)
      .catch((err) => setError(err.message))
  }, [])

  async function open(planId) {
    setError('')
    try {
      setOpenPlan(await api(`/api/plans/archived/${planId}`))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="mx-auto w-full max-w-md px-4 py-6">
      <h1 className="text-xl font-bold text-zinc-900">Historia</h1>

      {error && (
        <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
      )}

      {openPlan ? (
        <ArchivedPlanDetail plan={openPlan} onBack={() => setOpenPlan(null)} />
      ) : plans === null ? (
        <p className="mt-6 text-center text-sm text-zinc-500">Ładowanie…</p>
      ) : plans.length === 0 ? (
        <p className="mt-6 rounded-xl bg-white p-4 text-center text-sm text-zinc-500 shadow-sm">
          Jeszcze nie masz archiwalnych planów. Stare plany trafią tu po zatwierdzeniu
          następnego tygodnia.
        </p>
      ) : (
        <ul className="mt-4 space-y-2">
          {plans.map((p) => (
            <li key={p.id}>
              <button
                onClick={() => open(p.id)}
                className="w-full rounded-xl bg-white p-4 text-left shadow-sm hover:bg-zinc-50"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-zinc-900">
                    {p.week_title || `Tydzień ${p.week_number}`}
                  </span>
                  <span className="text-xs text-zinc-400">{p.workouts_total} treningów</span>
                </div>
                <p className="mt-1 text-xs text-zinc-500">
                  odhaczone: {p.workouts_done} z {p.workouts_total}
                </p>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function ArchivedPlanDetail({ plan, onBack }) {
  return (
    <div className="mt-4">
      <button
        onClick={onBack}
        className="text-sm text-zinc-500 underline-offset-2 hover:text-zinc-700 hover:underline"
      >
        ← Wróć do listy
      </button>

      <h2 className="mt-2 text-lg font-bold text-zinc-900">
        {plan.week_title || `Tydzień ${plan.week_number}`}
      </h2>

      {plan.coach_note && (
        <p className="mt-2 rounded-xl bg-white p-3 text-sm text-zinc-600 shadow-sm">
          <span className="font-medium">Trener: </span>
          {plan.coach_note}
        </p>
      )}

      <div className="mt-3 space-y-4">
        {plan.workouts.map((workout) => (
          <section key={workout.id} className="rounded-xl bg-white p-4 shadow-sm">
            <div className="flex items-start justify-between gap-2">
              <h3 className="font-semibold text-zinc-900">{workout.name}</h3>
              {workout.done && workout.completed_date && (
                <span className="shrink-0 rounded-full bg-emerald-100 px-2 py-0.5 text-xs text-emerald-700">
                  zrobiony {workout.completed_date}
                </span>
              )}
            </div>
            <ul className="mt-3 divide-y divide-zinc-100">
              {workout.exercises.map((ex) => (
                <li key={ex.id} className="py-2">
                  <div className="flex justify-between gap-2">
                    <span className="text-zinc-900">{ex.name}</span>
                    <span className="shrink-0 text-sm text-zinc-500">
                      {ex.sets} × {ex.reps}
                      {ex.load && ` · ${ex.load}`}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-500">
                    przerwa {ex.rest_between_sets_s} s
                    {ex.performed && ` · zrobiłem: ${ex.performed}`}
                    {ex.rating != null && ` · ocena: ${'★'.repeat(ex.rating)}`}
                    {ex.note && ` · ${ex.note}`}
                  </p>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  )
}
