import aioredis
from fastapi import BackgroundTasks, Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from db import Base, SessionLocal, engine
from models import SendMessageRequest, SendMessageRequestStatus
from schemas import SendMessageRequestCreate, SendMessageRequestCreateResponse
from services import DiscordService, MessengerService, MessageDeliveryFailedError
from settings import REDIS_URL


Base.metadata.create_all(bind=engine)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://panagiotis.ca",
        "http://localhost:8000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_messenger_service():
    yield DiscordService()


@app.on_event("startup")
async def startup():
    if REDIS_URL:
        redis = await aioredis.create_redis_pool(REDIS_URL)
        await FastAPILimiter.init(redis)


def build_rate_limit(times, seconds):
    def get_rate_limit():
        if REDIS_URL:
            yield RateLimiter(times=times, seconds=seconds)()
        else:
            yield None
    return get_rate_limit


@app.get("/ping", dependencies=[Depends(build_rate_limit(3, 60))])
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
