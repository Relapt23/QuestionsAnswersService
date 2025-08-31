from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from src.app.schemas import (
    QuestionResponse,
    QuestionCreateParams,
    QuestionWithAnswersResponse,
    CreateAnswerParams,
    AnswerResponse,
)

from src.db.models import Question, Answer

from src.db.db_config import make_session

router = APIRouter()


@router.get("/questions/")
async def get_questions(
    session: AsyncSession = Depends(make_session),
) -> list[QuestionResponse]:
    questions = (
        (await session.execute(select(Question).order_by(Question.created_at.desc())))
        .scalars()
        .all()
    )

    return [QuestionResponse.model_validate(q) for q in questions]


@router.post("/questions/", status_code=status.HTTP_201_CREATED)
async def create_question(
    payload: QuestionCreateParams, session: AsyncSession = Depends(make_session)
) -> QuestionResponse:
    new_question = Question(text=payload.text)
    session.add(new_question)

    await session.commit()
    await session.refresh(new_question)

    return QuestionResponse.model_validate(new_question)


@router.get("/questions/{question_id}")
async def get_questions_with_answers(
    question_id: int, session: AsyncSession = Depends(make_session)
) -> QuestionWithAnswersResponse:
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

    return QuestionWithAnswersResponse.model_validate(question)


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: int, session: AsyncSession = Depends(make_session)
) -> Response:
    db_question = (
        await session.execute(
            delete(Question).where(Question.id == question_id).returning(Question.id)
        )
    ).scalar_one_or_none()

    if db_question is None:
        raise HTTPException(status_code=404, detail="question_not_found")

    await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/questions/{question_id}/answers/", status_code=status.HTTP_201_CREATED)
async def create_answer(
    question_id: int,
    payload: CreateAnswerParams,
    session: AsyncSession = Depends(make_session),
) -> AnswerResponse:
    db_question = (
        await session.execute(select(Question).where(Question.id == question_id))
    ).scalar_one_or_none()

    if db_question is None:
        raise HTTPException(status_code=404, detail="question_not_found")

    new_answer = Answer(
        question_id=question_id, user_id=payload.user_id, text=payload.text
    )
    session.add(new_answer)

    await session.commit()
    await session.refresh(new_answer)

    return AnswerResponse.model_validate(new_answer)


@router.get("/answers/{answer_id}")
async def get_answer(
    answer_id: int, session: AsyncSession = Depends(make_session)
) -> AnswerResponse:
    answer = (
        await session.execute(select(Answer).where(Answer.id == answer_id))
    ).scalar_one_or_none()

    if answer is None:
        raise HTTPException(status_code=404, detail="answer_not_found")

    return AnswerResponse.model_validate(answer)


@router.delete("/answers/{answer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_answer(
    answer_id: int, session: AsyncSession = Depends(make_session)
) -> Response:
    deleted_answer = (
        await session.execute(
            delete(Answer).where(Answer.id == answer_id).returning(Answer.id)
        )
    ).scalar_one_or_none()

    if deleted_answer is None:
        raise HTTPException(status_code=404, detail="answer_not_found")

    await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
