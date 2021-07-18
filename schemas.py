import enum
from datetime import datetime

from pydantic import BaseModel, EmailStr


class SendMessageRequestCreate(BaseModel):
    name: str
    email: EmailStr
    subject: str
    content: str


class SendMessageRequestCreateResponse(BaseModel):
    status: enum.Enum
    date_time: datetime

    class Config:
        orm_mode = True
