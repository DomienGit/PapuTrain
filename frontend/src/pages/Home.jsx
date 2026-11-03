/**
 * Ekran główny — na razie zapowiedź. Od Etapu 5 pokaże tu aktywny plan
 * (generowanie przez AI) i od Etapu 7 odhaczanie treningów ze stoperem.
 */
export default function Home({ username }) {
  return (
    <div className="mx-auto w-full max-w-md px-4 py-6">
      <h1 className="text-xl font-bold text-zinc-900">PapuTrain</h1>
      <div className="mt-4 rounded-2xl bg-white p-5 text-center shadow-sm">
        <p className="text-zinc-600">
          Cześć, <span className="font-semibold">{username}</span>!
        </p>
        <p className="mt-3 text-sm text-zinc-500">
          Profil i sprzęt zapisane. Generowanie planu treningowego pojawi się
          w kolejnym etapie (integracja z AI).
        </p>
      </div>
    </div>
  )
}
