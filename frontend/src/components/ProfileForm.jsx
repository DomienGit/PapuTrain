import { useState } from 'react'
import { api } from '../api'
import MusclePreferences from './MusclePreferences'

const LEVELS = ['początkujący', 'średni', 'zaawansowany']

const inputClass =
  'w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-base outline-none focus:border-zinc-900'

/**
 * Formularz profilu — jeden komponent dla dwóch miejsc (req 25):
 * - onboarding krok 1: initial=null (nowy profil, wartości domyślne),
 * - podzakładka "Profil": initial=profil z API (pola wypełnione, edycja).
 * Zapis = PUT /api/profile; po sukcesie onSaved dostaje aktualny profil z serwera.
 */
export default function ProfileForm({ initial, submitLabel, onSaved }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [musclePrefs, setMusclePrefs] = useState(initial?.muscle_preferences ?? {})

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setMessage('')
    const form = new FormData(event.target)
    const value = (name, fallback = '') => form.get(name)?.toString().trim() || fallback
    try {
      const profile = await api('/api/profile', {
        method: 'PUT',
        body: JSON.stringify({
          goal: value('goal'),
          level: value('level', 'początkujący'),
          workouts_per_week: Number(value('workouts_per_week', '3')),
          workout_duration_min: Number(value('workout_duration_min', '45')),
          weight_kg: value('weight_kg') ? Number(value('weight_kg')) : null,
          height_cm: value('height_cm') ? Number(value('height_cm')) : null,
          limitations: value('limitations'),
          muscle_preferences: musclePrefs,
        }),
      })
      setMessage('Zapisano.')
      onSaved?.(profile)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-2xl bg-white p-5 shadow-sm">
      <div>
        <label className="mb-1 block text-sm font-medium text-zinc-700" htmlFor="goal">
          Cel (np. zbudowanie mięśni, redukcja, kondycja)
        </label>
        <input
          id="goal"
          name="goal"
          required
          maxLength={200}
          defaultValue={initial?.goal ?? ''}
          className={inputClass}
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-zinc-700" htmlFor="level">
          Poziom
        </label>
        <select
          id="level"
          name="level"
          defaultValue={initial?.level ?? 'początkujący'}
          className={inputClass}
        >
          {LEVELS.map((level) => (
            <option key={level} value={level}>
              {level}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-sm font-medium text-zinc-700" htmlFor="workouts_per_week">
            Treningów w tygodniu
          </label>
          <input
            id="workouts_per_week"
            name="workouts_per_week"
            type="number"
            min={1}
            max={7}
            defaultValue={initial?.workouts_per_week ?? 3}
            required
            className={inputClass}
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-zinc-700" htmlFor="workout_duration_min">
            Czas treningu (min)
          </label>
          <input
            id="workout_duration_min"
            name="workout_duration_min"
            type="number"
            min={10}
            max={240}
            defaultValue={initial?.workout_duration_min ?? 45}
            required
            className={inputClass}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-sm font-medium text-zinc-700" htmlFor="weight_kg">
            Waga (kg)
          </label>
          <input
            id="weight_kg"
            name="weight_kg"
            type="number"
            min={30}
            max={350}
            step="0.5"
            defaultValue={initial?.weight_kg ?? ''}
            className={inputClass}
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-zinc-700" htmlFor="height_cm">
            Wzrost (cm)
          </label>
          <input
            id="height_cm"
            name="height_cm"
            type="number"
            min={120}
            max={230}
            defaultValue={initial?.height_cm ?? ''}
            className={inputClass}
          />
        </div>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-zinc-700" htmlFor="limitations">
          Ograniczenia zdrowotne (opcjonalnie)
        </label>
        <textarea
          id="limitations"
          name="limitations"
          rows={2}
          maxLength={2000}
          placeholder="np. ból dolnego odcinka pleców przy skłonach"
          defaultValue={initial?.limitations ?? ''}
          className={inputClass}
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-zinc-700">
          Na jakich partiach chcesz się skupić? (opcjonalnie)
        </label>
        <p className="mb-2 text-xs text-zinc-500">
          1 = pomiń partię, 2 = maks. jedno ćwiczenie w tygodniu, 4-5 = priorytet
          (5 najmocniejszy). Bez oceny = neutralnie.
        </p>
        <MusclePreferences value={musclePrefs} onChange={setMusclePrefs} />
      </div>

      {error && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
      )}
      {message && <p className="text-sm text-green-700">{message}</p>}

      <button
        type="submit"
        disabled={busy}
        className="w-full rounded-lg bg-zinc-900 py-2.5 font-medium text-white hover:bg-zinc-700 disabled:opacity-50"
      >
        {busy ? 'Zapisuję…' : submitLabel}
      </button>
    </form>
  )
}
