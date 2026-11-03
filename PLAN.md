# PapuTrain — plan aplikacji treningowej

Data powstania: 2026-11-02

## Co to za aplikacja

Webowa aplikacja na telefon (strona działająca w przeglądarce, instalowalna jak aplikacja).
Tylko jeden użytkownik: Dominik. AI (Google Gemini) generuje plan treningowy na tydzień,
na podstawie profilu, sprzętu i poprzedniego tygodnia. Plan można obejrzeć, zmodyfikować
i zatwierdzić. Po zatwierdzeniu plan jest aktywny na tydzień, można odhaczać wykonane
treningi i oceniać ćwiczenia (1-5). Przyciskiem generuje się następny tydzień.
Plan NIE przypisuje treningów do konkretnych dni kalendarzowych — na tydzień jest
N treningów do wykonania w dowolne dni, we własnym rytmie.

## Wymagania zebrane

1. Tylko dla mnie — jedno konto, login + hasło (VPS jest publiczny, więc trzeba się logować).
2. AI: Google Gemini (darmowy limit), mój klucz API trzymany na serwerze.
3. Dane na serwerze, w bazie SQLite (mała baza w jednym pliku — zero administracji).
4. Backend na moim VPS.
5. Profil treningowy: cel, liczba treningów w tygodniu i czas jednego treningu, poziom, waga/wzrost/ograniczenia zdrowotne.
6. Sprzęt: lista predefiniowanych typowych sprzętów domowych (zaznaczam "posiadam")
   + możliwość dopisania własnego sprzętu polem tekstowym (także w onboardingu).
   Wolne ciężary: osobna pozycja "Obciążenie" — po zaznaczeniu rozwija się panel,
   w którym wpisuję kolejne krążki: najpierw waga w kg, obok liczba sztuk, przycisk
   "Dodaj obciążenie"; zapisuje się to jako krótki opis tekstowy przy sprzęcie
   (np. "4×2,5 kg + 2×10 kg") i trafia do AI. Pozycja "Siłownia": zaznaczam, gdy
   trenuję na siłowni = pełny dostęp do sprzętu (wszystkie ćwiczenia wykonalne,
   AI wie o siłowni).
7. Generowanie kolejnego tygodnia: na podstawie poprzedniego planu + ocen ćwiczeń (1-5)
   + uwag do ćwiczeń + odhaczonych treningów.
8. Panel zatwierdzania: po wygenerowaniu plan jest szkicem — można go edytować ręcznie
   (usunąć pozycję, zmienić serie/powtórzenia), usunąć ćwiczenie, albo napisać AI tekstowo
   "zmień mi ten dzień" i dostać nową wersję. Dopiero przycisk zatwierdź czyni plan aktywnym.
9. Odhaczanie treningów jako wykonanych (z datą wykonania — AI widzi realny rytm).
10. Historia planów (poprzednie tygodnie można przeglądać).
11. Uwagi do ćwiczeń (np. "boli kolano przy przysiadzie") — AI bierze je pod uwagę.
12. PWA — instalowalna ikona na ekranie głównym telefonu.
13. Pierwsze uruchomienie: kreator onboardingowy — najpierw profil (parametry ciała), potem sprzęt (zwykłe pola tekstowe), potem wybór ćwiczeń; dopiero po tym aplikacja przechodzi na ekran główny.
14. Elastyczny tydzień: plan zawiera N treningów (np. 3) ponumerowanych "Trening 1, 2, 3" — BEZ przypisania do pon/wt/śr. Wykonuję je w dowolne dni; jeśli we wtorek coś wypadnie, robię trening w środę — bez poczucia spóźnienia.
15. Katalog ćwiczeń: na podstawie zaznaczonego sprzętu aplikacja sugeruje ćwiczenia, które mogę odhaczyć — traktowane jako preferencje, nie jako zamknięta pula. Wybór ćwiczeń jest krokiem OPCJONALNYM — nie znam się na ćwiczeniach, więc mogę go pominąć ("pomiń, niech AI wybierze") i AI zbuduje plan sam, na bazie sprzętu i profilu.
16. Zakładka "Sprzęt i ćwiczenia" dostępna zawsze, także gdy plan jest aktywny (dokupienie sprzętu, dopisanie ulubionego ćwiczenia).
17. Przycisk "Generuj następny tydzień" aktywny dopiero po odhaczeniu WSZYSTKICH treningów aktualnego planu.
18. Projekt ma być jednocześnie: narzędziem na co dzień i elementem portfolio (Python, Docker, deploy).
19. Odstępy czasowe w planie: przerwa między seriami przy każdym ćwiczeniu (np. 90 s) i przerwa między ćwiczeniami na poziomie treningu. Progresja może dotyczyć także CZASU — AI skraca przerwy, gdy ćwiczenia oceniam jako łatwe, i wydłuża, gdy trudne.
20. Stoper podczas aktywnego treningu: włączam go RAZ na początku treningu i leci cały czas, bez żadnych przycisków do naciskania przy ćwiczeniach czy seriah — zero klikania w trakcie. Czas cały czas przed oczami: pływający pasek na dole ekranu (widoczny na każdej zakładce) + osobna zakładka "Stoper" z dużym zegarem (start/stop/reset). Przerwy z planu są tylko INFORMACJĄ tekstową ("przerwa 90 s") — sam czytam czas ze stopera, żadnych timerów odliczających i dźwięków.

## Stack technologii

| Warstwa | Technologia | Co to jest (wyjaśnienie) |
|---|---|---|
| Backend | Python 3.12 + FastAPI | Framework do budowania API (serwis, który odpowiada na zapytania HTTP) |
| Baza danych | SQLite + SQLModel | SQLModel łączy bazę z modelem danych w Pythonie; autorstwa twórcy FastAPI |
| Frontend | React + Vite (JavaScript) | Biblioteka do interfejsu + narzędzie do budowania projektu |
| Style | Tailwind CSS | Gotowe klasy CSS — szybko wychodzi ładny wygląd na telefon |
| AI | Gemini API (model Flash) | Darmowy limit dzienny; klucz w pliku .env na serwerze |
| Logowanie | JWT (token) + bcrypt | Token to podpisany bilet, który przeglądarka wysyła przy każdym zapytaniu; bcrypt to bezpieczne haszowanie haseł |
| Deploy | Docker + docker-compose + Nginx + HTTPS (certbot) | Kontenery (paczki z aplikacją), Nginx jako brama przekazująca ruch, certbot = darmowy certyfikat HTTPS |

## Struktura danych (tabele w bazie)

- **profile** — jeden rekord: cel, poziom, treningi_w_tygodniu, czas_treningu_min, waga, wzrost, ograniczenia.
- **equipment** — nazwa, typ (predefiniowany / własny), czy_posiadany (bool), szczegóły
  (opcjonalny tekst, np. "4×2,5 kg + 2×10 kg" dla pozycji "Obciążenie"). Pozycja
  "Siłownia" rozpoznawana po nazwie: jej posiadanie = pełny dostęp do sprzętu.
- **exercise_catalog** — nazwa_ćwiczenia, potrzebny_sprzęt (lista nazw sprzętu), czy_wybrane (zaznaczone przeze mnie jako "pasuje"), moja_ocena (1-5, null = nieocenione), źródło (wbudowane / AI / własne). Wbudowany katalog (ok. 80-100 ćwiczeń z przypisanym sprzętem) generuje raz Gemini na etapie budowy aplikacji i trafia do pliku JSON w kodzie. Ćwiczenia zasugerowane przez AI w planach ZAPISUJĄ SIĘ AUTOMATYCZNIE do katalogu (źródło: AI) — katalog rośnie z każdym tygodniem i jest wysyłany do AI przy kolejnych generowaniach, żeby AI nie wymyślał nazw od zera (mniejszy koszt zapytań, spójna nazwa ćwiczenia).
- **plans** — id, data_startu_tygdnia, status (draft / active / archived), numer_tygodnia, tytuł_tygodnia i notatka_trenera (z odpowiedzi AI), uwagi_od_użytkownika.
- **workouts** (treningi w planie) — id, plan_id, numer_treningu (1, 2, 3...), nazwa_treningu (np. "Trening A — góra ciała"), przerwa_miedzy_cwiczeniami_s (sekundy, opcjonalna), czy_zrobiony (bool), data_wykonania (opcjonalna). Brak pola "dzień tygodnia" — trening wykonywany w dowolnym dniu.
- **exercises** — id, workout_id, nazwa, serie, powtórzenia, przerwa_miedzy_seriami_s (sekundy), obciążenie/opis, ocena (1-5, null = brak — to ocena WYKONANIA w danym tygodniu, nie mylić z oceną preferencji w exercise_catalog), uwaga (tekst).

## Format odpowiedzi AI

Gemini ma zwracać TYLKO JSON (wymuszony tryb JSON w API) o strukturze:

```json
{
  "week_title": "Tydzień 3",
  "workouts": [
    {
      "workout_name": "Trening A — góra ciała",
      "rest_between_exercises": 60,
      "exercises": [
        {"name": "Pompki", "sets": 4, "reps": "8-12", "rest_between_sets": 90, "notes": "tempo wolne na zejściu"}
      ]
    }
  ],
  "coach_note": "Krótka uwaga trenera na ten tydzień"
}
```

Czasy przerw podawane w sekundach.

Serwer waliduje JSON (pydantic) i zapisuje jako draft. AI nigdy nie pisze bezpośrednio do bazy jako "aktywny" — zawsze przez draft + zatwierdzenie.

AI komponuje plan z ćwiczeń odhaczonych w katalogu (czy_wybrane — traktuje je jako preferencje) oraz może DODAWAĆ WŁASNE sugestie, ale tylko ćwiczenia wykonalne w moich warunkach: bez sprzętu (masa własnego ciała), z domowym sprzętem zastępczym (stół, krzesło, ściana, podłoga) lub z posiadanego sprzętu. Żadnych ćwiczeń wymagających sprzętu, którego nie mam (maszyny, siłownia, sztanga olimpijska itd.). Preferuje ćwiczenia z wysoką oceną w katalogu, pomija ocenione nisko. Każde nowe ćwiczenie użyte w planie serwer zapisuje do katalogu ze źródłem "AI".

## Ekrany aplikacji (React)

1. **Logowanie** — login + hasło.
2. **Onboarding (tylko przy pierwszym uruchomieniu, gdy nie ma profilu ani aktywnego planu)** — kreator trzech kroków: profil (parametry ciała) → sprzęt (lista "posiadam" + dopisywanie własnego + panel "Obciążenie") → ćwiczenia (sugestie możliwe do wykonania z mojego sprzętu, odhaczam te, które mi pasują — krok opcjonalny, można pominąć). Po zakończeniu kreator się nie pokazuje.
3. **Sprzęt i ćwiczenia** — dostępna zawsze z menu, dwie zakładki: **Sprzęt** (lista "posiadam" + dopisywanie własnego + panel "Obciążenie") i **Ćwiczenia** (katalog: oceniam ćwiczenia 1-5, zaznaczam "pasuje / nie pasuje", dopisuję własne; ćwiczenia zasugerowane przez AI mają etykietę "od AI"). Oceny z katalogu są brane pod uwagę przy generowaniu planów.
4. **Aktywny plan (ekran główny)** — numerowane treningi jako sekcje ("Trening 1", "Trening 2"...), bez dni kalendarzowych; przy odhaczonym treningu widać datę wykonania; każde ćwiczenie:
   nazwa, serie x powtórzenia, przerwa między seriami (np. "przerwa 90 s" — tylko informacja), uwaga; akcje: edytuj, usuń, ocena 1-5 (gwiazdki), pole uwagi;
   na dole treningu: checkbox "trening zrobiony"; na dole ekranu: przycisk "Generuj następny tydzień" (nieaktywny, dopóki nie odhaczę wszystkich treningów);
   podczas aktywnego treningu na dole ekranu PŁYWAJĄCY PASEK ze stoperem — widoczny cały czas na każdym ekranie aplikacji (klik otwiera pełny stoper).
5. **Stoper (zakładka)** — duży zegar: start / stop / reset. Włączam raz, czas leci przez cały trening, niezależnie od przechodzenia po ekranach. Otwierany też jednym kliknięciem z pływającego paska.
6. **Draft / panel zatwierdzania** — pokazuje wygenerowany plan z oznaczeniem "szkic";
   akcje: zatwierdź, edytuj ręcznie, dla każdego treningu przycisk "poproś AI o zmianę" (pole tekstowe),
   odrzuć i wygeneruj od nowa.
7. **Historia** — lista archiwalnych planów, kliknięcie pokazuje pełny plan.

## Przepływ generowania kolejnego tygodnia

1. Warunek startowy: wszystkie treningi aktualnego planu odhaczone jako wykonane. Jeśli nie — przycisk "Generuj następny tydzień" jest nieaktywny z podpowiedzią "odhacz wszystkie treningi".
2. Klikam "Generuj następny tydzień".
3. Backend zbiera: profil + sprzęt (posiadany) + katalog ćwiczeń z ocenami 1-5 i zaznaczeniami "pasuje" + ostatni aktywny plan + oceny wykonania 1-5 + uwagi + odhaczone treningi (z datami wykonania — AI widzi realny rytm).
4. Buduje prompt (instrukcję dla AI) i wysyła do Gemini. Twarde zasady w instrukcji: (a) używać WYŁĄCZNIE ćwiczeń bez sprzętu, z domowymi zamiennikami (stół, krzesło, ściana, podłoga) lub z posiadanego sprzętu; (b) NIE przypisywać treningów do dni kalendarzowych — N treningów ponumerowanych do wykonania w dowolne dni tygodnia; (c) zawsze podawać przerwy między seriami i między ćwiczeniami; progresja może polegać także na skróceniu/wydłużeniu przerw (krótsze przerwy gdy ćwiczenia łatwe, dłuższe gdy trudne).
5. Gemini zwraca JSON → walidacja → zapis jako draft → nowe ćwiczenia (nieznane w katalogu) dopisują się do katalogu ze źródłem "AI".
6. Ja oglądam draft, ewentualnie edytuję / proszę AI o poprawki.
7. Klikam "Zatwierdź" → draft staje się planem aktywnym, stary plan przechodzi do archiwum.

## Etapy prac

Tryb pracy: Dominik podejmuje decyzje projektowe (co i jak ma działać), Claude pisze kod i krótko tłumaczy, co zrobił i dlaczego.

Każdy etap kończy się czymś, co działa — nie idziemy dalej, dopóki poprzedni krok nie jest zrobiony.

- **Etap 0 — fundament:** repo git, venv (izolowane środowisko Pythona), FastAPI z jednym endpointem "/hello", pierwszy commit.
- **Etap 1 — baza i modele:** SQLModel, tabele profile/equipment/exercise_catalog/plans/workouts/exercises, wbudowany katalog ćwiczeń (JSON), endpointy CRUD (create/read/update/delete) dla profilu, sprzętu i katalogu ćwiczeń.
- **Etap 2 — logowanie:** login + hasło w bazie (bcrypt), endpoint logowania zwracający JWT, ochrona pozostałych endpointów.
- **Etap 3 — frontend szkielet:** projekt React+Vite+Tailwind, ekran logowania, wywołanie API, przechowywanie tokena.
- **Etap 4 — onboarding i konfiguracja w UI:** kreator pierwszego uruchomienia (profil → sprzęt z panelem "Obciążenie" i opcją "Siłownia" → wybór ćwiczeń), zakładka "Sprzęt i ćwiczenia" dostępna zawsze, sugestie ćwiczeń wg sprzętu (przy "Siłowni" — wszystkie).
- **Etap 5 — integracja Gemini:** klucz w .env, budowa prompta z profilu, sprzętu (razem ze szczegółami obciążenia, np. "4×2,5 kg"; "Siłownia" = pełny dostęp) i odhaczonych ćwiczeń (plus zasady: "tylko ćwiczenia wykonalne w domu / z moim sprzętem" i "bez przypisywania do dni kalendarzowych"), generowanie draftu, walidacja JSON.
- **Etap 6 — panel draftu:** wyświetlanie szkicu, edycja ręczna, usuwanie pozycji, "poproś AI o zmianę" per trening, zatwierdzanie.
- **Etap 7 — progresja i trening na żywo:** odhaczanie treningów (z datą wykonania), oceny wykonania 1-5 w planie, uwagi do ćwiczeń, przerwy między seriami/ćwiczeniami widoczne w planie (jako informacja), zakładka "Ćwiczenia" z ocenami preferencji 1-5 w katalogu, blokada przycisku "Generuj następny tydzień" do czasu odhaczenia wszystkich treningów, generowanie z uwzględnieniem całej historii, zakładka "Stoper" (start/stop/reset) + pływający pasek stopera widoczny cały czas podczas treningu.
- **Etap 8 — historia:** lista archiwalnych planów + widok szczegółów.
- **Etap 9 — PWA:** manifest + ikony + instalacja na telefon.
- **Etap 10 — deploy na VPS:** Dockerfile dla backendu i frontendu, docker-compose, Nginx jako reverse proxy (brama przekazująca ruch z portu 443 do aplikacji), HTTPS przez certbot.

## Decyzje domyślne (do podważenia w każdej chwili)

- JavaScript bez TypeScript na start (mniej nauki naraz; TS można dodać później).
- SQLModel zamiast czystego SQLAlchemy (prostszy zapis, spójny z FastAPI).
- Model Gemini: łańcuch fallbacku (limit darmowy jest dzienny per model — po wyczerpaniu
  backend sam przechodzi na kolejny): gemini-3.6-flash → gemini-3-flash-preview →
  gemini-3.5-flash-lite → gemini-3.1-flash-lite. Lista konfigurowalna w .env (GEMINI_MODELS).
- Na VPS: aplikacja pod własną subdomeną/domeną z HTTPS; bez domeny — dostęp po IP + port, ale wtedy certyfikat jest trudniejszy.
