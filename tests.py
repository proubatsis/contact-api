import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from db import Base, engine
from main import app, get_db
from models import SendMessageRequest, SendMessageRequestStatus

DB_URL = "sqlite:///./test.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()
        self.client = TestClient(app)
        return super().setUp()

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(bind=engine)
        return super().tearDown()

    def test_ping(self):
        response = self.client.get("/ping")
        self.assertEqual(200, response.status_code)

    @patch("main.do_message_send")
    def test_create_email(self, do_message_send_mock):
        # Invalid email address
        response = self.client.post(
            "/message",
            json={
                "name": "Me",
                "email": "gmail.com",
                "subject": "Hello",
                "content": "This is an email!",
            },
        )
        self.assertEqual(422, response.status_code)

        # Should work
        response = self.client.post(
            "/message",
            json={
                "name": "Me",
                "email": "me@gmail.com",
                "subject": "Hello",
                "content": "This is an email!",
            },
        )

        self.assertEqual(200, response.status_code)
        send_request = self.db.query(SendMessageRequest).first()
        self.assertIsNotNone(send_request)
        self.assertEqual("Me", send_request.name)
        self.assertEqual("me@gmail.com", send_request.email)
        self.assertEqual("Hello", send_request.subject)
        self.assertEqual("This is an email!", send_request.content)

        self.assertDictEqual(
            {
                "status": int(SendMessageRequestStatus.ACCEPTED),
                "date_time": send_request.date_time.isoformat(),
            },
            response.json(),
        )


if __name__ == "__main__":
    unittest.main()
