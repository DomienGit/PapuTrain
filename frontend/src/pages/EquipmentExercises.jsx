import { useEffect, useState } from 'react'
import { api } from '../api'
import EquipmentList from '../components/EquipmentList'
import ExerciseList from '../components/ExerciseList'

/**
 * Zakładka "Sprzęt i ćwiczenia" (PLAN.md: ekran 3). Dostępna zawsze,
 * także gdy plan jest aktywny. Dwie pod-zakładki: Sprzęt i Ćwiczenia.
 */
export default function EquipmentExercises() {
  const [subTab, setSubTab] = useState('equipment') // 'equipment' | 'exercises'
  const [ownedNames, setOwnedNames] = useState(new Set())

  // Lista posiadanego sprzętu — potrzebna do liczenia wykonalnych ćwiczeń.
  // Odświeżamy przy każdym wejściu w pod-zakładkę ćwiczeń (sprzęt mógł się zmienić).
  useEffect(() => {
    if (subTab !== 'exercises') return
    api('/api/equipment?owned=true')
      .then((items) => setOwnedNames(new Set(items.map((i) => i.name.casefold()))))
      .catch(() => {})
  }, [subTab])

  const tabClass = (active) =>
    `flex-1 rounded-lg py-2 text-center text-sm font-medium transition-colors ${
      active ? 'bg-zinc-900 text-white' : 'text-zinc-600 hover:bg-zinc-100'
    }`

  return (
    <div className="mx-auto w-full max-w-md px-4 py-6">
      <h1 className="mb-4 text-xl font-bold text-zinc-900">Sprzęt i ćwiczenia</h1>

      <div className="mb-5 flex gap-1 rounded-xl bg-white p-1 shadow-sm">
        <button className={tabClass(subTab === 'equipment')} onClick={() => setSubTab('equipment')}>
          Sprzęt
        </button>
        <button className={tabClass(subTab === 'exercises')} onClick={() => setSubTab('exercises')}>
          Ćwiczenia
        </button>
      </div>

      {subTab === 'equipment' ? (
        <EquipmentList allowAdd />
      ) : (
        <ExerciseList ownedNames={ownedNames} allowAdd />
      )}
    </div>
  )
}
