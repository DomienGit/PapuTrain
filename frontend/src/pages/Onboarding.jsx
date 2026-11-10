import { useEffect, useState } from 'react'
import { api } from '../api'
import EquipmentList from '../components/EquipmentList'
import ExerciseList from '../components/ExerciseList'
import ProfileForm from '../components/ProfileForm'

/**
 * Kreator pierwszego uruchomienia (PLAN.md: ekran 2). Pokazuje się tylko,
 * gdy nie ma profilu. Trzy kroki: profil → sprzęt → ćwiczenia (opcjonalne).
 */
export default function Onboarding({ onDone }) {
  const [step, setStep] = useState(1) // 1 = profil, 2 = sprzęt, 3 = ćwiczenia
  const [ownedNames, setOwnedNames] = useState(new Set())
  const [error, setError] = useState('')

  // Krok 3 potrzebuje listy posiadanego sprzętu, żeby pokazać tylko
  // wykonalne ćwiczenia. Ładujemy ją razem z krokiem 2.
  useEffect(() => {
    if (step !== 2) return
    api('/api/equipment?owned=true')
      .then((items) => setOwnedNames(new Set(items.map((i) => i.name.toLowerCase()))))
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

        {step === 1 && (
          <ProfileForm initial={null} submitLabel="Dalej" onSaved={next} />
        )}
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
