/**
 * Powiadomienie o błędzie przyklejone do dołu ekranu (req 30) — nie przewija się
 * z treścią. Siedzi nad dolną nawigacją; gdy widać pływający pasek stopera,
 * App.jsx podnosi je wyżej przez zmienną CSS --toast-bottom.
 * Znika po kliknięciu × albo gdy ekran wyczyści błąd (np. przy kolejnej próbie).
 */
export default function ErrorToast({ message, onClose }) {
  if (!message) return null
  return (
    <div
      role="alert"
      className="fixed inset-x-4 bottom-[var(--toast-bottom,1rem)] z-20 mx-auto flex max-w-md items-start gap-2 rounded-xl bg-red-600 px-4 py-3 text-sm text-white shadow-lg"
    >
      <p className="flex-1">{message}</p>
      <button
        type="button"
        onClick={onClose}
        aria-label="Zamknij"
        className="-my-1 -mr-2 rounded-md px-2 py-1 text-lg leading-none text-red-100 hover:bg-red-500"
      >
        ×
      </button>
    </div>
  )
}
