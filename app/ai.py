"""Rozmowa z Gemini: budowa promptu i generowanie planu tygodnia (Etap 5).

Prompt budujemy po polsku (odpowiedź AI też ma być po polsku — tak wymagają
teksty w UI). Twarde zasady dla AI pochodzą wprost z PLAN.md.
"""

import json

from google import genai
from google.genai import types

from app.config import settings
from app.models import CatalogExercise, Equipment, Profile

GYM_NAME = "siłownia"  # rozpoznawana po nazwie (spójnie z frontendem)
HOME_SUBSTITUTES = "stół, krzesło, ściana, podłoga"


class AiError(Exception):
    """Błąd generowania planu — komunikat gotowy do wyświetlenia w UI."""


def _has_gym(equipment: list[Equipment]) -> bool:
    return any(eq.name.casefold() == GYM_NAME for eq in equipment)


def _equipment_lines(equipment: list[Equipment]) -> list[str]:
    lines = []
    for eq in sorted(equipment, key=lambda e: e.name.casefold()):
        if eq.name.casefold() == GYM_NAME:
            continue
        lines.append(f"- {eq.name}" + (f" ({eq.details})" if eq.details else ""))
    return lines


def _catalog_lines(catalog: list[CatalogExercise]) -> list[str]:
    lines = []
    for ex in sorted(catalog, key=lambda e: e.name.casefold()):
        flags = []
        if ex.chosen:
            flags.append("wybrane przeze mnie")
        if ex.preference_rating is not None:
            flags.append(f"moja ocena preferencji: {ex.preference_rating}/5")
        suffix = f" [{'; '.join(flags)}]" if flags else ""
        equipment_note = (
            f", sprzęt: {', '.join(ex.required_equipment)}" if ex.required_equipment else ""
        )
        lines.append(f"- {ex.name}{equipment_note}{suffix}")
    return lines


def build_generation_prompt(
    profile: Profile,
    equipment: list[Equipment],
    catalog: list[CatalogExercise],
    week_number: int,
) -> str:
    """Składa instrukcję dla Gemini z profilu, sprzętu i katalogu ćwiczeń."""
    gym = _has_gym(equipment)
    body = [
        "Jesteś doświadczonym trenerem personalnym. Ułóż plan treningowy na jeden tydzień.",
        "",
        "PROFIL OSOBY:",
        f"- cel: {profile.goal}",
        f"- poziom zaawansowania: {profile.level}",
        f"- liczba treningów w tygodniu: {profile.workouts_per_week}",
        f"- maksymalny czas jednego treningu: {profile.workout_duration_min} minut",
    ]
    if profile.weight_kg or profile.height_cm:
        body.append(
            f"- waga/wzrost: {profile.weight_kg or '?'} kg / {profile.height_cm or '?'} cm"
        )
    if profile.limitations:
        body.append(f"- ograniczenia zdrowotne: {profile.limitations}")

    body.append("")
    body.append("DOSTĘPNY SPRZĘT:")
    eq_lines = _equipment_lines(equipment)
    if gym:
        body.append("- PEŁNY DOSTĘP DO SIŁOWNI (wszystkie maszyny, sztangi, półki itd.)")
    if eq_lines:
        body.extend(eq_lines)
    if not eq_lines and not gym:
        body.append("- brak — tylko masa własnego ciała")
    body.append(f"- zawsze dozwolone: masa własnego ciała i domowe zamienniki ({HOME_SUBSTITUTES})")

    body.append("")
    body.append("KATALOG ĆWICZEŃ (moje preferencje):")
    cat_lines = _catalog_lines(catalog)
    body.extend(cat_lines if cat_lines else "- (katalog pusty — zaproponuj sam)")

    body.extend(
        [
            "",
            "TWARDE ZASADY:",
            f"1. Wygeneruj DOKŁADNIE {profile.workouts_per_week} treningów ponumerowanych "
            '"Trening 1", "Trening 2" itd. — BEZ przypisywania do dni tygodnia.',
            "2. Używaj WYŁĄCZNIE ćwiczeń wykonalnych bez sprzętu, z domowymi zamiennikami "
            "lub z podanego sprzętu. Żadnych maszyn ani sztang olimpijskich, jeśli nie ma "
            "pełnego dostępu do siłowni.",
            "3. Każdy trening powinien dać się wykonać w podanym czasie.",
            "4. ZAWSZE podawaj przerwy między seriami i między ćwiczeniami (w sekundach). "
            "Progresja może polegać także na skróceniu przerw (ćwiczenia za łatwe) "
            "lub ich wydłużeniu (za trudne).",
            "5. Ćwiczenia ocenione 4-5/5 preferuj, ocenione 1-2/5 pomiń. Ćwiczenia wybrane "
            "traktuj jako preferencje — resztę dobierz tak, żeby plan był sensowny całościowo.",
            "6. Respektuj ograniczenia zdrowotne — nie proponuj ćwiczeń, które mogą szkodzić.",
            f"7. Tytuł tygodnia: \"Tydzień {week_number}\".",
            "8. Wszystkie teksty (nazwy treningów, uwagi, notatka trenera) po polsku.",
            "",
            "ODPOWIEDŹ: zwróć WYŁĄCZNIE poprawny JSON (bez komentarzy i markdown) "
            "dokładnie w tej strukturze:",
            """{
  "week_title": "Tydzień 1",
  "workouts": [
    {
      "workout_name": "Trening 1 — góra ciała",
      "rest_between_exercises": 60,
      "exercises": [
        {"name": "Pompki", "sets": 4, "reps": "8-12", "rest_between_sets": 90,
         "notes": "tempo wolne na zejściu"}
      ]
    }
  ],
  "coach_note": "Krótka uwaga trenera na ten tydzień"
}""",
        ]
    )
    return "\n".join(body)


def generate_plan(prompt: str) -> dict:
    """Wysyła prompt do Gemini i zwraca sparsowany JSON. Rzuca AiError, gdy coś pójdzie nie tak."""
    if not settings.gemini_api_key:
        raise AiError("Brak klucza GEMINI_API_KEY w pliku .env — dodaj go i zrestartuj serwer")

    # UWAGA: timeout w google-genai jest w MILISEKUNDACH (90000 = 90 s).
    # Bez jawnego timeoutu zapytanie potrafi wisieć bardzo długo.
    client = genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(timeout=90000),
    )
    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",  # wymuszony tryb JSON
                temperature=0.7,
            ),
        )
    except Exception as err:
        raise AiError(f"Nie udało się połączyć z Gemini: {err}") from err

    text = (response.text or "").strip()
    if not text:
        raise AiError("Gemini zwrócił pustą odpowiedź — spróbuj ponownie")
    try:
        return json.loads(text)
    except json.JSONDecodeError as err:
        raise AiError("Gemini zwrócił odpowiedź, która nie jest poprawnym JSON-em") from err
