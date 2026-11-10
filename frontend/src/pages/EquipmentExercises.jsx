import { useEffect, useState } from 'react'
import { api } from '../api'
import EquipmentList from '../components/EquipmentList'
import ExerciseList from '../components/ExerciseList'
import History from './History'
import ProfileForm from '../components/ProfileForm'

/**
 * Zakładka "Profil" (PLAN.md: ekran 3, req 26). Dostępna zawsze, także gdy
 * plan jest aktywny. Cztery pod-zakładki: Sprzęt, Ćwiczenia, Parametry, Historia.
 */
export default function EquipmentExercises() {
  const [subTab, setSubTab] = useState('equipment')
  // 'equipment' | 'exercises' | 'profile' | 'history'
  const [ownedNames, setOwnedNames] = useState(new Set())
  // Podzakładka "Parametry" (req 25): profil z API dla formularza edycji.
  const [profile, setProfile] = useState(null) // null = jeszcze ładuję
  const [error, setError] = useState('')

  // Lista posiadanego sprzętu — potrzebna do liczenia wykonalnych ćwiczeń.
  // Odświeżamy przy każdym wejściu w pod-zakładkę ćwiczeń (sprzęt mógł się zmienić).
  useEffect(() => {
    if (subTab !== 'exercises') return
    api('/api/equipment?owned=true')
      .then((items) => setOwnedNames(new Set(items.map((i) => i.name.toLowerCase()))))
      .catch(() => {})
  }, [subTab])

  // Podzakładka Parametry: ładujemy profil przy każdym wejściu (dane mogły się zmienić).
  useEffect(() => {
    if (subTab !== 'profile') return
    setError('')
    api('/api/profile')
      .then(setProfile)
      .catch((err) => setError(err.message))
  }, [subTab])

  const tabClass = (active) =>
    `flex-1 rounded-lg py-2 text-center text-xs font-medium transition-colors ${
      active ? 'bg-zinc-900 text-white' : 'text-zinc-600 hover:bg-zinc-100'
    }`

  return (
    <div className="mx-auto w-full max-w-md px-4 py-6">
      <h1 className="mb-4 text-xl font-bold text-zinc-900">Profil</h1>

      <div className="mb-5 flex gap-1 rounded-xl bg-white p-1 shadow-sm">
        <button className={tabClass(subTab === 'equipment')} onClick={() => setSubTab('equipment')}>
          Sprzęt
        </button>
        <button className={tabClass(subTab === 'exercises')} onClick={() => setSubTab('exercises')}>
          Ćwiczenia
        </button>
        <button className={tabClass(subTab === 'profile')} onClick={() => setSubTab('profile')}>
          Parametry
        </button>
        <button className={tabClass(subTab === 'history')} onClick={() => setSubTab('history')}>
          Historia
        </button>
      </div>

      {subTab === 'equipment' && <EquipmentList allowAdd />}

      {subTab === 'exercises' && <ExerciseList ownedNames={ownedNames} allowAdd />}

      {subTab === 'history' && <History />}

      {subTab === 'profile' && (
        <div>
          <p className="mb-3 text-sm text-zinc-600">
            Tutaj aktualizujesz swoje dane: cel, poziom, parametry ciała i preferencje
            partii. AI korzysta z nich przy każdym generowaniu planu.
          </p>
          {error && (
            <p className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
          )}
          {profile === null ? (
            <p className="text-sm text-zinc-500">Ładowanie…</p>
          ) : (
            <ProfileForm initial={profile} submitLabel="Zapisz" onSaved={setProfile} />
          )}
        </div>
      )}
    </div>
  )
}
