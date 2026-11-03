"""Plany tygodnia: generowanie przez AI (Etap 5) i odczyt szkicu/aktywnego planu.

Panel edycji i zatwierdzania szkicu powstanie w Etapie 6 — tu tylko dane.
Zasady (PLAN.md): szkic zawsze maksymalnie jeden (nowy nadpisuje stary),
generowanie zablokowane, dopóki aktywny plan ma nieodhaczone treningi.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError
from sqlmodel import select

from app.ai import AiError, build_generation_prompt, generate_plan
from app.database import SessionDep
from app.models import CatalogExercise, Equipment, Exercise, Plan, Profile, Workout
from app.schemas import AiPlan

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
                        "sets": ex.sets,
                        "reps": ex.reps,
                        "rest_between_sets_s": ex.rest_between_sets_s,
                        "load": ex.load,
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


def _register_ai_exercises(session, plan_data: AiPlan) -> None:
    """Nowe nazwy ćwiczeń od AI dopisuje do katalogu ze źródłem "ai" (PLAN.md)."""
    existing = {ex.name.casefold() for ex in session.exec(select(CatalogExercise)).all()}
    for workout in plan_data.workouts:
        for exercise in workout.exercises:
            if exercise.name.casefold() not in existing:
                session.add(
                    CatalogExercise(name=exercise.name, required_equipment=[], source="ai")
                )
                existing.add(exercise.name.casefold())


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

    equipment = list(session.exec(select(Equipment).where(Equipment.owned)).all())  # type: ignore[arg-type]
    catalog = list(session.exec(select(CatalogExercise)).all())
    week_number = max((p.week_number for p in session.exec(select(Plan)).all()), default=0) + 1

    prompt = build_generation_prompt(profile, equipment, catalog, week_number)
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
            session.add(
                Exercise(
                    workout_id=workout.id,
                    name=exercise_data.name,
                    sets=exercise_data.sets,
                    reps=exercise_data.reps,
                    rest_between_sets_s=exercise_data.rest_between_sets,
                    note=exercise_data.notes,
                )
            )

    _register_ai_exercises(session, plan_data)
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
