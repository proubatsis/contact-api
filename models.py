from datetime import datetime
import enum

from uuid import uuid4
from sqlalchemy import Column, Enum, String, DateTime

from db import Base


def generate_uuid():
    return str(uuid4())


class SendMessageRequestStatus(enum.IntEnum):
    ACCEPTED = 0
    SENT = 1
    FAILED = 2


class SendMessageRequest(Base):
    __tablename__ = "send_email_request"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    name = Column(String)
    email = Column(String)
    subject = Column(String)
    content = Column(String)
    domain = Column(String)
    ip_address = Column(String)
    date_time = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(SendMessageRequestStatus), default=SendMessageRequestStatus.ACCEPTED)
