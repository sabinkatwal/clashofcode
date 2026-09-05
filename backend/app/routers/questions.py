import json
import logging
from collections.abc import Mapping

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_developer
from app.database import get_db
from app.models import CodingQuestion
from app.schemas import CodingQuestionCreate, CodingQuestionResponse, CodingQuestionUpdate

router = APIRouter(tags=["Questions"])

VALID_LEVELS = {"easy", "medium", "hard"}


def _json_list(value: object) -> list:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return []
    if isinstance(value, list):
        return value
    return []


def _serialize_question(question: CodingQuestion) -> dict:
    test_cases = _json_list(question.test_cases)
    examples = _json_list(question.examples)
    return {
        "id": question.id,
        "title": question.title,
        "question_text": question.description,
        "option_a": getattr(question, "option_a", None),
        "option_b": getattr(question, "option_b", None),
        "option_c": getattr(question, "option_c", None),
        "option_d": getattr(question, "option_d", None),
        "options": [],
        "difficulty": question.difficulty,
        "description": question.description,
        "test_cases": test_cases,
        "points": question.points,
        "examples": [
            {
                "input": ex.get("input") if isinstance(ex.get("input"), str) else json.dumps(ex.get("input")),
                "output": ex.get("output") if isinstance(ex.get("output"), str) else json.dumps(ex.get("output")),
                "explanation": ex.get("explanation") if ex.get("explanation") is not None else None,
            }
            for ex in examples
            if isinstance(ex, Mapping)
        ],
        "constraints": question.constraints,
        "starter_code": question.starter_code,
    }


@router.get("/questions", response_model=list[CodingQuestionResponse])
async def list_questions(
    level: str | None = Query(default=None, alias="level"),
    difficulty: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    query = select(CodingQuestion).order_by(CodingQuestion.points.asc(), CodingQuestion.id.asc())

    selected_difficulty = difficulty or level
    if selected_difficulty and selected_difficulty.lower() != "all":
        normalized_level = selected_difficulty.lower()
        if normalized_level not in VALID_LEVELS:
            raise HTTPException(status_code=400, detail="Invalid difficulty level.")
        query = query.where(CodingQuestion.difficulty == normalized_level)

    result = await db.execute(query)
    raw_questions = result.scalars().all()
    serialized = []
    for i, question in enumerate(raw_questions):
        try:
            serialized.append(_serialize_question(question))
        except Exception as exc:
            logging.exception("Failed serializing question at index %s (id=%s)", i, getattr(question, 'id', None))
            raise HTTPException(status_code=500, detail=f"Serialization error on question id={getattr(question, 'id', None)}") from exc
    return serialized


@router.post(
    "/questions",
    response_model=CodingQuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_question(
    data: CodingQuestionCreate,
    _: str = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    question = CodingQuestion(
        title=data.title.strip(),
        difficulty=data.difficulty,
        description=data.description.strip(),
        test_cases=[case.model_dump() for case in data.test_cases],
        examples=[example.model_dump() for example in data.examples],
        constraints=data.constraints.strip() if data.constraints else None,
        points=data.points,
        starter_code=data.starter_code,
    )

    db.add(question)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A question with this title already exists.",
        ) from exc

    await db.refresh(question)
    return _serialize_question(question)


@router.put("/questions/{question_id}", response_model=CodingQuestionResponse)
async def update_question(
    question_id: int,
    data: CodingQuestionUpdate,
    _: str = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CodingQuestion).where(CodingQuestion.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    updates = data.model_dump(exclude_unset=True)
    if "title" in updates and updates["title"] is not None:
        question.title = updates["title"].strip()
    if "difficulty" in updates and updates["difficulty"] is not None:
        question.difficulty = updates["difficulty"]
    if "description" in updates and updates["description"] is not None:
        question.description = updates["description"].strip()
    if "test_cases" in updates and updates["test_cases"] is not None:
        question.test_cases = [case.model_dump() for case in data.test_cases or []]
    if "examples" in updates and updates["examples"] is not None:
        question.examples = [example.model_dump() for example in data.examples or []]
    if "constraints" in updates:
        question.constraints = data.constraints.strip() if data.constraints else None
    if "points" in updates and updates["points"] is not None:
        question.points = updates["points"]
    if "starter_code" in updates:
        question.starter_code = data.starter_code

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A question with this title already exists.",
        ) from exc

    await db.refresh(question)
    return _serialize_question(question)


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: int,
    _: str = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CodingQuestion).where(CodingQuestion.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    await db.delete(question)
    await db.commit()
