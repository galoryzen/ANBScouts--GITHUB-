import enum
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields

db = SQLAlchemy()

class Base(db.Model):
    __abstract__ = True

class User(Base):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)

    # Profile information
    username = db.Column(db.String(100))
    password = db.Column(db.String(255))

    # User personal information
    role = db.Column(db.String(50))
    name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))

    # Record information
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Video relations
    videos = relationship("Video", back_populates="user")

    # Vote relation
    votes = relationship("Vote", back_populates="user")


class VideoStatus(enum.Enum):
    PROCESADO = "procesado"
    PROCESANDO = "procesando"
    SUBIENDO = "subiendo"
    ERROR = "error"


class Video(Base):
    __tablename__ = "video"

    video_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    status = db.Column(db.Enum(VideoStatus))
    original_url = db.Column(db.String(255), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    processed_url = db.Column(db.String(255), nullable=True)
    processed_at = db.Column(db.DateTime, nullable=True)

    user_id = db.Column(db.Integer, ForeignKey("user.id"))
    user = relationship("User", back_populates="videos")
    is_deleted = db.Column(db.Boolean, default=False)

    # Vote relation
    votes = relationship("Vote", back_populates="video")


class Vote(Base):
    __tablename__ = "vote"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, ForeignKey("user.id"))
    user = relationship("User", back_populates="votes")

    video_id = db.Column(db.Integer, ForeignKey("video.video_id"))
    video = relationship("Video", back_populates="votes")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class VideoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Video
        include_fk = True
        load_instance = True

    video_id = fields.String(attribute="video_id")
    uploaded_at = fields.DateTime(format="iso")
    processed_at = fields.DateTime(format="iso")
    processed_url = fields.Url()
