from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AnswerOut(BaseModel):
    id: int
    question_id: int
    user_id: str
    text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
