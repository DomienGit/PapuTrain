"""Rozmowa z Gemini: budowa promptu i generowanie planu tygodnia (Etap 5).

Prompt budujemy po polsku (odpowiedź AI też ma być po polsku — tak wymagają
teksty w UI). Twarde zasady dla AI pochodzą wprost z PLAN.md.
"""

import json
import logging
import re
import time

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.config import settings
from app.models import CatalogExercise, Equipment, Profile

logger = logging.getLogger(__name__)

# Przy przeciążeniu (5xx/timeout) powtarzamy TEN SAM model do tej liczby prób,
# z pauzą — bywa, że chmura "dopisze" za chwilę. Limit dzienny (429) i nieosiągalny
# model (404) nie mają sensu ponawiać — od razu bierzemy kolejny z listy.
ATTEMPTS_PER_MODEL = 3
RETRY_PAUSE_S = 3

GYM_NAME = "siłownia"  # rozpoznawana po nazwie (spójnie z frontendem)
HOME_SUBSTITUTES = "stół, krzesło, ściana, podłoga"


class AiError(Exception):
    """Błąd generowania planu — komunikat gotowy do wyświetlenia w UI."""


def _status_code(err: Exception) -> int | None:
    """Wyciąga kod HTTP z wyjątku SDK (atrybut .code albo z tekstu błędu)."""
    code = getattr(err, "code", None)
    if isinstance(code, int):
        return code
    match = re.search(r"\b([45]\d\d)\b", str(err))
    return int(match.group(1)) if match else None


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
    """Wysyła prompt do Gemini i zwraca sparsowany JSON.

    Darmowy limit (free tier) jest dzienny PER MODEL, więc przy odmowie
    (limit 429, przeciążenie 5xx, nieosiągalny 404, timeout) próbujemy
    kolejny model z listy GEMINI_MODELS.
    """
    if not settings.gemini_api_key:
        raise AiError("Brak klucza GEMINI_API_KEY w pliku .env — dodaj go i zrestartuj serwer")

    # UWAGA: timeout w google-genai jest w MILISEKUNDACH (90000 = 90 s).
    client = genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(timeout=90000),
    )

    problems: list[str] = []
    for model in settings.gemini_models_list:
        for attempt in range(1, ATTEMPTS_PER_MODEL + 1):
            start = time.monotonic()
            try:
                logger.info("Gemini: pytam model %s (próba %d/%d)", model, attempt, ATTEMPTS_PER_MODEL)
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",  # wymuszony tryb JSON
                        temperature=0.7,
                    ),
                )
            except (genai_errors.ClientError, genai_errors.ServerError) as err:
                code = _status_code(err)
                if code == 429 or code == 404:
                    # limit dzienny / model nieosiągalny — ponawianie nic nie da
                    logger.warning("Gemini: %s odmówił (HTTP %s) — następny model", model, code)
                    problems.append(f"{model} (HTTP {code})")
                    break
                if code is not None and 500 <= code < 600:
                    if attempt < ATTEMPTS_PER_MODEL:
                        logger.warning(
                            "Gemini: %s przeciążony (HTTP %s) — ponawiam za %d s",
                            model, code, RETRY_PAUSE_S,
                        )
                        time.sleep(RETRY_PAUSE_S)
                        continue
                    logger.warning("Gemini: %s nadal przeciążony po %d próbach — następny model", model, attempt)
                    problems.append(f"{model} (HTTP {code})")
                    break
                # 401/403 (zły klucz) czy 400 (złe zapytanie) — zmiana modelu nie pomoże
                raise AiError(f"Gemini odrzucił zapytanie (HTTP {code}): {err}") from err
            except httpx.HTTPError as err:
                # np. timeout — model przyjęty, ale nie odpowiada (widzieliśmy to na 3.8-flash)
                if attempt < ATTEMPTS_PER_MODEL:
                    logger.warning(
                        "Gemini: %s nie odpowiedział (%s) — ponawiam za %d s",
                        model, type(err).__name__, RETRY_PAUSE_S,
                    )
                    time.sleep(RETRY_PAUSE_S)
                    continue
                logger.warning("Gemini: %s nadal nie odpowiada po %d próbach — następny model", model, attempt)
                problems.append(f"{model} (brak odpowiedzi)")
                break

            elapsed = time.monotonic() - start
            text = (response.text or "").strip()
            if not text:
                raise AiError("Gemini zwrócił pustą odpowiedź — spróbuj ponownie")
            try:
                result = json.loads(text)
            except json.JSONDecodeError as err:
                raise AiError("Gemini zwrócił odpowiedź, która nie jest poprawnym JSON-em") from err
            if attempt > 1:
                logger.info("Gemini: model %s odpowiedział dopiero przy próbie %d (łącznie %.1f s)", model, attempt, elapsed)
            else:
                logger.info("Gemini: model %s odpowiedział w %.1f s", model, elapsed)
            return result

    raise AiError(
        "Wszystkie modele wyczerpały limit albo nie odpowiadają (" + "; ".join(problems) + "). "
        "Spróbuj ponownie później."
    )
