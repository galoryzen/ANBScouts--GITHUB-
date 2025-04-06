from datetime import datetime, UTC
import unittest

from flask import json
from flask_jwt_extended import create_access_token
from src.models.main import User, Video, VideoSchema, VideoStatus, Vote
from src.app import app, db

def generate_mock_jwt(user_id):
    """Generates a mock JWT token for testing."""
    return create_access_token(identity={"id": str(user_id)})


class TestPublic(unittest.TestCase):

    def setUp(self):
        self.url = "/public/"
        self.client = app.test_client()

        with app.app_context():
            db.create_all()


    def create_users(self):
        self.user1 = User(
            username="user1",
            password="password123",
            role="admin",
            name="John",
            last_name="Doe",
            email="john.doe@example.com",
            city="City1",
            country="Country1",
            created_at=datetime.now(UTC),
        )

        self.user2 = User(
            username="user2",
            password="password456",
            role="viewer",
            name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            city="City2",
            country="Country2",
            created_at=datetime.now(UTC),
        )

        self.user3 = User(
            username="user3",
            password="password456",
            role="viewer",
            name="John",
            last_name="Smith",
            email="john.smith@example.com",
            city="City3",
            country="Country3",
            created_at=datetime.now(UTC),
        )

        db.session.add(self.user1)
        db.session.add(self.user2)
        db.session.add(self.user3)
    
        db.session.commit()

    def create_videos(self):
        self.video1_user1 = Video(
            title="Video 1 for User 1",
            status=VideoStatus.PROCESANDO,
            uploaded_at=datetime.now(UTC),
            user=self.user1,
        )

        self.video2_user1 = Video(
            title="Video 2 for User 1",
            status=VideoStatus.PROCESADO,
            uploaded_at=datetime.now(UTC),
            user=self.user1,
        )

        self.video1_user2 = Video(
            title="Video 1 for User 2",
            status=VideoStatus.SUBIENDO,
            uploaded_at=datetime.now(UTC),
            user=self.user2,
        )

        self.video2_user2 = Video(
            title="Video 2 for User 2",
            status=VideoStatus.ERROR,
            uploaded_at=datetime.now(UTC),
            user=self.user2,
        )

        db.session.add(self.video1_user1)
        db.session.add(self.video2_user1)
        db.session.add(self.video1_user2)
        db.session.add(self.video2_user2)

        db.session.commit()

    def tearDown(self):
        db.session.query(Video).delete()
        db.session.query(User).delete()
        db.session.commit()

    def test_get_public_videos_200(self):
        self.create_users()
        self.create_videos()

        response = self.client.get(f"{self.url}videos")
        self.assertEqual(response.status_code, 200)

    def test_vote_video_success_200(self):
        self.create_users()
        self.create_videos()

        token = generate_mock_jwt(self.user3.id)
        headers = {"Authorization": f"Bearer {token}"}
        video_id = self.video2_user1.video_id

        response = self.client.post(f"{self.url}videos/{video_id}/vote", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["message"], "Voto exitoso")

    def test_vote_video_unauthorized_401(self):
        self.create_users()
        self.create_videos()

        video_id = self.video2_user1.video_id
        response = self.client.post(f"{self.url}videos/{video_id}/vote")

        self.assertEqual(response.status_code, 401)

    def test_vote_video_already_voted_400(self):
        self.create_users()
        self.create_videos()

        token = generate_mock_jwt(self.user2.id)
        headers = {"Authorization": f"Bearer {token}"}
        video_id = self.video2_user1.video_id

        self.client.post(f"{self.url}videos/{video_id}/vote", headers=headers)

        response = self.client.post(f"{self.url}videos/{video_id}/vote", headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["message"], "Ya has votado por este video")