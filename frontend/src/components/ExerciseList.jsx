import { useEffect, useState } from 'react'
import { api } from '../api'

const sourceBadge = {
  builtin: '',
  custom: 'własne',
  ai: 'od AI',
}

/**
 * Katalog ćwiczeń z flagą "pasuje mi". Wymaga propa ownedNames
 * (zbiór nazwy posiadanego sprzętu, małymi literami) — na jego podstawie
 * liczy, które ćwiczenia są wykonalne u Dominika.
 */
export default function ExerciseList({ ownedNames, allowAdd = false }) {
  const [items, setItems] = useState(null)
  const [onlyFeasible, setOnlyFeasible] = useState(true)
  const [newName, setNewName] = useState('')
  const [newEquipment, setNewEquipment] = useState('') // np. "hantle, gumy oporowe"
  const [error, setError] = useState('')

  useEffect(() => {
    api('/api/exercises')
      .then(setItems)
      .catch((err) => setError(err.message))
  }, [])

  function isFeasible(exercise) {
    if (ownedNames.has('siłownia')) return true // tryb siłowni = pełny dostęp
    return exercise.required_equipment.every((eq) => ownedNames.has(eq.casefold()))
  }

  async function toggleChosen(item) {
    setError('')
    try {
      const updated = await api(`/api/exercises/${item.id}`, {
        method: 'PUT',
        body: JSON.stringify({ chosen: !item.chosen }),
      })
      setItems(items.map((i) => (i.id === updated.id ? updated : i)))
    } catch (err) {
      setError(err.message)
    }
  }

  async function add(event) {
    event.preventDefault()
    if (!newName.trim()) return
    setError('')
    const equipment = newEquipment
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean)
    try {
      const created = await api('/api/exercises', {
        method: 'POST',
        body: JSON.stringify({ name: newName, required_equipment: equipment }),
      })
      setItems([...items, created])
      setNewName('')
      setNewEquipment('')
    } catch (err) {
      setError(err.message)
    }
  }

  if (items === null) return <p className="text-sm text-zinc-500">Ładowanie…</p>

  const visible = onlyFeasible ? items.filter(isFeasible) : items
  // Zaznaczone na górze, potem alfabetycznie.
  const sorted = [...visible].sort(
    (a, b) => Number(b.chosen) - Number(a.chosen) || a.name.localeCompare(b.name, 'pl'),
  )

  return (
    <div>
      {ownedNames.has('siłownia') && (
        <p className="mb-3 rounded-lg bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
          Tryb siłowni: pokazuję cały katalog — masz pełny dostęp do sprzętu.
        </p>
      )}

      <label className="mb-3 flex items-center gap-2 text-sm text-zinc-600">
        <input
          type="checkbox"
          checked={onlyFeasible}
          onChange={(e) => setOnlyFeasible(e.target.checked)}
          className="size-4 accent-zinc-900"
        />
        Pokaż tylko możliwe z mojego sprzętu
      </label>

      {allowAdd && (
        <form onSubmit={add} className="mb-4 space-y-2">
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="nazwa ćwiczenia, np. Wykroki bułgarskie"
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-base outline-none focus:border-zinc-900"
          />
          <input
            value={newEquipment}
            onChange={(e) => setNewEquipment(e.target.value)}
            placeholder="potrzebny sprzęt, po przecinku (może być puste)"
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-base outline-none focus:border-zinc-900"
          />
          <button
            type="submit"
            className="w-full rounded-lg bg-zinc-900 py-2 text-sm font-medium text-white hover:bg-zinc-700"
          >
            Dodaj ćwiczenie
          </button>
        </form>
      )}

      {error && (
        <p className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
      )}

      {sorted.length === 0 ? (
        <p className="rounded-xl bg-white p-4 text-center text-sm text-zinc-500 shadow-sm">
          Nic tu nie ma. Zaznacz sprzęt w zakładce „Sprzęt” albo odznacz filtr.
        </p>
      ) : (
        <ul className="divide-y divide-zinc-100 rounded-xl bg-white shadow-sm">
          {sorted.map((item) => (
            <li key={item.id} className="px-4 py-3">
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={item.chosen}
                  onChange={() => toggleChosen(item)}
                  className="size-5 accent-zinc-900"
                  aria-label={`Pasuje mi: ${item.name}`}
                />
                <span className="min-w-0 flex-1 truncate text-zinc-900">{item.name}</span>
                {sourceBadge[item.source] && (
                  <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-500">
                    {sourceBadge[item.source]}
                  </span>
                )}
              </div>
              {item.required_equipment.length > 0 && (
                <p className="mt-1 pl-8 text-xs text-zinc-500">
                  sprzęt: {item.required_equipment.join(', ')}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
