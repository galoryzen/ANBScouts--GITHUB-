from datetime import datetime, UTC
import unittest
import io

from flask import json
from flask_jwt_extended import create_access_token
from src.models.main import User, Video, VideoSchema, VideoStatus
from src.app import app, db
from unittest.mock import patch

def generate_mock_jwt(user_id):
    """Generates a mock JWT token for testing."""
    return create_access_token(identity={"id": str(user_id)})

class TestVideos(unittest.TestCase):
    def setUp(self):
        self.url = "/videos/"
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

    def test_get_videos_not_authorized_401(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_get_videos_empty_for_user_with_no_videos_200(self):
        self.create_users()
        self.create_videos()

        token = generate_mock_jwt(self.user3.id)
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.get(self.url, headers=headers)

        self.assertEqual(response.json, [])

    def test_get_videos_videos_user_1_200(self):
        self.create_users()
        self.create_videos()

        token = generate_mock_jwt(self.user1.id)
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.get(self.url, headers=headers)

        schema = VideoSchema(many=True)
        expected_videos = json.loads(schema.dumps([self.video2_user1, self.video1_user1]))
        self.assertEqual(response.json, expected_videos)

    @patch("src.tasks.process_video.delay")
    def test_upload_video_success_201(self, mock_process_video):
        self.create_users()

        token = generate_mock_jwt(self.user1.id)
        headers = {"Authorization": f"Bearer {token}"}

        data = {
            "title": "Video de prueba",
            "file": (io.BytesIO(b"contenido fake de video"), "video.mp4")
        }

        mock_process_video.return_value.id = "mock-task-id"

        response = self.client.post("/videos/upload", headers=headers, data=data, content_type="multipart/form-data")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["title"], "Video de prueba")
        self.assertEqual(response.json["message"], "Video subido correctamente. Procesamiento en curso")


class TestVideo(unittest.TestCase):
    def setUp(self):
        self.url = "/videos/"
        self.client = app.test_client()

        self.create_videos()

    def create_videos(self):
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

        db.session.add(self.user1)
        db.session.add(self.user2)

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

        db.session.add(self.video1_user1)
        db.session.add(self.video2_user1)
        db.session.commit()

        self.url = f"{self.url}{self.video1_user1.video_id}"

    def tearDown(self):
        db.session.query(Video).delete()
        db.session.query(User).delete()
        db.session.commit()

    def test_get_videos_not_authorized_401(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_get_video_empty_404(self):
        url = f"{self.url}999"
        token = generate_mock_jwt(self.user1.id)
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.get(url, headers=headers)


        self.assertEqual(response.status_code, 404)

    def test_get_video_existing_owner_200(self):
        token = generate_mock_jwt(self.user1.id)
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.get(self.url, headers=headers)

        schema = VideoSchema()
        expected_video = json.loads(schema.dumps(self.video1_user1))
        expected_video["votes_count"] = 0

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, expected_video)

    def test_get_video_existing_not_owner_403(self):
        token = generate_mock_jwt(self.user2.id)
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.get(self.url, headers=headers)

        self.assertEqual(response.status_code, 403)

    def test_delete_videos_not_authorized_401(self):
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, 401)

    def test_delete_video_empty_404(self):
        url = f"{self.url}999"
        token = generate_mock_jwt(self.user1.id)
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.delete(url, headers=headers)

        self.assertEqual(response.status_code, 404)

    def test_delete_video_existing_owner_200(self):
        token = generate_mock_jwt(self.user1.id)
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.delete(self.url, headers=headers)

        db.session.refresh(self.video1_user1)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.video1_user1.is_deleted)

    def test_delete_video_existing_not_owner_403(self):
        token = generate_mock_jwt(self.user2.id)
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.delete(self.url, headers=headers)

        self.assertEqual(response.status_code, 403)

    def test_delete_video_existing_owner_already_ready_voted_400(self):
        url = f'/videos/{self.video2_user1.video_id}'
        token = generate_mock_jwt(self.user1.id)
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.delete(url, headers=headers)

        self.assertEqual(response.status_code, 400)

