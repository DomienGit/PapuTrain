/**
 * Gwiazdki 1-5 używane w dwóch miejscach (PLAN.md Etap 7):
 * - ocena preferencji ćwiczenia w katalogu (zakładka "Ćwiczenia"),
 * - ocena WYKONANIA ćwiczenia w aktywnym planie.
 * Klik na gwiazdkę ustawia ocenę; onChange dostaje numer 1-5.
 */
export default function Stars({ value, onChange, label = 'ocena' }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          onClick={() => onChange(n)}
          aria-label={`${label}: ${n} z 5`}
          className={`text-lg leading-none transition-colors ${
            value != null && n <= value ? 'text-amber-400' : 'text-zinc-300'
          } hover:text-amber-300`}
        >
          ★
        </button>
      ))}
    </div>
  )
}
