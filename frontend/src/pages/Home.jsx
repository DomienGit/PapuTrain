import { useEffect, useState } from 'react'
import { api } from '../api'
import DraftPanel from '../components/DraftPanel'
import Stars from '../components/Stars'

/**
 * Ekran główny. Trzy stany (PLAN.md ekran 4 i 6):
 * - szkic → DraftPanel (edycja, zatwierdzanie),
 * - plan aktywny → widok "na żywo": odhaczanie treningów, oceny 1-5,
 *   uwagi do ćwiczeń, "Generuj następny tydzień" (zablokowany do odhaczenia),
 * - brak planu → przycisk "Generuj plan".
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
        plan.status === 'draft' ? (
          <DraftPanel plan={plan} onChange={setPlan} onRejected={() => setPlan(null)} />
        ) : (
          <PlanView plan={plan} onChange={setPlan} onGenerate={generate} generating={busy} />
        )
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

function PlanView({ plan, onChange, onGenerate, generating }) {
  const [error, setError] = useState('')

  // Wspólny helper PATCH dla odhaczania i ocen. Backend zwraca cały
  // odświeżony plan — podmieniamy go w stanie rodzica, żeby gwiazdki
  // i odhaczenia przerysowywały się od razu, bez restartu aplikacji.
  async function patchPlan(path, body) {
    setError('')
    try {
      const updated = await api(path, { method: 'PATCH', body: JSON.stringify(body) })
      onChange(updated)
      return updated
    } catch (err) {
      setError(err.message)
      return null
    }
  }

  const undone = plan.workouts.filter((w) => !w.done).length

  return (
    <div className="mt-4">
      <h2 className="text-lg font-bold text-zinc-900">
        {plan.week_title || `Tydzień ${plan.week_number}`}
      </h2>

      {plan.coach_note && (
        <p className="mt-2 rounded-xl bg-white p-3 text-sm text-zinc-600 shadow-sm">
          <span className="font-medium">Trener: </span>
          {plan.coach_note}
        </p>
      )}

      {error && (
        <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
      )}

      <div className="mt-3 space-y-4">
        {plan.workouts.map((workout) => (
          <WorkoutSection key={workout.id} workout={workout} patchPlan={patchPlan} />
        ))}
      </div>

      <div className="mt-5">
        <button
          onClick={onGenerate}
          disabled={generating || undone > 0}
          className="w-full rounded-lg bg-zinc-900 py-2.5 font-medium text-white hover:bg-zinc-700 disabled:opacity-50"
        >
          {generating ? 'AI układa plan… (może chwilę potrwać)' : 'Generuj następny tydzień'}
        </button>
        {undone > 0 && (
          <p className="mt-1 text-center text-xs text-zinc-500">
            odhacz wszystkie treningi (zostały {undone})
          </p>
        )}
      </div>
    </div>
  )
}

function WorkoutSection({ workout, patchPlan }) {
  return (
    <section className="rounded-xl bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold text-zinc-900">{workout.name}</h3>
          {workout.rest_between_exercises_s != null && (
            <p className="text-xs text-zinc-500">
              przerwa między ćwiczeniami: {workout.rest_between_exercises_s} s
            </p>
          )}
        </div>
        {workout.done && workout.completed_date && (
          <span className="shrink-0 rounded-full bg-emerald-100 px-2 py-0.5 text-xs text-emerald-700">
            zrobiony {workout.completed_date}
          </span>
        )}
      </div>

      <ul className="mt-3 divide-y divide-zinc-100">
        {workout.exercises.map((exercise) => (
          <ExerciseFeedback
            key={exercise.id}
            workout={workout}
            exercise={exercise}
            patchPlan={patchPlan}
          />
        ))}
      </ul>

      <label className="mt-3 flex items-center gap-2 border-t border-zinc-100 pt-3 text-sm text-zinc-700">
        <input
          type="checkbox"
          checked={workout.done}
          onChange={() =>
            patchPlan(`/api/plans/active/workouts/${workout.id}`, { done: !workout.done })
          }
          className="size-5 accent-emerald-600"
          aria-label={`Trening zrobiony: ${workout.name}`}
        />
        trening zrobiony
      </label>
    </section>
  )
}

function ExerciseFeedback({ workout, exercise, patchPlan }) {
  const [noteOpen, setNoteOpen] = useState(false)
  const [noteText, setNoteText] = useState(exercise.note || '')
  // "Zrobiłem" (req 21): faktyczne serie×powtórzenia; placeholder = sugestia AI.
  const [performedText, setPerformedText] = useState(exercise.performed || '')

  async function saveNote() {
    const updated = await patchPlan(
      `/api/plans/active/workouts/${workout.id}/exercises/${exercise.id}`,
      { note: noteText },
    )
    if (updated) setNoteOpen(false)
  }

  // Zapis "zrobiłem" przy wyjściu z pola (blur) lub Enter; puste pole czyści wpis.
  async function savePerformed() {
    const value = performedText.trim()
    if (value === (exercise.performed || '')) return // bez zmian — nie dzwoń do API
    await patchPlan(`/api/plans/active/workouts/${workout.id}/exercises/${exercise.id}`, {
      performed: value,
    })
  }

  return (
    <li className="py-2">
      <div className="flex justify-between gap-2">
        <span className="text-zinc-900">{exercise.name}</span>
        <span className="shrink-0 text-sm text-zinc-500">
          {exercise.sets} × {exercise.reps}
        </span>
      </div>
      <p className="text-xs text-zinc-500">
        przerwa {exercise.rest_between_sets_s} s
        {exercise.load && ` · ${exercise.load}`}
      </p>
      <div className="mt-1 flex items-center gap-3">
        <Stars
          value={exercise.rating}
          onChange={(n) =>
            patchPlan(`/api/plans/active/workouts/${workout.id}/exercises/${exercise.id}`, {
              rating: n,
            })
          }
          label={`ocena wykonania: ${exercise.name}`}
        />
        <button
          onClick={() => setNoteOpen(!noteOpen)}
          className="text-xs text-zinc-400 underline-offset-2 hover:text-zinc-600 hover:underline"
        >
          {exercise.note ? 'zmień uwagę' : '+ uwaga'}
        </button>
      </div>
      <div className="mt-2 flex items-center gap-2">
        <span className="text-xs text-zinc-500">zrobiłem:</span>
        <input
          value={performedText}
          onChange={(e) => setPerformedText(e.target.value)}
          onBlur={savePerformed}
          onKeyDown={(e) => e.key === 'Enter' && e.currentTarget.blur()}
          placeholder={`${exercise.sets}×${exercise.reps}`} // sugestia AI jako wzór
          inputMode="numeric"
          className="w-24 rounded-lg border border-zinc-200 px-2 py-1 text-sm text-zinc-900 placeholder:text-zinc-300 focus:border-zinc-400 focus:outline-none"
          aria-label={`faktycznie zrobione serie×powtórzenia: ${exercise.name}`}
        />
        {exercise.performed && (
          <span className="text-xs text-emerald-600">zapisane</span>
        )}
      </div>
      {exercise.note && !noteOpen && (
        <p className="mt-1 text-xs text-zinc-600">„{exercise.note}”</p>
      )}
      {noteOpen && (
        <div className="mt-2 flex gap-2">
          <input
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            placeholder="np. boli kolano przy przysiadzie"
            className="min-w-0 flex-1 rounded-lg border border-zinc-200 px-3 py-1.5 text-sm focus:border-zinc-400 focus:outline-none"
          />
          <button
            onClick={saveNote}
            className="rounded-lg bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-zinc-700"
          >
            Zapisz
          </button>
        </div>
      )}
    </li>
  )
}
