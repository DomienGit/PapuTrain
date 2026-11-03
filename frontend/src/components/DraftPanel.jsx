import { useState } from 'react'
import { api } from '../api'

/**
 * Panel szkicu (Etap 6, PLAN.md ekran 6): oglądanie wygenerowanego planu,
 * ręczna edycja treningów i ćwiczeń, "poproś AI o zmianę" per trening,
 * zatwierdzanie (szkic → plan aktywny) i odrzucanie.
 * Każda akcja edycji zwraca z API pełny odświeżony plan — podmieniamy go w górze.
 */
export default function DraftPanel({ plan, onChange, onRejected }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function approve() {
    setBusy(true)
    setError('')
    try {
      // Plan wraca już ze statusem "active" — rodzic sam pokaże widok aktywnego.
      onChange(await api('/api/plans/draft/approve', { method: 'POST' }))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function reject() {
    if (!window.confirm('Odrzucić ten szkic? Później możesz wygenerować plan od nowa.')) return
    setBusy(true)
    setError('')
    try {
      await api('/api/plans/draft', { method: 'DELETE' })
      onRejected()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mt-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-zinc-900">
          {plan.week_title || `Tydzień ${plan.week_number}`}
        </h2>
        <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-700">
          szkic
        </span>
      </div>

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
          <WorkoutCard
            key={workout.id}
            workout={workout}
            onChange={onChange}
            setError={setError}
          />
        ))}
      </div>

      <div className="mt-5 space-y-2">
        <button
          onClick={approve}
          disabled={busy}
          className="w-full rounded-lg bg-emerald-600 py-2.5 font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
        >
          {busy ? 'Zatwierdzam…' : 'Zatwierdź plan'}
        </button>
        <button
          onClick={reject}
          disabled={busy}
          className="w-full rounded-lg bg-white py-2.5 font-medium text-zinc-600 shadow-sm hover:bg-zinc-50 disabled:opacity-50"
        >
          Odrzuć szkic (generuj od nowa)
        </button>
      </div>
    </div>
  )
}

function WorkoutCard({ workout, onChange, setError }) {
  const [editingHeader, setEditingHeader] = useState(false)
  const [aiOpen, setAiOpen] = useState(false)
  const [aiText, setAiText] = useState('')
  const [aiBusy, setAiBusy] = useState(false)

  async function sendToAi() {
    if (!aiText.trim()) return
    setAiBusy(true)
    setError('')
    try {
      onChange(
        await api(`/api/plans/draft/workouts/${workout.id}/ask-ai`, {
          method: 'POST',
          body: JSON.stringify({ request: aiText }),
        }),
      )
      setAiOpen(false)
      setAiText('')
    } catch (err) {
      setError(err.message)
    } finally {
      setAiBusy(false)
    }
  }

  return (
    <section className="rounded-xl bg-white p-4 shadow-sm">
      {editingHeader ? (
        <HeaderEditForm workout={workout} onChange={onChange} onClose={() => setEditingHeader(false)} setError={setError} />
      ) : (
        <div className="flex items-start justify-between gap-2">
          <div>
            <h3 className="font-semibold text-zinc-900">{workout.name}</h3>
            {workout.rest_between_exercises_s != null && (
              <p className="text-xs text-zinc-500">
                przerwa między ćwiczeniami: {workout.rest_between_exercises_s} s
              </p>
            )}
          </div>
          <button
            onClick={() => setEditingHeader(true)}
            className="shrink-0 rounded-md px-2 py-1 text-xs font-medium text-zinc-500 hover:bg-zinc-100"
          >
            edytuj
          </button>
        </div>
      )}

      <ul className="mt-3 divide-y divide-zinc-100">
        {workout.exercises.map((exercise) => (
          <ExerciseRow
            key={exercise.id}
            workout={workout}
            exercise={exercise}
            onChange={onChange}
            setError={setError}
          />
        ))}
      </ul>

      <div className="mt-3 border-t border-zinc-100 pt-3">
        {aiOpen ? (
          <div>
            <textarea
              value={aiText}
              onChange={(e) => setAiText(e.target.value)}
              rows={2}
              placeholder='np. "zamień pompki na ćwiczenia na nogi i skróć przerwy"'
              className="w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm focus:border-zinc-400 focus:outline-none"
            />
            <div className="mt-2 flex gap-2">
              <button
                onClick={sendToAi}
                disabled={aiBusy || !aiText.trim()}
                className="flex-1 rounded-lg bg-zinc-900 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50"
              >
                {aiBusy ? 'AI poprawia trening… (może chwilę potrwać)' : 'Wyślij do AI'}
              </button>
              <button
                onClick={() => setAiOpen(false)}
                disabled={aiBusy}
                className="rounded-lg px-3 py-2 text-sm text-zinc-500 hover:bg-zinc-100 disabled:opacity-50"
              >
                Anuluj
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setAiOpen(true)}
            className="w-full rounded-lg border border-zinc-200 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50"
          >
            Poproś AI o zmianę tego treningu
          </button>
        )}
      </div>
    </section>
  )
}

function HeaderEditForm({ workout, onChange, onClose, setError }) {
  const [name, setName] = useState(workout.name)
  const [rest, setRest] = useState(workout.rest_between_exercises_s ?? '')
  const [saving, setSaving] = useState(false)

  async function save() {
    setSaving(true)
    setError('')
    const body = { name }
    if (rest !== '') body.rest_between_exercises_s = Number(rest)
    try {
      onChange(
        await api(`/api/plans/draft/workouts/${workout.id}`, {
          method: 'PATCH',
          body: JSON.stringify(body),
        }),
      )
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        className="w-full rounded-lg border border-zinc-200 px-3 py-1.5 text-sm font-semibold focus:border-zinc-400 focus:outline-none"
      />
      <input
        type="number"
        value={rest}
        onChange={(e) => setRest(e.target.value)}
        placeholder="przerwa między ćwiczeniami (s)"
        className="mt-2 w-full rounded-lg border border-zinc-200 px-3 py-1.5 text-sm focus:border-zinc-400 focus:outline-none"
      />
      <div className="mt-2 flex gap-2">
        <button
          onClick={save}
          disabled={saving || !name.trim()}
          className="rounded-lg bg-zinc-900 px-4 py-1.5 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50"
        >
          Zapisz
        </button>
        <button
          onClick={onClose}
          className="rounded-lg px-3 py-1.5 text-sm text-zinc-500 hover:bg-zinc-100"
        >
          Anuluj
        </button>
      </div>
    </div>
  )
}

function ExerciseRow({ workout, exercise, onChange, setError }) {
  const [editing, setEditing] = useState(false)

  async function remove() {
    if (!window.confirm(`Usunąć ćwiczenie "${exercise.name}" z tego treningu?`)) return
    setError('')
    try {
      onChange(
        await api(`/api/plans/draft/workouts/${workout.id}/exercises/${exercise.id}`, {
          method: 'DELETE',
        }),
      )
    } catch (err) {
      setError(err.message)
    }
  }

  if (editing) {
    return (
      <li className="py-2">
        <ExerciseEditForm
          workout={workout}
          exercise={exercise}
          onChange={onChange}
          onClose={() => setEditing(false)}
          setError={setError}
        />
      </li>
    )
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
        {exercise.note && ` · ${exercise.note}`}
      </p>
      <div className="mt-1 flex gap-2">
        <button
          onClick={() => setEditing(true)}
          className="rounded-md px-2 py-0.5 text-xs font-medium text-zinc-500 hover:bg-zinc-100"
        >
          edytuj
        </button>
        <button
          onClick={remove}
          className="rounded-md px-2 py-0.5 text-xs font-medium text-red-400 hover:bg-red-50"
        >
          usuń
        </button>
      </div>
    </li>
  )
}

function ExerciseEditForm({ workout, exercise, onChange, onClose, setError }) {
  const [form, setForm] = useState({
    name: exercise.name,
    sets: exercise.sets,
    reps: exercise.reps,
    rest_between_sets_s: exercise.rest_between_sets_s ?? '',
    note: exercise.note || '',
  })
  const [saving, setSaving] = useState(false)

  function set(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  async function save() {
    setSaving(true)
    setError('')
    try {
      onChange(
        await api(`/api/plans/draft/workouts/${workout.id}/exercises/${exercise.id}`, {
          method: 'PATCH',
          body: JSON.stringify({
            name: form.name,
            sets: Number(form.sets),
            reps: form.reps,
            ...(form.rest_between_sets_s !== '' && {
              rest_between_sets_s: Number(form.rest_between_sets_s),
            }),
            note: form.note,
          }),
        }),
      )
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="rounded-lg bg-zinc-50 p-3">
      <input
        value={form.name}
        onChange={(e) => set('name', e.target.value)}
        placeholder="nazwa ćwiczenia"
        className="w-full rounded-lg border border-zinc-200 px-3 py-1.5 text-sm focus:border-zinc-400 focus:outline-none"
      />
      <div className="mt-2 grid grid-cols-3 gap-2">
        <input
          type="number"
          value={form.sets}
          onChange={(e) => set('sets', e.target.value)}
          placeholder="serie"
          className="rounded-lg border border-zinc-200 px-3 py-1.5 text-sm focus:border-zinc-400 focus:outline-none"
        />
        <input
          value={form.reps}
          onChange={(e) => set('reps', e.target.value)}
          placeholder="powtórzenia"
          className="rounded-lg border border-zinc-200 px-3 py-1.5 text-sm focus:border-zinc-400 focus:outline-none"
        />
        <input
          type="number"
          value={form.rest_between_sets_s}
          onChange={(e) => set('rest_between_sets_s', e.target.value)}
          placeholder="przerwa s"
          className="rounded-lg border border-zinc-200 px-3 py-1.5 text-sm focus:border-zinc-400 focus:outline-none"
        />
      </div>
      <input
        value={form.note}
        onChange={(e) => set('note', e.target.value)}
        placeholder="uwaga (np. tempo, uwaga zdrowotna)"
        className="mt-2 w-full rounded-lg border border-zinc-200 px-3 py-1.5 text-sm focus:border-zinc-400 focus:outline-none"
      />
      <div className="mt-2 flex gap-2">
        <button
          onClick={save}
          disabled={saving || !form.name.trim()}
          className="rounded-lg bg-zinc-900 px-4 py-1.5 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50"
        >
          {saving ? 'Zapisuję…' : 'Zapisz'}
        </button>
        <button
          onClick={onClose}
          className="rounded-lg px-3 py-1.5 text-sm text-zinc-500 hover:bg-zinc-100"
        >
          Anuluj
        </button>
      </div>
    </div>
  )
}
