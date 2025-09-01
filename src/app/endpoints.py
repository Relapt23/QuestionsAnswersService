from fastapi import APIRouter, Depends, HTTPException, status, Response
from src.db.db_adapter import (
    GetAdapter,
    make_get_adapter,
    CreateAdapter,
    make_create_adapter,
    DeleteAdapter,
    make_delete_adapter,
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
    g_adapter: GetAdapter = Depends(make_get_adapter),
) -> list[QuestionResponse]:
    questions = (await g_adapter.get_questions()).scalars().all()

    return [QuestionResponse.model_validate(q) for q in questions]


@router.post("/questions/", status_code=status.HTTP_201_CREATED)
async def create_question(
    payload: QuestionCreateParams,
    c_adapter: CreateAdapter = Depends(make_create_adapter),
) -> QuestionResponse:
    new_question = await c_adapter.create_questions(payload.text)

    return QuestionResponse.model_validate(new_question)


@router.get("/questions/{question_id}")
async def get_questions_with_answers(
    question_id: int, g_adapter: GetAdapter = Depends(make_get_adapter)
) -> QuestionWithAnswersResponse:
    question = (
        await g_adapter.get_questions_with_answers(question_id)
    ).scalar_one_or_none()

    if not question:
        raise HTTPException(status_code=404, detail="question_not_found")

    return QuestionWithAnswersResponse.model_validate(question)


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: int, d_adapter: DeleteAdapter = Depends(make_delete_adapter)
) -> Response:
    db_question = (await d_adapter.delete_question(question_id)).scalar_one_or_none()

    if db_question is None:
        raise HTTPException(status_code=404, detail="question_not_found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/questions/{question_id}/answers/", status_code=status.HTTP_201_CREATED)
async def create_answer(
    question_id: int,
    payload: CreateAnswerParams,
    c_adapter: CreateAdapter = Depends(make_create_adapter),
    g_adapter: GetAdapter = Depends(make_get_adapter),
) -> AnswerResponse:
    db_question = (await g_adapter.get_question(question_id)).scalar_one_or_none()

    if db_question is None:
        raise HTTPException(status_code=404, detail="question_not_found")

    new_answer = await c_adapter.create_answer(
        q_id=question_id, user_id=payload.user_id, text=payload.text
    )

    return AnswerResponse.model_validate(new_answer)


@router.get("/answers/{answer_id}")
async def get_answer(
    answer_id: int, g_adapter: GetAdapter = Depends(make_get_adapter)
) -> AnswerResponse:
    answer = (await g_adapter.get_answer_by_answer_id(answer_id)).scalar_one_or_none()

    if answer is None:
        raise HTTPException(status_code=404, detail="answer_not_found")

    return AnswerResponse.model_validate(answer)


@router.delete("/answers/{answer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_answer(
    answer_id: int, d_adapter: DeleteAdapter = Depends(make_delete_adapter)
) -> Response:
    deleted_answer = (await d_adapter.delete_answer(answer_id)).scalar_one_or_none()

    if deleted_answer is None:
        raise HTTPException(status_code=404, detail="answer_not_found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
