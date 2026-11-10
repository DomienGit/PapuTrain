"""Plany tygodnia: generowanie przez AI (Etap 5) i odczyt szkicu/aktywnego planu.

Panel edycji i zatwierdzania szkicu powstanie w Etapie 6 — tu tylko dane.
Zasady (PLAN.md): szkic zawsze maksymalnie jeden (nowy nadpisuje stary),
generowanie zablokowane, dopóki aktywny plan ma nieodhaczone treningi.
"""

from datetime import date

from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError
from sqlmodel import select

from app.ai import (
    AiError,
    build_generation_prompt,
    build_workout_revision_prompt,
    generate_plan,
)
from app.database import SessionDep
from app.models import CatalogExercise, Equipment, Exercise, Plan, Profile, Workout
from app.schemas import (
    AiExercise,
    AiPlan,
    AiWorkout,
    AskAiRequest,
    ExerciseFeedbackUpdate,
    ExerciseUpdate,
    WorkoutDoneUpdate,
    WorkoutUpdate,
)

router = APIRouter(prefix="/api/plans", tags=["plans"])


def _plan_to_dict(session, plan: Plan) -> dict:
    """Składa plan z treningami i ćwiczeniami w jeden zagnieżdżony słownik."""
    workouts = session.exec(
        select(Workout).where(Workout.plan_id == plan.id).order_by(Workout.number)  # type: ignore[arg-type]
    ).all()
    workouts_data = []
    for workout in workouts:
        exercises = session.exec(
            select(Exercise).where(Exercise.workout_id == workout.id).order_by(Exercise.id)  # type: ignore[arg-type]
        ).all()
        workouts_data.append(
            {
                "id": workout.id,
                "number": workout.number,
                "name": workout.name,
                "rest_between_exercises_s": workout.rest_between_exercises_s,
                "done": workout.done,
                "completed_date": workout.completed_date,
                "exercises": [
                    {
                        "id": ex.id,
                        "name": ex.name,
                        "muscle_group": ex.muscle_group,
                        "sets": ex.sets,
                        "reps": ex.reps,
                        "rest_between_sets_s": ex.rest_between_sets_s,
                        "load": ex.load,
                        "performed": ex.performed,
                        "rating": ex.rating,
                        "note": ex.note,
                    }
                    for ex in exercises
                ],
            }
        )
    return {
        "id": plan.id,
        "status": plan.status,
        "week_number": plan.week_number,
        "week_title": plan.week_title,
        "coach_note": plan.coach_note,
        "user_notes": plan.user_notes,
        "workouts": workouts_data,
    }


def _delete_plan(session, plan: Plan) -> None:
    """Usuwa plan razem z treningami i ćwiczeniami (SQLite nie ma CASCADE w SQLModel)."""
    for workout in session.exec(select(Workout).where(Workout.plan_id == plan.id)).all():
        for exercise in session.exec(select(Exercise).where(Exercise.workout_id == workout.id)).all():
            session.delete(exercise)
        session.delete(workout)
    session.delete(plan)


def _register_ai_exercises(session, workouts: list[AiWorkout]) -> None:
    """Nowe nazwy ćwiczeń od AI dopisuje do katalogu ze źródłem "ai" (PLAN.md)."""
    existing = {ex.name.casefold() for ex in session.exec(select(CatalogExercise)).all()}
    for workout in workouts:
        for exercise in workout.exercises:
            if exercise.name.casefold() not in existing:
                session.add(
                    CatalogExercise(name=exercise.name, required_equipment=[], source="ai")
                )
                existing.add(exercise.name.casefold())


def _ratings_from_catalog(catalog: list[CatalogExercise]) -> dict[str, int | None]:
    """Pamięć gwiazdek (req 24): nazwa -> ostatnia ocena wykonania."""
    return {ex.name.casefold(): ex.last_rating for ex in catalog}


def _exercise_from_ai(
    workout_id: int, data: AiExercise, ratings: dict[str, int | None]
) -> Exercise:
    """Ćwiczenie z odpowiedzi AI. Gdy nazwa jest w pamięci katalogu, gwiazdki
    wykonania startują od razu zaznaczone (req 24); nieznana nazwa = brak oceny."""
    return Exercise(
        workout_id=workout_id,
        name=data.name,
        muscle_group=data.muscle_group,
        sets=data.sets,
        reps=data.reps,
        rest_between_sets_s=data.rest_between_sets,
        load=data.load,
        note=data.notes,
        rating=ratings.get(data.name.casefold()),
    )


@router.post("/generate")
def generate_plan_endpoint(session: SessionDep) -> dict:
    active = session.exec(select(Plan).where(Plan.status == "active")).first()  # type: ignore[arg-type]
    if active is not None:
        undone = [
            w
            for w in session.exec(select(Workout).where(Workout.plan_id == active.id)).all()
            if not w.done
        ]
        if undone:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Odhacz wszystkie treningi aktywnego planu przed wygenerowaniem kolejnego",
            )

    profile = session.exec(select(Profile)).first()
    if profile is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Najpierw uzupełnij profil w kreatorze")

    # Poprzedni plan z wynikami (oceny, uwagi, daty) — AI progresuje na jego bazie.
    history = None
    if active is not None:
        workouts = session.exec(
            select(Workout).where(Workout.plan_id == active.id).order_by(Workout.number)  # type: ignore[arg-type]
        ).all()
        history = [(w, _workout_exercises(session, w)) for w in workouts]

    equipment = list(session.exec(select(Equipment).where(Equipment.owned)).all())  # type: ignore[arg-type]
    catalog = list(session.exec(select(CatalogExercise)).all())
    week_number = max((p.week_number for p in session.exec(select(Plan)).all()), default=0) + 1

    prompt = build_generation_prompt(profile, equipment, catalog, week_number, history)
    try:
        raw = generate_plan(prompt)
        plan_data = AiPlan.model_validate(raw)
    except AiError as err:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(err))
    except ValidationError as err:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"AI zwróciło plan o niepoprawnej strukturze: {err.errors()[:3]}",
        )

    # Szkic zawsze jeden: stary draft leci do kosza.
    old_draft = session.exec(select(Plan).where(Plan.status == "draft")).first()  # type: ignore[arg-type]
    if old_draft is not None:
        _delete_plan(session, old_draft)

    plan = Plan(
        status="draft",
        week_number=week_number,
        week_title=plan_data.week_title,
        coach_note=plan_data.coach_note,
    )
    session.add(plan)
    session.flush()  # flush = zapis do bazy bez kończenia transakcji; potrzebne, by mieć plan.id

    ratings = _ratings_from_catalog(catalog)
    for number, workout_data in enumerate(plan_data.workouts, start=1):
        workout = Workout(
            plan_id=plan.id,
            number=number,
            name=workout_data.workout_name,
            rest_between_exercises_s=workout_data.rest_between_exercises,
        )
        session.add(workout)
        session.flush()
        for exercise_data in workout_data.exercises:
            session.add(_exercise_from_ai(workout.id, exercise_data, ratings))

    _register_ai_exercises(session, plan_data.workouts)
    session.commit()
    return _plan_to_dict(session, plan)


@router.get("/draft")
def get_draft(session: SessionDep) -> dict:
    draft = session.exec(select(Plan).where(Plan.status == "draft")).first()  # type: ignore[arg-type]
    if draft is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Brak szkicu planu")
    return _plan_to_dict(session, draft)


@router.get("/active")
def get_active(session: SessionDep) -> dict:
    active = session.exec(select(Plan).where(Plan.status == "active")).first()  # type: ignore[arg-type]
    if active is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Brak aktywnego planu")
    return _plan_to_dict(session, active)


@router.get("/archived")
def list_archived(session: SessionDep) -> list[dict]:
    """Lista archiwalnych planów (Etap 8) — skrót, bez ćwiczeń; pełny plan osobno."""
    plans = session.exec(
        select(Plan).where(Plan.status == "archived").order_by(Plan.week_number)  # type: ignore[arg-type]
    ).all()
    result = []
    for plan in plans:
        workouts = session.exec(
            select(Workout).where(Workout.plan_id == plan.id)  # type: ignore[arg-type]
        ).all()
        result.append(
            {
                "id": plan.id,
                "week_number": plan.week_number,
                "week_title": plan.week_title,
                "workouts_total": len(workouts),
                "workouts_done": sum(1 for w in workouts if w.done),
            }
        )
    return result


@router.get("/archived/{plan_id}")
def get_archived(plan_id: int, session: SessionDep) -> dict:
    plan = session.get(Plan, plan_id)
    if plan is None or plan.status != "archived":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nie ma takiego archiwalnego planu")
    return _plan_to_dict(session, plan)


# --- Etap 6: panel szkicu (zatwierdzanie, edycja ręczna, prośba do AI) ---

# Edycja szkicu pozwala uporządkować plan PRZED zatwierdzeniem; aktywny plan
# dostaje własne akcje (odhaczanie, oceny) w Etapie 7.
def _get_draft_or_404(session) -> Plan:
    draft = session.exec(select(Plan).where(Plan.status == "draft")).first()  # type: ignore[arg-type]
    if draft is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Brak szkicu planu")
    return draft


def _get_draft_workout_or_404(session, workout_id: int) -> Workout:
    """Trening szkicu o podanym id (404, gdy nie istnieje lub należy do innego planu)."""
    workout = session.get(Workout, workout_id)
    if workout is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nie ma takiego treningu w szkicu")
    if workout.plan_id != _get_draft_or_404(session).id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ten trening nie należy do szkicu")
    return workout


def _workout_exercises(session, workout: Workout) -> list[Exercise]:
    return list(
        session.exec(select(Exercise).where(Exercise.workout_id == workout.id)).all()  # type: ignore[arg-type]
    )


@router.post("/draft/approve")
def approve_draft(session: SessionDep) -> dict:
    """Szkic staje się planem aktywnym; dotychczasowy aktywny przechodzi do archiwum."""
    draft = _get_draft_or_404(session)
    old_active = session.exec(select(Plan).where(Plan.status == "active")).first()  # type: ignore[arg-type]
    if old_active is not None:
        old_active.status = "archived"
        session.add(old_active)
    draft.status = "active"
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return _plan_to_dict(session, draft)


@router.delete("/draft")
def reject_draft(session: SessionDep) -> dict:
    """Odrzucenie szkicu — użytkownik może od razu wygenerować plan od nowa."""
    draft = _get_draft_or_404(session)
    _delete_plan(session, draft)
    session.commit()
    return {"deleted": True}


@router.patch("/draft/workouts/{workout_id}")
def update_workout(workout_id: int, data: WorkoutUpdate, session: SessionDep) -> dict:
    """Ręczna zmiana treningu w szkicu: nazwa, przerwa między ćwiczeniami."""
    workout = _get_draft_workout_or_404(session, workout_id)
    if data.name is not None:
        workout.name = data.name
    if data.rest_between_exercises_s is not None:
        workout.rest_between_exercises_s = data.rest_between_exercises_s
    session.add(workout)
    session.commit()
    return _plan_to_dict(session, session.get(Plan, workout.plan_id))


@router.patch("/draft/workouts/{workout_id}/exercises/{exercise_id}")
def update_exercise(
    workout_id: int, exercise_id: int, data: ExerciseUpdate, session: SessionDep
) -> dict:
    """Ręczna zmiana ćwiczenia w szkicu: nazwa, serie, powtórzenia, przerwy, uwagi."""
    workout = _get_draft_workout_or_404(session, workout_id)  # pilnuje, że to trening szkicu
    exercise = session.get(Exercise, exercise_id)
    if exercise is None or exercise.workout_id != workout_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nie ma takiego ćwiczenia w tym treningu")
    for field in ("name", "sets", "reps", "rest_between_sets_s", "load", "note"):
        value = getattr(data, field)
        if value is not None:
            setattr(exercise, field, value)
    session.add(exercise)
    session.commit()
    return _plan_to_dict(session, session.get(Plan, workout.plan_id))


@router.delete("/draft/workouts/{workout_id}/exercises/{exercise_id}")
def delete_exercise(workout_id: int, exercise_id: int, session: SessionDep) -> dict:
    """Usunięcie ćwiczenia ze szkicu."""
    workout = _get_draft_workout_or_404(session, workout_id)
    exercise = session.get(Exercise, exercise_id)
    if exercise is None or exercise.workout_id != workout_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nie ma takiego ćwiczenia w tym treningu")
    session.delete(exercise)
    session.commit()
    return _plan_to_dict(session, session.get(Plan, workout.plan_id))


@router.post("/draft/workouts/{workout_id}/ask-ai")
def ask_ai_to_revise_workout(workout_id: int, body: AskAiRequest, session: SessionDep) -> dict:
    """"Poproś AI o zmianę": AI przepisuje jeden trening wg tekstowej prośby."""
    workout = _get_draft_workout_or_404(session, workout_id)
    draft = session.get(Plan, workout.plan_id)

    profile = session.exec(select(Profile)).first()
    if profile is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Najpierw uzupełnij profil w kreatorze")
    equipment = list(session.exec(select(Equipment).where(Equipment.owned)).all())  # type: ignore[arg-type]
    catalog = list(session.exec(select(CatalogExercise)).all())

    all_workouts = session.exec(
        select(Workout).where(Workout.plan_id == draft.id).order_by(Workout.number)  # type: ignore[arg-type]
    ).all()
    workouts_with_exercises = [(w, _workout_exercises(session, w)) for w in all_workouts]

    prompt = build_workout_revision_prompt(
        profile, equipment, catalog, workouts_with_exercises, workout, body.request
    )
    try:
        raw = generate_plan(prompt)
        workout_data = AiWorkout.model_validate(raw)
    except AiError as err:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(err))
    except ValidationError as err:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"AI zwróciło trening o niepoprawnej strukturze: {err.errors()[:3]}",
        )

    # Stare ćwiczenia treningu lecą do kosza, wchodzą nowe od AI.
    for exercise in _workout_exercises(session, workout):
        session.delete(exercise)
    workout.name = workout_data.workout_name
    workout.rest_between_exercises_s = workout_data.rest_between_exercises
    session.add(workout)
    session.flush()
    ratings = _ratings_from_catalog(catalog)
    for exercise_data in workout_data.exercises:
        session.add(_exercise_from_ai(workout.id, exercise_data, ratings))
    _register_ai_exercises(session, [workout_data])
    session.commit()
    return _plan_to_dict(session, draft)


# --- Etap 7: trening na żywo (odhaczanie, oceny wykonania, uwagi) ---

def _get_active_or_404(session) -> Plan:
    active = session.exec(select(Plan).where(Plan.status == "active")).first()  # type: ignore[arg-type]
    if active is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Brak aktywnego planu")
    return active


def _get_active_workout_or_404(session, workout_id: int) -> Workout:
    """Trening aktywnego planu o podanym id (404, gdy nie istnieje lub cudzy plan)."""
    workout = session.get(Workout, workout_id)
    if workout is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nie ma takiego treningu")
    if workout.plan_id != _get_active_or_404(session).id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ten trening nie należy do aktywnego planu")
    return workout


@router.patch("/active/workouts/{workout_id}")
def set_workout_done(workout_id: int, data: WorkoutDoneUpdate, session: SessionDep) -> dict:
    """Odhaczenie treningu. Data wykonania = dziś (AI widzi realny rytm — PLAN.md req 9)."""
    workout = _get_active_workout_or_404(session, workout_id)
    workout.done = data.done
    workout.completed_date = date.today() if data.done else None
    session.add(workout)
    session.commit()
    return _plan_to_dict(session, session.get(Plan, workout.plan_id))


@router.patch("/active/workouts/{workout_id}/exercises/{exercise_id}")
def set_exercise_feedback(
    workout_id: int, exercise_id: int, data: ExerciseFeedbackUpdate, session: SessionDep
) -> dict:
    """Ocena wykonania (1-5), uwaga i "zrobiłem" — idą do AI przy kolejnym tygodniu."""
    workout = _get_active_workout_or_404(session, workout_id)
    exercise = session.get(Exercise, exercise_id)
    if exercise is None or exercise.workout_id != workout_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nie ma takiego ćwiczenia w tym treningu")
    if data.rating is not None:
        exercise.rating = data.rating
        # Pamięć gwiazdek (req 24): ostatnia ocena wróci jako pre-wypełniona,
        # gdy AI znów da ćwiczenie o tej samej nazwie.
        entry = next(
            (
                c
                for c in session.exec(select(CatalogExercise)).all()
                if c.name.casefold() == exercise.name.casefold()
            ),
            None,
        )
        if entry is not None:
            entry.last_rating = data.rating
            session.add(entry)
    if data.note is not None:
        exercise.note = data.note
    if data.performed is not None:
        exercise.performed = data.performed
    if data.load is not None:
        exercise.load = data.load
    session.add(exercise)
    session.commit()
    return _plan_to_dict(session, session.get(Plan, workout.plan_id))
