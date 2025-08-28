from pydantic import BaseModel, ConfigDict
from datetime import datetime


class QuestionCreate(BaseModel):
    text: str


class QuestionOut(BaseModel):
    id: int
    text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
