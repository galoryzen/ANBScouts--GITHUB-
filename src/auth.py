from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from datetime import timedelta
from src.models.main import db
from src.models.main import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    # Validar campos obligatorios
    required_fields = ["username", "password1", "password2", "role", "name", "last_name", "email", "city", "country"]
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"El campo '{field}' es obligatorio"}), 400

    username = data.get('username')
    password1 = data.get('password1')
    password2 = data.get('password2')
    role = data.get('role')
    name = data.get('name')
    last_name = data.get('last_name')
    email = data.get('email')
    city = data.get('city')
    country = data.get('country')

    # Validar que las contraseñas coincidan
    if password1 != password2:
        return jsonify({"error": "Las contraseñas no coinciden"}), 400

    # Validar que el email sea único
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "El email ya está registrado"}), 400

    # Cifrar la contraseña
    hashed_password = generate_password_hash(password1)

    # Crear un nuevo usuario
    new_user = User(
        username=username,
        password=hashed_password,
        role=role,
        name=name,
        last_name=last_name,
        email=email,
        city=city,
        country=country
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Usuario creado exitosamente"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    # Validar campos obligatorios
    required_fields = ["username", "password"]
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"El campo '{field}' es obligatorio"}), 400

    username = data.get('username')
    password = data.get('password')

    # Buscar al usuario por username
    user = User.query.filter_by(username=username).first()

    # Validación de credenciales
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Credenciales inválidas"}), 401

    # Generar un token JWT
    access_token = create_access_token(
        identity={"id": user.id, "username": user.username, "email": user.email},
        expires_delta=timedelta(hours=1)
    )

    return jsonify({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600  # 1 hora
    }), 200