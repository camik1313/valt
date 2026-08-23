# ============================================================
# exercises.py — the GET /exercises endpoint.
#
# Returns the full, static exercise library (app/exercises/database.py)
# for the browsable /exercises page on the frontend — NOT personalized;
# personalized, ranked recommendations are attached to an Analysis
# instead (see report_service.py's _build_recommendations, surfaced via
# GET /report/{id}.recommendations). This endpoint just lists what
# exists so a user can browse research-backed exercises without having
# run a scan first.
# ============================================================

from fastapi import APIRouter

from app.exercises.database import EXERCISES
from app.models.schemas import ExerciseInfo

router = APIRouter(tags=["exercises"])


@router.get("/exercises", response_model=list[ExerciseInfo])
async def list_exercises():
    return [
        ExerciseInfo(
            exercise_id=e.exercise_id,
            exercise_name=e.exercise_name,
            short_description=e.short_description,
            instructions=e.instructions,
            movement_targets=e.movement_targets,
            difficulty=e.difficulty,
            equipment=e.equipment,
            age_ranges=e.age_ranges,
            sports=e.sports,
            competitive_levels=e.competitive_levels,
            research_source=e.research_source,
            source_program=e.source_program,
            safety_notes=e.safety_notes,
        )
        for e in EXERCISES
    ]
