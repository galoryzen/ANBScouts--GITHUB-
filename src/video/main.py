import uuid
import os
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from src.models.main import VideoSchema, Video, Vote, db, VideoStatus
from sqlalchemy import func, select
from werkzeug.utils import secure_filename
from src.tasks import process_video


videos_bp = Blueprint('videos', __name__)

FOLDER = 'uploads/'
EXTENSIONS = {'mp4'}
FILE_SIZE = 100 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSIONS

@videos_bp.route('/upload', methods=['POST'], strict_slashes=False)
@jwt_required()
def upload_video():
    identity = get_jwt_identity()
    user_id = identity['id']

    if not user_id:
        return {"message": "Usuario no autenticado"}, 401

    video = request.files["file"]
    title = request.form["title"]
    
    if not allowed_file(video.filename):
        return {"message": "El formato del vídeo debe ser .mp4"}, 400

    video.seek(0, os.SEEK_END)
    file_size = video.tell()
    video.seek(0)

    if file_size > FILE_SIZE:
        return {"message": "El tamaño del archivo excede el límite de 100MB"}, 400

    filename = secure_filename(video.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(FOLDER, unique_filename)

    os.makedirs(FOLDER, exist_ok=True)
    video.save(file_path)

    new_video = Video(
        title=title,
        status=VideoStatus.SUBIENDO,
        original_url=file_path,
        user_id=user_id
    )

    db.session.add(new_video)
    db.session.commit()

    task = process_video.delay(new_video.video_id, unique_filename)

    return jsonify({
        "message": "Video subido correctamente. Procesamiento en curso",
        "title": title
    }), 201


@videos_bp.route('', methods=['GET'], strict_slashes=False)
@jwt_required()
def get_videos():
    identity = get_jwt_identity()
    user_id = identity['id']

    if not user_id:
        return {"mesage": "Usuario no autenticado"}, 401
    
    videos = db.session.execute(
        select(Video)
        .where(Video.user_id == user_id, Video.is_deleted == False)
        .order_by(Video.uploaded_at.desc())
    ).scalars().all()

    video_schema = VideoSchema(many=True)    
    serialized_videos = video_schema.dump(videos)

    return jsonify(serialized_videos), 200


@videos_bp.route("/<int:id>", methods=['GET'], strict_slashes=False)
@jwt_required()
def get_video_usuario(id: int):
    identity = get_jwt_identity()
    auth_user_id = identity['id']

    if not auth_user_id:
        return {"mesage": "Usuario no autenticado"}, 401
    
    video = db.session.execute(
        select(
            Video,
            func.count(Vote.id).label("votes_count")
        )
        .where(Video.video_id == id, Video.is_deleted == False)
        .outerjoin(Vote, Vote.video_id == Video.video_id)
        .group_by(Video.video_id)
    ).first()

    if not video:
        return {"message": "El video con el video_id especificado no existe o no pertenece al usuario"}, 404
    
    data, votes = video

    if str(data.user_id) != auth_user_id:
        return {"message": "El usuario autenticado no tiene permisos para acceder a este video."}, 403
    
    video_schema = VideoSchema()    
    serialized_video = video_schema.dump(data)
    serialized_video["votes_count"] = votes

    return jsonify(serialized_video), 200




@videos_bp.route("/<int:id>", methods=['DELETE'], strict_slashes=False)
@jwt_required()
def delete_video_usuario(id: int):
    identity = get_jwt_identity()
    auth_user_id = identity['id']

    if not auth_user_id:
        return {"message": "Usuario no autenticado"}, 401

    video = Video.query.get_or_404(id)

    if video.is_deleted:
        return {"message": "El video no se encuentra disponible en la plataforma"}, 404        

    if str(video.user_id) != auth_user_id:
        return {"message": "El usuario autenticado no tiene permisos para acceder a este video."}, 403

    if video.status == VideoStatus.PROCESADO:
        return {"message": "El video no se puede eliminar debido a que esta habilitado para votacion"}, 400

    video.is_deleted = True
    db.session.commit()

    return {"message": "Video eliminado exitosamente"}, 200