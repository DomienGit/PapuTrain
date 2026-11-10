import { useEffect, useState } from 'react'
import { api } from '../api'
import EquipmentList from '../components/EquipmentList'
import ExerciseList from '../components/ExerciseList'
import MusclePreferences from '../components/MusclePreferences'

/**
 * Zakładka "Sprzęt i ćwiczenia" (PLAN.md: ekran 3). Dostępna zawsze,
 * także gdy plan jest aktywny. Trzy pod-zakładki: Sprzęt, Ćwiczenia, Profil.
 */
export default function EquipmentExercises() {
  const [subTab, setSubTab] = useState('equipment') // 'equipment' | 'exercises' | 'profile'
  const [ownedNames, setOwnedNames] = useState(new Set())
  // Podzakładka "Profil" (req 23): profil z API + robocze oceny partii.
  const [profile, setProfile] = useState(null) // null = jeszcze ładuję
  const [prefs, setPrefs] = useState({})
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  // Lista posiadanego sprzętu — potrzebna do liczenia wykonalnych ćwiczeń.
  // Odświeżamy przy każdym wejściu w pod-zakładkę ćwiczeń (sprzęt mógł się zmienić).
  useEffect(() => {
    if (subTab !== 'exercises') return
    api('/api/equipment?owned=true')
      .then((items) => setOwnedNames(new Set(items.map((i) => i.name.toLowerCase()))))
      .catch(() => {})
  }, [subTab])

  // Podzakładka Profil: ładujemy profil przy każdym wejściu (oceny mogły się zmienić).
  useEffect(() => {
    if (subTab !== 'profile') return
    setMessage('')
    setError('')
    api('/api/profile')
      .then((data) => {
        setProfile(data)
        setPrefs(data?.muscle_preferences ?? {})
      })
      .catch((err) => setError(err.message))
  }, [subTab])

  async function savePrefs() {
    if (!profile) return
    setSaving(true)
    setError('')
    setMessage('')
    try {
      // PUT nadpisuje CAŁY profil — odsyłamy wszystkie pola z GET-a + nowe oceny.
      const updated = await api('/api/profile', {
        method: 'PUT',
        body: JSON.stringify({
          goal: profile.goal,
          level: profile.level,
          workouts_per_week: profile.workouts_per_week,
          workout_duration_min: profile.workout_duration_min,
          weight_kg: profile.weight_kg,
          height_cm: profile.height_cm,
          limitations: profile.limitations,
          muscle_preferences: prefs,
        }),
      })
      setProfile(updated)
      setPrefs(updated.muscle_preferences ?? {})
      setMessage('Zapisano.')
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

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
        <button className={tabClass(subTab === 'profile')} onClick={() => setSubTab('profile')}>
          Profil
        </button>
      </div>

      {subTab === 'equipment' && <EquipmentList allowAdd />}

      {subTab === 'exercises' && <ExerciseList ownedNames={ownedNames} allowAdd />}

      {subTab === 'profile' && (
        <div>
          <p className="mb-3 text-sm text-zinc-600">
            Gwiazdki mówią AI, na jakich partiach ma się skupić plan: 1 = pomiń partię,
            2 = maks. jedno ćwiczenie w tygodniu, 4-5 = priorytet (5 najmocniejszy).
          </p>
          {profile === null ? (
            <p className="text-sm text-zinc-500">Ładowanie…</p>
          ) : (
            <>
              <MusclePreferences value={prefs} onChange={setPrefs} />
              {error && (
                <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
              )}
              {message && <p className="mt-3 text-sm text-green-700">{message}</p>}
              <button
                onClick={savePrefs}
                disabled={saving}
                className="mt-4 w-full rounded-lg bg-zinc-900 py-2.5 font-medium text-white hover:bg-zinc-700 disabled:opacity-50"
              >
                {saving ? 'Zapisuję…' : 'Zapisz'}
              </button>
            </>
          )}
        </div>
      )}
    </div>
  )
}
