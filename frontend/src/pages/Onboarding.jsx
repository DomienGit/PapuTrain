import { useEffect, useState } from 'react'
import { api } from '../api'
import EquipmentList from '../components/EquipmentList'
import ExerciseList from '../components/ExerciseList'

const LEVELS = ['początkujący', 'średni', 'zaawansowany']

const inputClass =
  'w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-base outline-none focus:border-zinc-900'

/**
 * Kreator pierwszego uruchomienia (PLAN.md: ekran 2). Pokazuje się tylko,
 * gdy nie ma profilu. Trzy kroki: profil → sprzęt → ćwiczenia (opcjonalne).
 */
export default function Onboarding({ onDone }) {
  const [step, setStep] = useState(1) // 1 = profil, 2 = sprzęt, 3 = ćwiczenia
  const [ownedNames, setOwnedNames] = useState(new Set())
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  // Krok 3 potrzebuje listy posiadanego sprzętu, żeby pokazać tylko
  // wykonalne ćwiczenia. Ładujemy ją razem z krokiem 2.
  useEffect(() => {
    if (step !== 2) return
    api('/api/equipment?owned=true')
      .then((items) => setOwnedNames(new Set(items.map((i) => i.name.casefold()))))
      .catch((err) => setError(err.message))
  }, [step])

  function next() {
    setError('')
    setStep(step + 1)
  }

  return (
    <div className="min-h-dvh bg-zinc-100 px-4 py-8">
      <div className="mx-auto w-full max-w-sm">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-zinc-900">Witaj w PapuTrain</h1>
          <p className="mt-1 text-sm text-zinc-500">Krok {step} z 3</p>
          <div className="mt-3 flex justify-center gap-1.5">
            {[1, 2, 3].map((n) => (
              <span
                key={n}
                className={`h-1.5 w-8 rounded-full ${n <= step ? 'bg-zinc-900' : 'bg-zinc-300'}`}
              />
            ))}
          </div>
        </div>

        {error && (
          <p className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
        )}

        {step === 1 && <ProfileStep onSaved={next} />}
        {step === 2 && (
          <div>
            <p className="mb-3 text-sm text-zinc-600">
              Zaznacz sprzęt, który masz. To podstawa — AI może używać tylko tego,
              na czym naprawdę potrenujesz.
            </p>
            <EquipmentList allowAdd />
            <button
              onClick={next}
              className="mt-6 w-full rounded-lg bg-zinc-900 py-2.5 font-medium text-white hover:bg-zinc-700"
            >
              Dalej
            </button>
          </div>
        )}
        {step === 3 && (
          <div>
            <p className="mb-3 text-sm text-zinc-600">
              Odhacz ćwiczenia, które Ci pasują — AI potraktuje je jako preferencje.
              Możesz też pominąć ten krok i pozwolić AI wybrać za Ciebie.
            </p>
            <ExerciseList ownedNames={ownedNames} />
            <div className="mt-6 space-y-2">
              <button
                onClick={onDone}
                className="w-full rounded-lg bg-zinc-900 py-2.5 font-medium text-white hover:bg-zinc-700"
              >
                Zakończ
              </button>
              <button
                onClick={onDone}
                className="w-full rounded-lg border border-zinc-300 py-2.5 text-sm text-zinc-700 hover:bg-zinc-200"
              >
                Pomiń — niech AI wybierze
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function ProfileStep({ onSaved }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    const form = new FormData(event.target)
    const value = (name, fallback = '') => form.get(name)?.toString().trim() || fallback
    try {
      await api('/api/profile', {
        method: 'PUT',
        body: JSON.stringify({
          goal: value('goal'),
          level: value('level', 'początkujący'),
          workouts_per_week: Number(value('workouts_per_week', '3')),
          workout_duration_min: Number(value('workout_duration_min', '45')),
          weight_kg: value('weight_kg') ? Number(value('weight_kg')) : null,
          height_cm: value('height_cm') ? Number(value('height_cm')) : null,
          limitations: value('limitations'),
        }),
      })
      onSaved()
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
        <input id="goal" name="goal" required maxLength={200} className={inputClass} />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-zinc-700" htmlFor="level">
          Poziom
        </label>
        <select id="level" name="level" defaultValue="początkujący" className={inputClass}>
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
            defaultValue={3}
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
            defaultValue={45}
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
          className={inputClass}
        />
      </div>

      <button
        type="submit"
        disabled={busy}
        className="w-full rounded-lg bg-zinc-900 py-2.5 font-medium text-white hover:bg-zinc-700 disabled:opacity-50"
      >
        {busy ? 'Zapisuję…' : 'Dalej'}
      </button>
    </form>
  )
}
