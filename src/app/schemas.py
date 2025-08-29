from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AnswerResponse(BaseModel):
    id: int
    question_id: int
    user_id: str
    text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreateAnswerParams(BaseModel):
    user_id: str
    text: str

    model_config = ConfigDict(from_attributes=True)


class QuestionCreateParams(BaseModel):
    text: str


class QuestionResponse(BaseModel):
    id: int
    text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionWithAnswersResponse(QuestionResponse):
    answers: list[AnswerResponse]
