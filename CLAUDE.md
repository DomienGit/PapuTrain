# PapuTrain

Webowa aplikacja treningowa na telefon (PWA) — AI generuje plan na tydzień na podstawie
profilu i sprzętu użytkownika, plan można modyfikować i zatwierdzać, treningi odhaczać
i oceniać. Jeden użytkownik: Dominik.

**Źródło prawdy dla funkcji i architektury: `PLAN.md`.** Zanim zaczniesz pracę nad funkcją,
przeczytaj odpowiednią sekcję PLAN.md. Gdy Dominik zmienia wymagania — najpierw zaktualizuj
PLAN.md, potem pisz kod.

## Tryb pracy

- **Dominik jest architektem** — podejmuje decyzje produktowe: co aplikacja robi, jak działa, jak wygląda.
- **Claude pisze kod** — tworzy aplikację i przy każdym większym kawałku KRÓTKO tłumaczy, co zrobił i dlaczego (Dominik uczy się Pythona i DevOps od zera).
- Decyzje implementacyjne w granicach PLAN.md podejmuj sam. Gdy pomysł wykracza poza PLAN.md albo zmienia ustaloną funkcję — zatrzymaj się i zapytaj.
- Nie zakładaj wiedzy Dominika — lepiej wyjaśnić, niż założyć.

## Komunikacja

- Po polsku. Cytaty z błędów/dokumentacji po angielsku zawsze objaśnij po polsku.
- Krótko i konkretnie, bez rozpisywania się bez potrzeby.
- Żargon (IaC, webhook, idempotentność...) wyjaśnij jednym zdaniem przy pierwszym użyciu.

## Proces

- Pracujemy etapami z sekcji "Etapy prac" w PLAN.md, po kolei. Etap kończy się kodem, który DZIAŁA (przetestowany uruchomieniem) + commitem.
- Nie zaczynaj kolejnego etapu bez zamknięcia poprzedniego.
- Push na GitHub tylko na wyraźną prośbę Dominika.
- Jeśli coś w PLAN.md okazuje się niepraktyczne w kodzie — zgłoś i zaproponuj zmianę planu, zanim ją zrobisz.

## Stack (szczegóły i uzasadnienia: PLAN.md)

- Backend: Python 3.12, FastAPI, SQLModel, SQLite (plik bazy w repożytorium serwera, nie w git), pydantic do walidacji.
- Frontend: React + Vite, JavaScript (bez TypeScript na start), Tailwind CSS, folder `frontend/`.
- AI: Google Gemini (model Flash), klucz API w `.env` — `.env` NIGDY nie trafia do repo (gitignore).
- Logowanie: JWT + bcrypt.
- Deploy docelowy: Docker + docker-compose + Nginx + certbot na VPS Dominika (Etap 10).

## Konwencje

- Teksty w UI aplikacji po polsku (aplikacja dla Dominika). Nazwy zmiennych, kod, komunikaty commitów po angielsku (standard branżowy, ważne dla portfolio).
- Commity: krótki, opisowy komunikat; jeden etap = jeden lub kilka sensownych commitów, nie jeden gigantyczny.
- Zależności backendu: `requirements.txt`. Zależności frontendu: `npm` (package-lock w repo).
- Środowisko Pythona: `venv` w katalogu `.venv` (gitignore).

## Stan projektu

- Repo na GitHub: `DomienGit/PapuTrain` (branch `main`), skonfigurowane remote.
- Zrobione: PLAN.md (pełna specyfikacja), Etap 0 (szkielet FastAPI), Etap 1 (baza SQLModel, 6 tabel, katalog ćwiczeń JSON, CRUD: profil/sprzęt/katalog), Etap 2 (logowanie JWT + bcrypt, ochrona /api, skrypt `python -m app.create_user`), Etap 3 (frontend: React+Vite+Tailwind w `frontend/`, ekran logowania, token w localStorage, proxy `/api` w vite.config.js), Etap 4 (onboarding 3 kroki, zakładka "Sprzęt i ćwiczenia", panel "Obciążenie" z krążkami, flaga "Siłownia"; przetestowane na poziomie API i builda — kliki Dominika do potwierdzenia), Etap 5 (Gemini generuje draft planu: prompt z profilu/sprzętu/katalogu, walidacja JSON, zapis do bazy, endpointy generate/draft/active; fallback modeli z .env GEMINI_MODELS przy wyczerpaniu darmowego limitu + do 3 ponowień tego samego modelu przy przeciążeniu; klucz w .env; przetestowane NA ŻYWO — plan wygenerowany w ~3,5 s), Etap 6 (panel szkicu: zatwierdzenie draft→active ze zarchiwizowaniem starego, odrzucenie, ręczna edycja treningu/ćwiczeń (PATCH/DELETE), "poproś AI o zmianę" per trening na żywo; frontend DraftPanel.jsx; edycja tylko w statusie draft), Etap 7 (trening na żywo: odhaczanie treningów z datą wykonania, oceny wykonania 1-5 i uwagi do ćwiczeń w aktywnym planie, blokada "Generuj następny tydzień" do odhaczenia wszystkich, generowanie z HISTORIĄ poprzedniego planu w promptcie (wykonania, oceny, uwagi, daty + zasada progresji), zakładka Stoper (start/stop/reset, stan w App.jsx) + pływający pasek na każdej zakładce, gwiazdki preferencji 1-5 w katalogu; wspólne gwiazdki: components/Stars.jsx), Etap 8 (historia: GET /api/plans/archived + /archived/{id}, zakładka "Historia" — lista archiwalnych planów i pełny widok read-only; etykieta zakładki skrócona do "Sprzęt"), Etap 9 (PWA: public/manifest.json + ikony generowane skryptem frontend/scripts/generate_icons.py (Pillow, tylko narzędzie — nie w requirements.txt); meta tagi w index.html; brak service workera — na iPhonie instalacja pełna, na Androidzie możliwy skrót zamiast aplikacji), Etap 10 (deploy: https://paputrain.duckdns.org — subdomena DuckDNS → VPS; 3 kontenery: backend (uvicorn), frontend (nginx, statyczne pliki z builda Vite), caddy (TLS Let's Encrypt automatycznie, reverse proxy /api→backend, reszta→frontend); baza SQLite w volume ./data na VPS, ścieżka przez env PAPUTRAIN_DB; .env tylko na serwerze (JWT_SECRET + GEMINI_API_KEY); PWA ZAINSTALOWANA na telefonie Dominika i przetestowana na żywo).
- Następny: brak — wszystkie etapy PLAN.md zamknięte. Aktualizacja produkcji: rsync kodu (bez .git/.venv/node_modules/.env/data — wzorzec `/data` z kotwicą, żeby nie wyciąć app/data! także: frontend/dist, frontend/scripts, SECURITY_FIXES.md) na root@82.165.71.51:/opt/paputrain + `docker compose up -d --build`; po zmianie .env wymagane odtworzenie kontenera (`up -d`, nie sam `restart`). PUŁAPKI DEPLOYU (2026-11-04): (1) Caddyfile jest bind-mountem POJEDYNCZEGO pliku — rsync podmienia inode, więc kontener caddy widzi stary plik; po każdej zmianie Caddyfile konieczny `docker compose restart caddy` (sam `caddy reload` przeczyta stary plik); (2) backend w kontenerze działa jako appuser uid 1000 — `/opt/paputrain/data` musi mieć uid 1000 (na VPS to user `deploy`): `chown -R 1000:1000 /opt/paputrain/data` (jednorazowo zrobione 2026-11-04; ryzyko tylko gdyby katalog odtworzono od zera jako root).
- Zabezpieczenia (2026-11-04, review): slowapi 5 logowań/min (429), wyrównanie czasu odpowiedzi loginu (dummy bcrypt), wyłączone /docs+/openapi.json, błędy Gemini tylko do logów + max_output_tokens 4096, nagłówki HSTS/nosniff/X-Frame-Options/Referrer-Policy w Caddy, kontener backendu jako appuser (uid 1000). "Zrobiłem" (req 21): exercises.performed (faktyczne serie×powtórzenia z placeholderem sugestii AI), AI proponuje obciążenia w kg (load) — historia w promptcie kalibruje progresję na bazie sugestia-vs-fakt; migracja kolumny performed automatyczna w init_db.
- Uwaga środowiskowa: `.venv` budować na Pythonie 3.12 (na 3.14 sqlmodel 0.0.24 się wysypuje; lokalnie używamy `uv venv --python 3.12`).
