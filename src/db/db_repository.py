from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from sqlalchemy.orm import selectinload
from src.db.db_config import make_session
from src.db.models import Question, Answer
from sqlalchemy import select, delete
from typing import Sequence, Optional


class QuestionsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_questions(self) -> Sequence[Question]:
        db_questions = await self.session.execute(
            select(Question).order_by(Question.created_at.desc())
        )

        return db_questions.scalars().all()

    async def get_question_by_id(self, q_id: int) -> Optional[Question]:
        db_question = await self.session.execute(
            select(Question).where(Question.id == q_id)
        )

        return db_question.scalar_one_or_none()

    async def create_questions(self, text: str) -> Question:
        new_question = Question(text=text)

        self.session.add(new_question)
        await self.session.commit()
        await self.session.refresh(new_question)

        return new_question

    async def get_questions_with_answers(self, q_id: int) -> Optional[Question]:
        db_question = (
            await self.session.execute(
                select(Question)
                .options(selectinload(Question.answers))
                .where(Question.id == q_id)
            )
        ).unique()

        return db_question.scalar_one_or_none()

    async def delete_question(self, q_id: int) -> Optional[int]:
        deleted_question = await self.session.execute(
            delete(Question).where(Question.id == q_id).returning(Question.id)
        )

        await self.session.commit()

        return deleted_question.scalar_one_or_none()


class AnswersRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_answer(self, q_id: int, user_id: str, text: str) -> Answer:
        new_answer = Answer(question_id=q_id, user_id=user_id, text=text)

        self.session.add(new_answer)

        await self.session.commit()
        await self.session.refresh(new_answer)

        return new_answer

    async def get_answer_by_id(self, a_id: int) -> Optional[Answer]:
        db_answer = await self.session.execute(select(Answer).where(Answer.id == a_id))
        return db_answer.scalar_one_or_none()

    async def delete_answer(self, a_id: int) -> Optional[int]:
        deleted_answer = await self.session.execute(
            delete(Answer).where(Answer.id == a_id).returning(Answer.id)
        )

        await self.session.commit()

        return deleted_answer.scalar_one_or_none()


async def make_q_repository(
    session: AsyncSession = Depends(make_session),
) -> QuestionsRepository:
    return QuestionsRepository(session)


async def make_a_repository(
    session: AsyncSession = Depends(make_session),
) -> AnswersRepository:
    return AnswersRepository(session)
