import { useEffect, useState } from 'react'
import { api } from '../api'

const typeBadge = {
  predefined: 'z katalogu',
  custom: 'własny',
}

const OBciazenie = 'obciążenie' // specjalna pozycja z krążkami (rozpoznawana po nazwie)
const SILNIA = 'siłownia' // specjalna pozycja = pełny dostęp do sprzętu

/** "4×2,5 kg + 2×10 kg" -> [{count: 4, weight: 2.5}, {count: 2, weight: 10}] */
function parsePlates(details) {
  if (!details) return []
  return details.split(' + ').map((part) => {
    const match = part.trim().match(/^(\d+)×([\d,.]+) kg$/)
    return match
      ? { count: Number(match[1]), weight: Number(match[2].replace(',', '.')) }
      : null
  }).filter(Boolean)
}

/** [{count: 4, weight: 2.5}] -> "4×2,5 kg + 2×10 kg" (przecinek = polski zapis dziesiętny) */
function formatPlates(rows) {
  return rows
    .filter((r) => r.count > 0 && r.weight > 0)
    .map((r) => `${r.count}×${String(r.weight).replace('.', ',')} kg`)
    .join(' + ')
}

/**
 * Panel krążków dla pozycji "Obciążenie": wiersze waga + sztuki,
 * przycisk "Dodaj obciążenie". Każda zmiana od razu zapisuje się w API.
 */
function PlatesEditor({ item }) {
  const [rows, setRows] = useState(() => parsePlates(item.details))
  const [weight, setWeight] = useState('')
  const [count, setCount] = useState('')
  const [error, setError] = useState('')

  async function save(nextRows) {
    setRows(nextRows)
    setError('')
    try {
      await api(`/api/equipment/${item.id}`, {
        method: 'PUT',
        body: JSON.stringify({ details: formatPlates(nextRows) }),
      })
    } catch (err) {
      setError(err.message)
    }
  }

  function addRow(event) {
    event.preventDefault()
    const weightNum = Number(weight.replace(',', '.'))
    const countNum = Number(count)
    if (!weightNum || weightNum <= 0 || !countNum || countNum <= 0) {
      setError('Podaj wagę (> 0) i liczbę sztuk (> 0)')
      return
    }
    setError('')
    save([...rows, { weight: weightNum, count: countNum }])
    setWeight('')
    setCount('')
  }

  return (
    <div className="mx-4 mb-3 rounded-lg bg-zinc-50 p-3">
      {rows.length > 0 && (
        <ul className="mb-2 space-y-1">
          {rows.map((row, index) => (
            <li key={index} className="flex items-center gap-2 text-sm text-zinc-700">
              <span className="flex-1">
                {row.count}×{String(row.weight).replace('.', ',')} kg
              </span>
              <button
                onClick={() => save(rows.filter((_, i) => i !== index))}
                className="text-xs text-red-500 hover:text-red-700"
              >
                Usuń
              </button>
            </li>
          ))}
        </ul>
      )}
      <form onSubmit={addRow} className="flex items-center gap-2">
        <input
          value={weight}
          onChange={(e) => setWeight(e.target.value)}
          inputMode="decimal"
          placeholder="waga kg"
          className="w-24 rounded-lg border border-zinc-300 bg-white px-2 py-1.5 text-sm outline-none focus:border-zinc-900"
        />
        <input
          value={count}
          onChange={(e) => setCount(e.target.value)}
          inputMode="numeric"
          placeholder="szt."
          className="w-16 rounded-lg border border-zinc-300 bg-white px-2 py-1.5 text-sm outline-none focus:border-zinc-900"
        />
        <button
          type="submit"
          className="rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-zinc-700"
        >
          Dodaj obciążenie
        </button>
      </form>
      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
    </div>
  )
}

/**
 * Lista sprzętu z przełącznikiem "posiadam". Sam pobiera i aktualizuje dane.
 * Pozycja "Obciążenie" po zaznaczeniu rozwija panel krążków (waga + sztuki).
 * Pozycja "Siłownia" = pełny dostęp do sprzętu (patrz ExerciseList).
 * allowAdd = pokazuje pole "dodaj własny sprzęt".
 */
export default function EquipmentList({ allowAdd = false }) {
  const [items, setItems] = useState(null) // null = trwa ładowanie
  const [newName, setNewName] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    api('/api/equipment')
      .then(setItems)
      .catch((err) => setError(err.message))
  }, [])

  async function updateItem(id, body) {
    setError('')
    try {
      return await api(`/api/equipment/${id}`, {
        method: 'PUT',
        body: JSON.stringify(body),
      })
    } catch (err) {
      setError(err.message)
      return null
    }
  }

  async function toggleOwned(item) {
    const updated = await updateItem(item.id, { owned: !item.owned })
    if (updated) setItems(items.map((i) => (i.id === updated.id ? updated : i)))
  }

  async function add(event) {
    event.preventDefault()
    if (!newName.trim()) return
    setError('')
    try {
      const created = await api('/api/equipment', {
        method: 'POST',
        body: JSON.stringify({ name: newName }),
      })
      setItems([...items, created])
      setNewName('')
    } catch (err) {
      setError(err.message)
    }
  }

  async function remove(item) {
    setError('')
    try {
      await api(`/api/equipment/${item.id}`, { method: 'DELETE' })
      setItems(items.filter((i) => i.id !== item.id))
    } catch (err) {
      setError(err.message)
    }
  }

  if (items === null) return <p className="text-sm text-zinc-500">Ładowanie…</p>

  // Posiadane na górze, potem alfabetycznie (po polsku — ą, ć, ł w dobrym miejscu).
  const sorted = [...items].sort(
    (a, b) => Number(b.owned) - Number(a.owned) || a.name.localeCompare(b.name, 'pl'),
  )

  return (
    <div>
      {allowAdd && (
        <form onSubmit={add} className="mb-4 flex gap-2">
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="np. kettlebell 16 kg"
            className="min-w-0 flex-1 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-base outline-none focus:border-zinc-900"
          />
          <button
            type="submit"
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700"
          >
            Dodaj
          </button>
        </form>
      )}

      {error && (
        <p className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
      )}

      <ul className="divide-y divide-zinc-100 rounded-xl bg-white shadow-sm">
        {sorted.map((item) => {
          const key = item.name.casefold()
          const isGym = key === SILNIA
          return (
            <li key={item.id}>
              <div className="flex items-center gap-3 px-4 py-3">
                <input
                  type="checkbox"
                  checked={item.owned}
                  onChange={() => toggleOwned(item)}
                  className="size-5 accent-zinc-900"
                  aria-label={`Posiadam: ${item.name}`}
                />
                <span className="min-w-0 flex-1 truncate text-zinc-900">
                  {item.name}
                  {item.details && (
                    <span className="block truncate text-xs text-zinc-500">{item.details}</span>
                  )}
                </span>
                <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-500">
                  {typeBadge[item.type] || item.type}
                </span>
                {item.type === 'custom' && (
                  <button
                    onClick={() => remove(item)}
                    className="text-sm text-red-500 hover:text-red-700"
                    aria-label={`Usuń: ${item.name}`}
                  >
                    Usuń
                  </button>
                )}
              </div>
              {key === OBciazenie && item.owned && <PlatesEditor item={item} />}
              {isGym && item.owned && (
                <p className="mx-4 mb-3 rounded-lg bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
                  Tryb siłowni: wszystkie ćwiczenia uznane za wykonalne.
                </p>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
