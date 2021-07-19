import enum
from datetime import datetime

from pydantic import BaseModel, EmailStr, constr


class SendMessageRequestCreate(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=128)
    email: EmailStr
    subject: constr(strip_whitespace=True, min_length=1, max_length=255)
    content: constr(min_length=1, max_length=10000)


class SendMessageRequestCreateResponse(BaseModel):
    status: enum.Enum
    date_time: datetime

    class Config:
        orm_mode = True
