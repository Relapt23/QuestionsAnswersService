from fastapi import APIRouter, Depends, HTTPException, status, Response
from src.db.db_repository import (
    QuestionsRepository,
    make_q_repository,
    AnswersRepository,
    make_a_repository,
)

from src.app.schemas import (
    QuestionResponse,
    QuestionCreateParams,
    QuestionWithAnswersResponse,
    CreateAnswerParams,
    AnswerResponse,
)


router = APIRouter()


@router.get("/questions/")
async def get_questions(
    q_repository: QuestionsRepository = Depends(make_q_repository),
) -> list[QuestionResponse]:
    questions = await q_repository.get_questions()

    return [QuestionResponse.model_validate(q) for q in questions]


@router.post("/questions/", status_code=status.HTTP_201_CREATED)
async def create_question(
    payload: QuestionCreateParams,
    q_repository: QuestionsRepository = Depends(make_q_repository),
) -> QuestionResponse:
    new_question = await q_repository.create_questions(payload.text)

    return QuestionResponse.model_validate(new_question)


@router.get("/questions/{question_id}")
async def get_questions_with_answers(
    question_id: int, q_repository: QuestionsRepository = Depends(make_q_repository)
) -> QuestionWithAnswersResponse:
    question = await q_repository.get_questions_with_answers(question_id)

    if not question:
        raise HTTPException(status_code=404, detail="question_not_found")

    return QuestionWithAnswersResponse.model_validate(question)


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: int, q_repository: QuestionsRepository = Depends(make_q_repository)
) -> Response:
    db_question = await q_repository.delete_question(question_id)

    if db_question is None:
        raise HTTPException(status_code=404, detail="question_not_found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/questions/{question_id}/answers/", status_code=status.HTTP_201_CREATED)
async def create_answer(
    question_id: int,
    payload: CreateAnswerParams,
    a_repository: AnswersRepository = Depends(make_a_repository),
    q_repository: QuestionsRepository = Depends(make_q_repository),
) -> AnswerResponse:
    db_question = await q_repository.get_question_by_id(question_id)

    if db_question is None:
        raise HTTPException(status_code=404, detail="question_not_found")

    new_answer = await a_repository.create_answer(
        q_id=question_id, user_id=payload.user_id, text=payload.text
    )

    return AnswerResponse.model_validate(new_answer)


@router.get("/answers/{answer_id}")
async def get_answer(
    answer_id: int, a_repository: AnswersRepository = Depends(make_a_repository)
) -> AnswerResponse:
    answer = await a_repository.get_answer_by_id(answer_id)

    if answer is None:
        raise HTTPException(status_code=404, detail="answer_not_found")

    return AnswerResponse.model_validate(answer)


@router.delete("/answers/{answer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_answer(
    answer_id: int, a_repository: AnswersRepository = Depends(make_a_repository)
) -> Response:
    deleted_answer = await a_repository.delete_answer(answer_id)

    if deleted_answer is None:
        raise HTTPException(status_code=404, detail="answer_not_found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
