import { Component } from 'react'

/**
 * Siatka bezpieczeństwa: gdy gdziekolwiek w aplikacji wybuchnie błąd w czasie
 * działania, React zamontowałby PUSTĄ STRONĘ ("biały ekran", patrz bug z
 * casefold). Ten komponent łapie taki błąd i pokazuje komunikat + przycisk
 * odświeżenia, zamiast zostawiać użytkownika na czarno-białej pustce.
 */
export default class ErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-dvh flex-col items-center justify-center bg-zinc-100 px-6 text-center">
          <h1 className="text-lg font-bold text-zinc-900">Ups, coś się zepsuło</h1>
          <p className="mt-2 max-w-sm text-sm text-zinc-500">
            Wystąpił błąd w aplikacji. Odśwież stronę — jeśli nie pomoże, daj znać Dominikowi:
          </p>
          <pre className="mt-3 max-w-full overflow-x-auto rounded-lg bg-white p-3 text-left text-xs text-red-600">
            {String(this.state.error)}
          </pre>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 rounded-lg bg-zinc-900 px-6 py-2.5 font-medium text-white hover:bg-zinc-700"
          >
            Odśwież
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
