from fastapi import BackgroundTasks, Depends, FastAPI, Request
from sqlalchemy.orm import Session

from db import Base, SessionLocal, engine
from models import SendMessageRequest, SendMessageRequestStatus
from schemas import SendMessageRequestCreate, SendMessageRequestCreateResponse
from services import DiscordService, MessengerService, MessageDeliveryFailedError


Base.metadata.create_all(bind=engine)


app = FastAPI()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_messenger_service():
    yield DiscordService()


@app.get("/ping")
def ping():
    return {}


@app.post("/message", response_model=SendMessageRequestCreateResponse)
def create_message(
    request: Request,
    message_request: SendMessageRequestCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    messenger_service: MessengerService = Depends(get_messenger_service),
):
    send_request = SendMessageRequest(
        name=message_request.name,
        email=message_request.email,
        subject=message_request.subject,
        content=message_request.content,
        domain=request.headers["host"],
        ip_address=request.client.host,
    )
    db.add(send_request)
    db.commit()
    db.refresh(send_request)
    background_tasks.add_task(do_message_send, send_request, db, messenger_service)
    return send_request
 

def do_message_send(
    send_message_request: SendMessageRequest,
    db: Session,
    messenger_service: MessengerService,
):
    try:
        messenger_service.send_message(
            f"Name: {send_message_request.name}\n"
            f"Email: {send_message_request.email}\n"
            f"Subject: {send_message_request.subject}\n"
            f"Time: {send_message_request.date_time.isoformat()}\n"
            f"Domain: {send_message_request.domain}\n"
            f"IP Address: {send_message_request.ip_address}\n\n"
            f"{send_message_request.content}"
        )
        send_message_request.status = SendMessageRequestStatus.SENT
    except MessageDeliveryFailedError:
        send_message_request.status = SendMessageRequestStatus.FAILED

    db.commit()
