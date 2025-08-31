from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class AnswerResponse(BaseModel):
    id: int
    question_id: int
    user_id: str
    text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreateAnswerParams(BaseModel):
    user_id: str
    text: NonEmptyStr

    model_config = ConfigDict(from_attributes=True)


class QuestionCreateParams(BaseModel):
    text: NonEmptyStr


class QuestionResponse(BaseModel):
    id: int
    text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionWithAnswersResponse(QuestionResponse):
    answers: list[AnswerResponse]
