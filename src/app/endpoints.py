from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from src.app.schemas.questions import QuestionOut, QuestionCreate, QuestionWithAnswers
from src.db.models import Question

from src.db.db_config import make_session

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("/", response_model=list[QuestionOut])
async def get_questions(
    session: AsyncSession = Depends(make_session),
):
    questions = (
        (await session.execute(select(Question).order_by(Question.created_at.desc())))
        .scalars()
        .all()
    )

    return questions


@router.post("/", status_code=201)
async def create_question(
    payload: QuestionCreate, session: AsyncSession = Depends(make_session)
):
    new_question = Question(text=payload.text.strip())
    session.add(new_question)
    await session.commit()
    await session.refresh(new_question)
    return new_question


@router.get("/{question_id}", response_model=QuestionWithAnswers)
async def get_questions_with_answers(
    question_id: int, session: AsyncSession = Depends(make_session)
):
    question = (
        (
            await session.execute(
                select(Question)
                .options(selectinload(Question.answers))
                .where(Question.id == question_id)
            )
        )
        .unique()
        .scalar_one_or_none()
    )
    if not question:
        raise HTTPException(status_code=404, detail="question_not_found")

    question.answers.sort(reverse=True)

    return question


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: int, session: AsyncSession = Depends(make_session)
):
    db_question = (
        await session.execute(
            delete(Question).where(Question.id == question_id).returning(Question.id)
        )
    ).scalar_one_or_none()
    if db_question is None:
        raise HTTPException(status_code=404, detail="question_not_found")

    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
