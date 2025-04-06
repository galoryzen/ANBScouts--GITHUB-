from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from src.models.main import VideoSchema, Video, Vote, db, VideoStatus
from sqlalchemy import func, select

public_bp = Blueprint('public', __name__)

@public_bp.route('/videos', methods=['GET'], strict_slashes=False)
def get_videos():
    
    videos = db.session.execute(
        select(Video)
        .where(Video.status == VideoStatus.PROCESADO, Video.is_deleted == False)
        .order_by(Video.uploaded_at.desc())
    ).scalars().all()

    video_schema = VideoSchema(many=True)    
    serialized_videos = video_schema.dump(videos)

    return jsonify(serialized_videos), 200


@public_bp.route('/videos/<video_id>/vote', methods=['POST'], strict_slashes=False)
@jwt_required()
def vote_video(video_id: str):
    user_id = get_jwt_identity()
    user_id = user_id["id"]

    if not user_id:
        return {"mesage": "Usuario no autenticado"}, 401
    
    video = db.session.execute(
        select(Video)
        .where(Video.video_id == video_id, Video.status == VideoStatus.PROCESADO, Video.is_deleted == False)
    ).first()

    if not video:
        return {"message": f"El video con el {video_id} especificado no existe o no pertenece al usuario"}, 404

    vote = db.session.execute(
        select(Vote)
        .where(Vote.user_id == user_id, Vote.video_id == video_id)
    ).first()

    if vote:
        return {"message": "Ya has votado por este video"}, 400
    
    new_vote = Vote(user_id=user_id, video_id=video_id)
    db.session.add(new_vote)
    db.session.commit()

    return {"message": "Voto exitoso"}, 200
