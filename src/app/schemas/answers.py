from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID


class AnswerOut(BaseModel):
    id: int
    question_id: int
    user_id: UUID
    text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreateAnswer(BaseModel):
    user_id: UUID
    text: str

    model_config = ConfigDict(from_attributes=True)
