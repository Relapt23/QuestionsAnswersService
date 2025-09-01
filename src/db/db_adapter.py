from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from sqlalchemy.orm import selectinload

from src.db.db_config import make_session
from src.db.models import Question, Answer
from sqlalchemy import select, delete


class GetAdapter:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_questions(self):
        db_questions = await self.session.execute(
            select(Question).order_by(Question.created_at.desc())
        )

        return db_questions

    async def get_question(self, q_id: int):
        db_question = await self.session.execute(
            select(Question).where(Question.id == q_id)
        )

        return db_question

    async def get_questions_with_answers(self, q_id: int):
        db_question = (
            await self.session.execute(
                select(Question)
                .options(selectinload(Question.answers))
                .where(Question.id == q_id)
            )
        ).unique()

        return db_question

    async def get_answer_by_question_id(self, q_id: int):
        db_question = await self.session.execute(
            select(Question).where(Question.id == q_id)
        )
        return db_question

    async def get_answer_by_answer_id(self, a_id: int):
        answer = await self.session.execute(select(Answer).where(Answer.id == a_id))
        return answer


class CreateAdapter:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_questions(self, text: str) -> Question:
        new_question = Question(text=text)

        self.session.add(new_question)
        await self.session.commit()
        await self.session.refresh(new_question)

        return new_question

    async def create_answer(self, q_id: int, user_id: str, text: str):
        new_answer = Answer(question_id=q_id, user_id=user_id, text=text)

        self.session.add(new_answer)

        await self.session.commit()
        await self.session.refresh(new_answer)

        return new_answer


class DeleteAdapter:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def delete_question(self, q_id: int):
        db_question = await self.session.execute(
            delete(Question).where(Question.id == q_id).returning(Question.id)
        )

        await self.session.commit()

        return db_question

    async def delete_answer(self, a_id: int):
        deleted_answer = await self.session.execute(
            delete(Answer).where(Answer.id == a_id).returning(Answer.id)
        )

        await self.session.commit()

        return deleted_answer


async def make_get_adapter(
    session: AsyncSession = Depends(make_session),
) -> GetAdapter:
    return GetAdapter(session)


async def make_create_adapter(
    session: AsyncSession = Depends(make_session),
) -> CreateAdapter:
    return CreateAdapter(session)


async def make_delete_adapter(
    session: AsyncSession = Depends(make_session),
) -> DeleteAdapter:
    return DeleteAdapter(session)
