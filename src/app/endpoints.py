from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.app.schemas import QuestionOut, QuestionCreate
from src.db.models import Question

from src.db.db_config import make_session

router = APIRouter()


@router.get("/questions/", response_model=list[QuestionOut])
async def get_questions(
    session: AsyncSession = Depends(make_session),
):
    questions = (
        (await session.execute(select(Question).order_by(Question.created_at.desc())))
        .scalars()
        .all()
    )

    return questions


@router.post("/questions/")
async def create_question(
    payload: QuestionCreate, session: AsyncSession = Depends(make_session)
):
    new_question = Question(text=payload.text.strip())
    session.add(new_question)
    await session.commit()
    await session.refresh(new_question)
    return new_question
