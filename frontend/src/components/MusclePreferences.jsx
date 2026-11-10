import Stars from './Stars'

// Partie mięśniowe do preferencji (req 23). Musi się zgadzać z MUSCLE_GROUPS
// w app/schemas.py — backend wycina klucze spoza swojej listy.
const MUSCLE_GROUPS = [
  'klatka',
  'plecy',
  'nogi',
  'barki',
  'biceps',
  'triceps',
  'brzuch',
  'pośladki',
  'łydki',
  'przedramiona',
]

/**
 * Lista partii mięśniowych z gwiazdkami 1-5 (req 23). value to obiekt
 * {partia: 1-5} zawierający TYLKO ocenione partie; onChange dostaje nowy obiekt.
 */
export default function MusclePreferences({ value, onChange }) {
  return (
    <div className="divide-y divide-zinc-200 overflow-hidden rounded-2xl bg-white shadow-sm">
      {MUSCLE_GROUPS.map((group) => (
        <div key={group} className="flex items-center justify-between px-4 py-2.5">
          <span className="text-sm capitalize text-zinc-700">{group}</span>
          <Stars
            label={group}
            value={value[group] ?? null}
            onChange={(rating) => onChange({ ...value, [group]: rating })}
          />
        </div>
      ))}
    </div>
  )
}
