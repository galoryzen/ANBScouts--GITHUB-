from faker import Faker
from random import seed
from src.models.main import db
from src.models import User, Video, Vote, VideoStatus
from werkzeug.security import generate_password_hash

# Fijar semilla para reproducibilidad
SEED = 42
fake = Faker()
fake.seed_instance(SEED)
seed(SEED)

def create_users(n=5):
    users = []
    password = generate_password_hash("password123")
    for i in range(n):
        user = User(
            username=f"user_{i}",
            password=password,
            name=fake.first_name(),
            last_name=fake.last_name(),
            email=f"user_{i}@example.com",
            city=fake.city(),
            country=fake.country()
        )
        db.session.add(user)
        users.append(user)
    db.session.commit()
    return users

def create_videos(users, n=10):
    videos = []
    for i in range(n):
        video = Video(
            title=f"Video {i}",  # Títulos fijos
            status=list(VideoStatus)[i % len(VideoStatus)],
            original_url=f"https://example.com/video{i}",
            user_id=users[i % (len(users)-1)].id,
            processed_url=f"https://example.com/processed/video{i}" if i % 2 == 0 else None,
            processed_at=fake.date_time_this_year() if i % 2 == 0 else None,
        )
        db.session.add(video)
        videos.append(video)
    db.session.commit()
    return videos

def create_votes(users, videos, n=2):
    votes = []
    for i in range(n):
        vote = Vote(
            user_id=users[i % len(users)].id,
            video_id=videos[i % len(videos)].video_id,
        )
        db.session.add(vote)
        votes.append(vote)
    db.session.commit()
    return votes

def generate_mock_data():
    users = create_users()
    videos = create_videos(users)
    create_votes(users, videos)
    print("Mock data generated successfully!")

